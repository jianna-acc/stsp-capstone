# File: /backend/app/services/file_processor.py
# Purpose: Provides one reusable workflow for validating,
# extracting, chunking, and storing study-file content.

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.config import Settings
from app.services.file_extraction import (
    FileExtractionError,
    chunk_extracted_document,
    extract_document,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
    SupabaseAdminService,
)


class FileProcessorError(RuntimeError):
    """Base exception for reusable file-processing errors."""


class FileProcessorNotFoundError(FileProcessorError):
    """Raised when a study file cannot be found."""


class FileProcessorConflictError(FileProcessorError):
    """Raised when file and job states prevent processing."""


class FileProcessorTooLargeError(FileProcessorError):
    """Raised when a file exceeds the processing limit."""


class FileProcessorExtractionError(FileProcessorError):
    """Raised when readable content cannot be extracted."""


class FileProcessorUpstreamError(FileProcessorError):
    """Raised when Supabase or Storage cannot be reached."""


@dataclass(frozen=True)
class ValidatedFileSource:
    """Validated information about a queued private file."""

    study_file_id: UUID
    processing_job_id: UUID

    filename: str
    mime_type: str

    expected_size_bytes: int
    downloaded_size_bytes: int

    processing_status: str
    job_status: str


@dataclass(frozen=True)
class ProcessedFileResult:
    """Result returned after processing completes."""

    study_file_id: UUID
    processing_job_id: UUID

    filename: str
    mime_type: str

    character_count: int
    chunk_count: int

    page_count: int | None
    slide_count: int | None
    sheet_count: int | None

    processing_status: str
    job_status: str


class FileProcessorService:
    """Reusable study-file processing workflow."""

    def __init__(
        self,
        settings: Settings,
        admin_service: SupabaseAdminService | None = None,
    ) -> None:
        self._settings = settings

        self._admin = (
            admin_service
            if admin_service is not None
            else SupabaseAdminService(
                settings=settings,
            )
        )

    async def validate_source(
        self,
        file_id: UUID,
    ) -> ValidatedFileSource:
        """Confirm that a queued private file can be downloaded."""

        try:
            study_file, processing_job = (
                await self._load_context(
                    file_id=file_id,
                )
            )

            self._validate_matching_user(
                study_file=study_file,
                processing_job=processing_job,
            )

            self._require_queued_state(
                study_file=study_file,
                processing_job=processing_job,
            )

            expected_size = self._get_expected_size(
                study_file=study_file,
            )

            storage_path = self._get_required_text(
                row=study_file,
                field_name="storage_path",
                error_message=(
                    "The study file does not have "
                    "a Storage path."
                ),
            )

            payload = await self._admin.download_private_object(
                storage_path=storage_path,
            )

            downloaded_size = len(
                payload,
            )

            if downloaded_size != expected_size:
                raise FileProcessorConflictError(
                    "The downloaded file size does not "
                    "match the database record.",
                )

            return ValidatedFileSource(
                study_file_id=self._get_uuid(
                    study_file,
                    "id",
                    "The study-file ID is invalid.",
                ),
                processing_job_id=self._get_uuid(
                    processing_job,
                    "id",
                    "The processing-job ID is invalid.",
                ),
                filename=self._get_required_text(
                    row=study_file,
                    field_name="original_filename",
                    error_message=(
                        "The study file does not have "
                        "an original filename."
                    ),
                ),
                mime_type=self._get_required_text(
                    row=study_file,
                    field_name="mime_type",
                    error_message=(
                        "The study file does not have "
                        "a MIME type."
                    ),
                ),
                expected_size_bytes=expected_size,
                downloaded_size_bytes=downloaded_size,
                processing_status="queued",
                job_status="queued",
            )

        except FileProcessorError:
            raise

        except SupabaseAdminError as error:
            raise FileProcessorUpstreamError(
                str(error),
            ) from error

    async def process_file(
        self,
        file_id: UUID,
    ) -> ProcessedFileResult:
        """Download, extract, chunk, and store one study file."""

        processing_active = False

        try:
            study_file, processing_job = (
                await self._load_context(
                    file_id=file_id,
                )
            )

            self._validate_matching_user(
                study_file=study_file,
                processing_job=processing_job,
            )

            expected_size = self._get_expected_size(
                study_file=study_file,
            )

            storage_path = self._get_required_text(
                row=study_file,
                field_name="storage_path",
                error_message=(
                    "The study file does not have "
                    "a Storage path."
                ),
            )

            filename = self._get_required_text(
                row=study_file,
                field_name="original_filename",
                error_message=(
                    "The study file does not have "
                    "an original filename."
                ),
            )

            mime_type = self._get_required_text(
                row=study_file,
                field_name="mime_type",
                error_message=(
                    "The study file does not have "
                    "a MIME type."
                ),
            )

            processing_job_id = self._get_uuid(
                processing_job,
                "id",
                "The processing-job ID is invalid.",
            )

            await self._prepare_processing_state(
                file_id=file_id,
                study_file=study_file,
                processing_job=processing_job,
            )

            processing_active = True

            payload = await self._admin.download_private_object(
                storage_path=storage_path,
            )

            if len(payload) != expected_size:
                raise FileExtractionError(
                    "The downloaded file size does not "
                    "match its database record.",
                )

            document = extract_document(
                payload=payload,
                mime_type=mime_type,
                filename=filename,
            )

            chunks = chunk_extracted_document(
                document=document,
            )

            await self._admin.mark_indexing(
                file_id=file_id,
            )

            await self._admin.complete_processing(
                file_id=file_id,
                document=document,
                chunks=chunks,
            )

            return ProcessedFileResult(
                study_file_id=file_id,
                processing_job_id=processing_job_id,
                filename=filename,
                mime_type=mime_type,
                character_count=(
                    document.character_count
                ),
                chunk_count=len(
                    chunks,
                ),
                page_count=document.page_count,
                slide_count=document.slide_count,
                sheet_count=document.sheet_count,
                processing_status="ready",
                job_status="completed",
            )

        except FileProcessorError:
            raise

        except FileExtractionError as error:
            if processing_active:
                await self._best_effort_failure(
                    file_id=file_id,
                    error_code="EXTRACTION_FAILED",
                    error_message=str(error),
                )

            raise FileProcessorExtractionError(
                str(error),
            ) from error

        except SupabaseAdminError as error:
            if processing_active:
                await self._best_effort_failure(
                    file_id=file_id,
                    error_code="PROCESSING_SERVICE_ERROR",
                    error_message=str(error),
                )

            raise FileProcessorUpstreamError(
                str(error),
            ) from error

    async def _load_context(
        self,
        file_id: UUID,
    ) -> tuple[
        dict[str, object],
        dict[str, object],
    ]:
        """Load one study file and its processing job."""

        study_file = await self._admin.get_study_file(
            file_id=file_id,
        )

        if study_file is None:
            raise FileProcessorNotFoundError(
                "The study file was not found.",
            )

        processing_job = (
            await self._admin.get_processing_job(
                file_id=file_id,
            )
        )

        if processing_job is None:
            raise FileProcessorConflictError(
                "The study file does not have "
                "a processing job.",
            )

        return study_file, processing_job

    async def _prepare_processing_state(
        self,
        file_id: UUID,
        study_file: dict[str, object],
        processing_job: dict[str, object],
    ) -> None:
        """Start queued work or accept an already claimed job."""

        file_status = str(
            study_file.get(
                "processing_status",
                "",
            ),
        )

        job_status = str(
            processing_job.get(
                "status",
                "",
            ),
        )

        if (
            file_status == "queued"
            and job_status == "queued"
        ):
            await self._admin.start_processing(
                file_id=file_id,
            )

            return

        if (
            file_status == "reading"
            and job_status == "processing"
        ):
            return

        raise FileProcessorConflictError(
            "The file-processing state is not eligible "
            "for processing.",
        )

    def _require_queued_state(
        self,
        study_file: dict[str, object],
        processing_job: dict[str, object],
    ) -> None:
        """Require both records to still be queued."""

        file_status = str(
            study_file.get(
                "processing_status",
                "",
            ),
        )

        job_status = str(
            processing_job.get(
                "status",
                "",
            ),
        )

        if file_status != "queued":
            raise FileProcessorConflictError(
                "Only queued study files can be validated.",
            )

        if job_status != "queued":
            raise FileProcessorConflictError(
                "Only queued processing jobs can be validated.",
            )

    def _validate_matching_user(
        self,
        study_file: dict[str, object],
        processing_job: dict[str, object],
    ) -> None:
        """Ensure the file and job belong to the same user."""

        file_user_id = str(
            study_file.get(
                "user_id",
                "",
            ),
        ).strip()

        job_user_id = str(
            processing_job.get(
                "user_id",
                "",
            ),
        ).strip()

        if (
            not file_user_id
            or not job_user_id
            or file_user_id != job_user_id
        ):
            raise FileProcessorConflictError(
                "The study file and processing job "
                "do not belong to the same user.",
            )

    def _get_expected_size(
        self,
        study_file: dict[str, object],
    ) -> int:
        """Validate the recorded source-file size."""

        try:
            expected_size = int(
                study_file.get(
                    "size_bytes",
                    0,
                ),
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise FileProcessorConflictError(
                "The study file has an invalid "
                "recorded size.",
            ) from error

        if expected_size <= 0:
            raise FileProcessorConflictError(
                "The study file has an invalid "
                "recorded size.",
            )

        if (
            expected_size
            > self._settings.max_processing_file_bytes
        ):
            raise FileProcessorTooLargeError(
                "The file exceeds the backend "
                "processing limit.",
            )

        return expected_size

    @staticmethod
    def _get_required_text(
        row: dict[str, object],
        field_name: str,
        error_message: str,
    ) -> str:
        """Read one required string value from a row."""

        value = str(
            row.get(
                field_name,
                "",
            ),
        ).strip()

        if not value:
            raise FileProcessorConflictError(
                error_message,
            )

        return value

    @staticmethod
    def _get_uuid(
        row: dict[str, object],
        field_name: str,
        error_message: str,
    ) -> UUID:
        """Read one required UUID from a database row."""

        try:
            return UUID(
                str(
                    row.get(
                        field_name,
                        "",
                    ),
                ),
            )
        except (
            TypeError,
            ValueError,
            AttributeError,
        ) as error:
            raise FileProcessorConflictError(
                error_message,
            ) from error

    async def _best_effort_failure(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Attempt to preserve failure details without hiding errors."""

        try:
            await self._admin.fail_processing(
                file_id=file_id,
                error_code=error_code,
                error_message=error_message,
            )
        except SupabaseAdminError:
            return