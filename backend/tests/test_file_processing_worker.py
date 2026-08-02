# File: /backend/tests/test_file_processing_worker.py
# Purpose: Tests automatic queue claiming, stale-job recovery,
# successful processing, and worker failure handling without
# making real Supabase or Storage requests.

import asyncio
from types import SimpleNamespace
from typing import cast
from uuid import UUID

from app.core.config import Settings
from app.services.file_processor import (
    FileProcessorConflictError,
    ProcessedFileResult,
)
from app.services.supabase_admin import (
    ClaimedProcessingJob,
    RecoveredProcessingJobs,
)
from app.workers.file_processing_worker import (
    FileProcessingWorker,
)

FILE_ID = UUID(
    "f0dbc2c6-3e77-4609-a5b5-ecf8f64b60c7",
)

JOB_ID = UUID(
    "9b8d5ad3-6f55-477a-b916-72cf668dc76d",
)


class FakeAdminService:
    """In-memory replacement for Supabase admin access."""

    def __init__(
        self,
        claimed_job: (ClaimedProcessingJob | None),
    ) -> None:
        self.claimed_job = claimed_job

        self.claim_count = 0
        self.failure_count = 0
        self.recovery_count = 0

        self.failed_file_id: UUID | None = None

        self.error_code: str | None = None

        self.error_message: str | None = None

        self.recovery_result = RecoveredProcessingJobs(
            requeued_count=0,
            failed_count=0,
        )

        self.received_stale_after_minutes: int | None = None

        self.received_max_attempts: int | None = None

    async def claim_next_processing_job(
        self,
    ) -> ClaimedProcessingJob | None:
        """Return the configured job only once."""

        self.claim_count += 1

        result = self.claimed_job

        self.claimed_job = None

        return result

    async def recover_stale_processing_jobs(
        self,
        stale_after_minutes: int,
        max_attempts: int,
    ) -> RecoveredProcessingJobs:
        """Return the configured recovery result."""

        assert stale_after_minutes >= 1
        assert max_attempts >= 1

        self.recovery_count += 1

        self.received_stale_after_minutes = stale_after_minutes

        self.received_max_attempts = max_attempts

        return self.recovery_result

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Record one simulated processing failure."""

        self.failure_count += 1

        self.failed_file_id = file_id

        self.error_code = error_code

        self.error_message = error_message


class SuccessfulProcessor:
    """Processor that successfully completes a file."""

    def __init__(
        self,
    ) -> None:
        self.processed_file_id: UUID | None = None

    async def process_file(
        self,
        file_id: UUID,
    ) -> ProcessedFileResult:
        """Return a successful processing result."""

        self.processed_file_id = file_id

        return ProcessedFileResult(
            study_file_id=file_id,
            processing_job_id=JOB_ID,
            filename="lesson.pdf",
            mime_type="application/pdf",
            character_count=500,
            chunk_count=2,
            page_count=1,
            slide_count=None,
            sheet_count=None,
            processing_status="ready",
            job_status="completed",
        )


class FailingProcessor:
    """Processor that reports an invalid state."""

    async def process_file(
        self,
        file_id: UUID,
    ) -> ProcessedFileResult:
        """Raise a reusable processor conflict."""

        raise FileProcessorConflictError(
            "The claimed processing state is invalid.",
        )


def build_settings() -> Settings:
    """Create minimal settings for worker tests."""

    return cast(
        Settings,
        SimpleNamespace(),
    )


def test_worker_returns_no_work() -> None:
    """No queued job should produce a no-work result."""

    admin = FakeAdminService(
        claimed_job=None,
    )

    worker = FileProcessingWorker(
        settings=build_settings(),
        admin_service=admin,
        processor_factory=(SuccessfulProcessor),
    )

    result = asyncio.run(
        worker.run_once(),
    )

    assert result.claimed is False
    assert result.succeeded is False

    assert result.study_file_id is None

    assert result.processing_job_id is None

    assert admin.claim_count == 1
    assert admin.failure_count == 0


def test_worker_processes_claimed_job() -> None:
    """A claimed job should be passed to the processor."""

    claimed_job = ClaimedProcessingJob(
        processing_job_id=JOB_ID,
        study_file_id=FILE_ID,
    )

    admin = FakeAdminService(
        claimed_job=claimed_job,
    )

    processor = SuccessfulProcessor()

    worker = FileProcessingWorker(
        settings=build_settings(),
        admin_service=admin,
        processor_factory=(lambda: processor),
    )

    result = asyncio.run(
        worker.run_once(),
    )

    assert result.claimed is True
    assert result.succeeded is True

    assert result.study_file_id == FILE_ID

    assert result.processing_job_id == JOB_ID

    assert processor.processed_file_id == FILE_ID

    assert admin.claim_count == 1
    assert admin.failure_count == 0


def test_worker_marks_failed_claim() -> None:
    """A processing failure should preserve failure state."""

    claimed_job = ClaimedProcessingJob(
        processing_job_id=JOB_ID,
        study_file_id=FILE_ID,
    )

    admin = FakeAdminService(
        claimed_job=claimed_job,
    )

    worker = FileProcessingWorker(
        settings=build_settings(),
        admin_service=admin,
        processor_factory=(FailingProcessor),
    )

    result = asyncio.run(
        worker.run_once(),
    )

    assert result.claimed is True
    assert result.succeeded is False

    assert result.study_file_id == FILE_ID

    assert result.processing_job_id == JOB_ID

    assert admin.claim_count == 1
    assert admin.failure_count == 1

    assert admin.failed_file_id == FILE_ID

    assert admin.error_code is not None

    assert admin.error_message is not None

    assert "invalid" in admin.error_message.lower()


def test_worker_recovers_stale_jobs() -> None:
    """The worker should call stale-job recovery."""

    admin = FakeAdminService(
        claimed_job=None,
    )

    admin.recovery_result = RecoveredProcessingJobs(
        requeued_count=2,
        failed_count=1,
    )

    worker = FileProcessingWorker(
        settings=build_settings(),
        admin_service=admin,
        processor_factory=(SuccessfulProcessor),
        stale_after_minutes=30,
        max_attempts=3,
    )

    result = asyncio.run(
        worker.recover_stale_jobs(),
    )

    assert result.requeued_count == 2

    assert result.failed_count == 1

    assert admin.recovery_count == 1

    assert admin.received_stale_after_minutes == 30

    assert admin.received_max_attempts == 3


def test_worker_recovery_returns_zero_counts() -> None:
    """Recovery should also accept an empty result."""

    admin = FakeAdminService(
        claimed_job=None,
    )

    worker = FileProcessingWorker(
        settings=build_settings(),
        admin_service=admin,
        processor_factory=(SuccessfulProcessor),
    )

    result = asyncio.run(
        worker.recover_stale_jobs(),
    )

    assert result.requeued_count == 0

    assert result.failed_count == 0

    assert admin.recovery_count == 1


def test_worker_rejects_invalid_recovery_settings() -> None:
    """Invalid recovery configuration should be rejected."""

    admin = FakeAdminService(
        claimed_job=None,
    )

    try:
        FileProcessingWorker(
            settings=build_settings(),
            admin_service=admin,
            recovery_interval_seconds=0,
        )

    except ValueError as error:
        assert "recovery_interval_seconds" in str(error)

    else:
        raise AssertionError(
            "Expected invalid recovery interval to raise ValueError.",
        )

    try:
        FileProcessingWorker(
            settings=build_settings(),
            admin_service=admin,
            stale_after_minutes=0,
        )

    except ValueError as error:
        assert "stale_after_minutes" in str(error)

    else:
        raise AssertionError(
            "Expected invalid stale duration to raise ValueError.",
        )

    try:
        FileProcessingWorker(
            settings=build_settings(),
            admin_service=admin,
            max_attempts=0,
        )

    except ValueError as error:
        assert "max_attempts" in str(error)

    else:
        raise AssertionError(
            "Expected invalid maximum attempts to raise ValueError.",
        )
