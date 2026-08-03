# File: /backend/app/workers/file_processing_worker.py
# Purpose: Automatically recovers abandoned jobs, claims queued
# jobs, and processes study files as a long-running worker.

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Protocol
from uuid import UUID

from app.core.config import (
    Settings,
    get_settings,
)
from app.services.file_processor import (
    FileProcessorError,
    FileProcessorService,
    ProcessedFileResult,
)
from app.services.study_material_embedder import (
    StudyMaterialEmbedder,
)
from app.services.study_material_vector_indexer import (
    StudyMaterialVectorIndexer,
)
from app.services.supabase_admin import (
    ClaimedProcessingJob,
    RecoveredProcessingJobs,
    SupabaseAdminError,
    SupabaseAdminService,
)

logger = logging.getLogger(
    __name__,
)


class AdminServiceProtocol(Protocol):
    """Operations required from the Supabase admin service."""

    async def claim_next_processing_job(
        self,
    ) -> ClaimedProcessingJob | None:
        """Claim one queued processing job."""

        ...

    async def recover_stale_processing_jobs(
        self,
        stale_after_minutes: int,
        max_attempts: int,
    ) -> RecoveredProcessingJobs:
        """Recover abandoned processing jobs."""

        ...

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Mark one claimed processing job as failed."""

        ...


class ProcessorProtocol(Protocol):
    """Operations required from the reusable processor."""

    async def process_file(
        self,
        file_id: UUID,
    ) -> ProcessedFileResult:
        """Process one previously claimed study file."""

        ...


ProcessorFactory = Callable[
    [],
    ProcessorProtocol,
]


@dataclass(frozen=True)
class WorkerRunResult:
    """Result from one attempt to claim and process work."""

    claimed: bool
    succeeded: bool

    study_file_id: UUID | None = None
    processing_job_id: UUID | None = None

    error_message: str | None = None


class FileProcessingWorker:
    """Continuously recover and process queued study files."""

    def __init__(
        self,
        settings: Settings,
        admin_service: (AdminServiceProtocol | None) = None,
        processor_factory: (ProcessorFactory | None) = None,
        poll_seconds: float = 2.0,
        recovery_interval_seconds: float = 60.0,
        stale_after_minutes: int = 30,
        max_attempts: int = 3,
    ) -> None:
        if poll_seconds <= 0:
            raise ValueError(
                "poll_seconds must be greater than zero.",
            )

        if recovery_interval_seconds <= 0:
            raise ValueError(
                "recovery_interval_seconds must be greater than zero.",
            )

        if stale_after_minutes < 1:
            raise ValueError(
                "stale_after_minutes must be at least 1.",
            )

        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1.",
            )

        self._settings = settings

        self._admin = (
            admin_service
            if admin_service is not None
            else SupabaseAdminService(
                settings=settings,
            )
        )

        self._processor_factory = (
            processor_factory
            if processor_factory is not None
            else self._create_default_processor
        )

        self._poll_seconds = poll_seconds

        self._recovery_interval_seconds = recovery_interval_seconds

        self._stale_after_minutes = stale_after_minutes

        self._max_attempts = max_attempts

    def _create_default_processor(
        self,
    ) -> FileProcessorService:
        """Create the reusable processor used by the worker."""

        admin_service = SupabaseAdminService(
            settings=self._settings,
        )

        embedder = StudyMaterialEmbedder(
            settings=self._settings,
        )

        vector_indexer = StudyMaterialVectorIndexer(
            embedder=embedder,
            persistence=admin_service,
        )

        return FileProcessorService(
            settings=self._settings,
            admin_service=admin_service,
            vector_indexer=vector_indexer,
        )

    async def recover_stale_jobs(
        self,
    ) -> RecoveredProcessingJobs:
        """Recover abandoned jobs before claiming new work."""

        result = await self._admin.recover_stale_processing_jobs(
            stale_after_minutes=(self._stale_after_minutes),
            max_attempts=(self._max_attempts),
        )

        if result.requeued_count > 0 or result.failed_count > 0:
            logger.warning(
                "Recovered stale processing jobs: %s requeued, %s failed.",
                result.requeued_count,
                result.failed_count,
            )

        return result

    async def run_once(
        self,
    ) -> WorkerRunResult:
        """Claim and process at most one queued file."""

        claimed_job = await self._admin.claim_next_processing_job()

        if claimed_job is None:
            return WorkerRunResult(
                claimed=False,
                succeeded=False,
            )

        logger.info(
            "Claimed processing job %s for study file %s.",
            claimed_job.processing_job_id,
            claimed_job.study_file_id,
        )

        processor = self._processor_factory()

        try:
            result = await processor.process_file(
                file_id=(claimed_job.study_file_id),
            )

        except FileProcessorError as error:
            await self._mark_claim_failed(
                claimed_job=claimed_job,
                error_code=(type(error).__name__.upper()),
                error_message=str(
                    error,
                ),
            )

            logger.error(
                "Processing failed for study file %s: %s",
                claimed_job.study_file_id,
                error,
            )

            return WorkerRunResult(
                claimed=True,
                succeeded=False,
                study_file_id=(claimed_job.study_file_id),
                processing_job_id=(claimed_job.processing_job_id),
                error_message=str(
                    error,
                ),
            )

        except Exception as error:
            await self._mark_claim_failed(
                claimed_job=claimed_job,
                error_code=("WORKER_UNEXPECTED_ERROR"),
                error_message=(
                    "The background worker encountered an unexpected processing error."
                ),
            )

            logger.exception(
                "Unexpected processing error for study file %s.",
                claimed_job.study_file_id,
            )

            return WorkerRunResult(
                claimed=True,
                succeeded=False,
                study_file_id=(claimed_job.study_file_id),
                processing_job_id=(claimed_job.processing_job_id),
                error_message=str(
                    error,
                ),
            )

        logger.info(
            "Completed study file %s with %s chunks.",
            result.study_file_id,
            result.chunk_count,
        )

        return WorkerRunResult(
            claimed=True,
            succeeded=True,
            study_file_id=(result.study_file_id),
            processing_job_id=(result.processing_job_id),
        )

    async def run_forever(
        self,
        stop_event: asyncio.Event,
    ) -> None:
        """Recover and process jobs until shutdown."""

        logger.info(
            "File-processing worker started. "
            "Polling every %.2f seconds. "
            "Recovering stale jobs every %.2f seconds.",
            self._poll_seconds,
            self._recovery_interval_seconds,
        )

        next_recovery_time = 0.0

        while not stop_event.is_set():
            try:
                current_time = monotonic()

                if current_time >= next_recovery_time:
                    await self.recover_stale_jobs()

                    next_recovery_time = current_time + self._recovery_interval_seconds

                run_result = await self.run_once()

            except SupabaseAdminError as error:
                logger.error(
                    "Unable to communicate with the processing queue: %s",
                    error,
                )

                await self._wait_for_next_poll(
                    stop_event=stop_event,
                )

                continue

            except Exception:
                logger.exception(
                    "Unexpected worker loop failure.",
                )

                await self._wait_for_next_poll(
                    stop_event=stop_event,
                )

                continue

            if not run_result.claimed:
                await self._wait_for_next_poll(
                    stop_event=stop_event,
                )

        logger.info(
            "File-processing worker stopped.",
        )

    async def _mark_claim_failed(
        self,
        claimed_job: ClaimedProcessingJob,
        error_code: str,
        error_message: str,
    ) -> None:
        """Best-effort failure update for one claimed job."""

        try:
            await self._admin.fail_processing(
                file_id=(claimed_job.study_file_id),
                error_code=(error_code[:100]),
                error_message=(error_message[:1000]),
            )

        except SupabaseAdminError as error:
            logger.error(
                "Could not save failure state for study file %s: %s",
                claimed_job.study_file_id,
                error,
            )

    async def _wait_for_next_poll(
        self,
        stop_event: asyncio.Event,
    ) -> None:
        """Wait for the delay or an earlier shutdown."""

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=self._poll_seconds,
            )

        except TimeoutError:
            return


def parse_arguments() -> argparse.Namespace:
    """Read worker command-line arguments."""

    parser = argparse.ArgumentParser(
        description=("Recover and process queued study files automatically."),
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Recover stale jobs, claim at most one queued file, process it, and exit."
        ),
    )

    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
        help=("Seconds to wait when no queued work exists."),
    )

    parser.add_argument(
        "--recovery-interval-seconds",
        type=float,
        default=60.0,
        help=("Seconds between stale-job recovery checks."),
    )

    parser.add_argument(
        "--stale-after-minutes",
        type=int,
        default=30,
        help=("Minutes before an active job is considered stale."),
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help=("Maximum processing attempts before permanent failure."),
    )

    return parser.parse_args()


def register_shutdown_signals(
    stop_event: asyncio.Event,
) -> None:
    """Stop the worker gracefully on SIGINT or SIGTERM."""

    event_loop = asyncio.get_running_loop()

    for shutdown_signal in (
        signal.SIGINT,
        signal.SIGTERM,
    ):
        try:
            event_loop.add_signal_handler(
                shutdown_signal,
                stop_event.set,
            )

        except NotImplementedError:
            continue


async def run_from_arguments(
    arguments: argparse.Namespace,
) -> int:
    """Execute the worker using command-line options."""

    settings = get_settings()

    worker = FileProcessingWorker(
        settings=settings,
        poll_seconds=(arguments.poll_seconds),
        recovery_interval_seconds=(arguments.recovery_interval_seconds),
        stale_after_minutes=(arguments.stale_after_minutes),
        max_attempts=(arguments.max_attempts),
    )

    if arguments.once:
        try:
            await worker.recover_stale_jobs()

            result = await worker.run_once()

        except SupabaseAdminError as error:
            logger.error(
                "Unable to recover or claim queued work: %s",
                error,
            )

            return 1

        if not result.claimed:
            logger.info(
                "No queued file-processing job was found.",
            )

            return 0

        if not result.succeeded:
            return 1

        return 0

    stop_event = asyncio.Event()

    register_shutdown_signals(
        stop_event=stop_event,
    )

    await worker.run_forever(
        stop_event=stop_event,
    )

    return 0


def main() -> None:
    """Run the worker as a Python module."""

    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
    )

    arguments = parse_arguments()

    exit_code = asyncio.run(
        run_from_arguments(
            arguments=arguments,
        ),
    )

    raise SystemExit(
        exit_code,
    )


if __name__ == "__main__":
    main()
