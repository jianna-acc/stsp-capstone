# File: /backend/tests/test_file_processor.py
# Purpose: Tests reusable file-source validation and file
# processing without making real Supabase or Storage requests.

import asyncio
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest

from app.core.config import Settings
from app.services.file_extraction import (
    ExtractedChunk,
    ExtractedDocument,
)
from app.services.file_processor import (
    FileProcessorExtractionError,
    FileProcessorService,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)

FILE_ID = UUID(
    "f0dbc2c6-3e77-4609-a5b5-ecf8f64b60c7",
)

JOB_ID = UUID(
    "9b8d5ad3-6f55-477a-b916-72cf668dc76d",
)

USER_ID = UUID(
    "c1ec7032-b353-4577-9b98-1f2dc8392af8",
)

STORAGE_PATH = f"{USER_ID}/subject/file/lesson.txt"

TEXT_PAYLOAD = (
    b"Operating systems manage hardware resources.\n"
    b"They also provide services to applications."
)


class FakeAdminService:
    """In-memory replacement for trusted Supabase access."""

    def __init__(
        self,
        *,
        file_status: str = "queued",
        job_status: str = "queued",
        payload: bytes = TEXT_PAYLOAD,
    ) -> None:
        self.payload = payload

        self.study_file: dict[str, Any] = {
            "id": str(FILE_ID),
            "user_id": str(USER_ID),
            "subject_id": ("f5a86910-d2b0-49f4-899e-6f40bf734557"),
            "topic": "Operating Systems",
            "original_filename": "lesson.txt",
            "storage_path": STORAGE_PATH,
            "mime_type": "text/plain",
            "size_bytes": len(payload),
            "processing_status": file_status,
        }

        self.processing_job: dict[str, Any] = {
            "id": str(JOB_ID),
            "user_id": str(USER_ID),
            "study_file_id": str(FILE_ID),
            "status": job_status,
            "attempt_count": 1,
        }

        self.get_file_count = 0
        self.get_job_count = 0
        self.download_count = 0
        self.start_count = 0
        self.indexing_count = 0
        self.complete_count = 0
        self.failure_count = 0

        self.downloaded_storage_path: str | None = None
        self.started_file_id: UUID | None = None
        self.indexed_file_id: UUID | None = None
        self.completed_file_id: UUID | None = None
        self.failed_file_id: UUID | None = None

        self.completed_document: ExtractedDocument | None = None

        self.completed_chunks: list[ExtractedChunk] | None = None

        self.failure_code: str | None = None
        self.failure_message: str | None = None

    async def get_study_file(
        self,
        file_id: UUID,
    ) -> dict[str, Any] | None:
        """Return the configured study-file record."""

        self.get_file_count += 1

        assert file_id == FILE_ID

        return self.study_file

    async def get_processing_job(
        self,
        file_id: UUID,
    ) -> dict[str, Any] | None:
        """Return the configured processing-job record."""

        self.get_job_count += 1

        assert file_id == FILE_ID

        return self.processing_job

    async def download_private_object(
        self,
        storage_path: str,
    ) -> bytes:
        """Return the configured private file bytes."""

        self.download_count += 1
        self.downloaded_storage_path = storage_path

        assert storage_path == STORAGE_PATH

        return self.payload

    async def start_processing(
        self,
        file_id: UUID,
    ) -> None:
        """Record that queued processing was started."""

        self.start_count += 1
        self.started_file_id = file_id

        self.study_file["processing_status"] = "reading"

        self.processing_job["status"] = "processing"

    async def mark_indexing(
        self,
        file_id: UUID,
    ) -> None:
        """Record that extraction reached indexing."""

        self.indexing_count += 1
        self.indexed_file_id = file_id

        self.study_file["processing_status"] = "indexing"

    async def complete_processing(
        self,
        file_id: UUID,
        document: ExtractedDocument,
        chunks: list[ExtractedChunk],
    ) -> None:
        """Record the successfully extracted result."""

        self.complete_count += 1
        self.completed_file_id = file_id
        self.completed_document = document
        self.completed_chunks = chunks

        self.study_file["processing_status"] = "ready"

        self.processing_job["status"] = "completed"

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Record a synchronized processing failure."""

        self.failure_count += 1
        self.failed_file_id = file_id
        self.failure_code = error_code
        self.failure_message = error_message

        self.study_file["processing_status"] = "failed"

        self.processing_job["status"] = "failed"


def build_settings() -> Settings:
    """Create minimal settings for processor tests."""

    return cast(
        Settings,
        SimpleNamespace(
            max_processing_file_bytes=(20 * 1024 * 1024),
        ),
    )


def build_processor(
    admin: FakeAdminService,
) -> FileProcessorService:
    """Create a processor using the fake admin service."""

    return FileProcessorService(
        settings=build_settings(),
        admin_service=cast(
            SupabaseAdminService,
            admin,
        ),
    )


def test_validate_source_returns_file_details() -> None:
    """A valid queued source should return safe metadata."""

    admin = FakeAdminService()

    processor = build_processor(
        admin,
    )

    result = asyncio.run(
        processor.validate_source(
            FILE_ID,
        ),
    )

    assert result.study_file_id == FILE_ID
    assert result.processing_job_id == JOB_ID

    assert result.filename == "lesson.txt"
    assert result.mime_type == "text/plain"

    assert result.expected_size_bytes == len(TEXT_PAYLOAD)

    assert result.downloaded_size_bytes == len(TEXT_PAYLOAD)

    assert result.processing_status == "queued"
    assert result.job_status == "queued"

    assert admin.get_file_count == 1
    assert admin.get_job_count == 1
    assert admin.download_count == 1
    assert admin.start_count == 0
    assert admin.indexing_count == 0
    assert admin.complete_count == 0
    assert admin.failure_count == 0


def test_process_file_starts_queued_job() -> None:
    """A queued file should be started and completed."""

    admin = FakeAdminService(
        file_status="queued",
        job_status="queued",
    )

    processor = build_processor(
        admin,
    )

    result = asyncio.run(
        processor.process_file(
            FILE_ID,
        ),
    )

    assert result.study_file_id == FILE_ID
    assert result.processing_job_id == JOB_ID

    assert result.filename == "lesson.txt"
    assert result.mime_type == "text/plain"

    assert result.character_count > 0
    assert result.chunk_count >= 1

    assert result.page_count is None
    assert result.slide_count is None
    assert result.sheet_count is None

    assert result.processing_status == "ready"
    assert result.job_status == "completed"

    assert admin.start_count == 1
    assert admin.started_file_id == FILE_ID

    assert admin.indexing_count == 1
    assert admin.indexed_file_id == FILE_ID

    assert admin.complete_count == 1
    assert admin.completed_file_id == FILE_ID

    assert admin.failure_count == 0

    assert admin.completed_document is not None
    assert admin.completed_document.extracted_text == (
        "Operating systems manage hardware "
        "resources.\n"
        "They also provide services to "
        "applications."
    )

    assert admin.completed_chunks is not None
    assert len(admin.completed_chunks) >= 1

    first_chunk = admin.completed_chunks[0]

    assert first_chunk.chunk_index == 0
    assert first_chunk.locator_type == "document"
    assert first_chunk.locator_label == "Complete document"


def test_process_file_accepts_claimed_job() -> None:
    """A worker-claimed file must not be started twice."""

    admin = FakeAdminService(
        file_status="reading",
        job_status="processing",
    )

    processor = build_processor(
        admin,
    )

    result = asyncio.run(
        processor.process_file(
            FILE_ID,
        ),
    )

    assert result.processing_status == "ready"
    assert result.job_status == "completed"

    assert admin.start_count == 0
    assert admin.indexing_count == 1
    assert admin.complete_count == 1
    assert admin.failure_count == 0


def test_process_file_records_extraction_failure() -> None:
    """Unreadable text should produce a synchronized failure."""

    invalid_payload = b"\xff\xfe\xfa\xfb"

    admin = FakeAdminService(
        file_status="queued",
        job_status="queued",
        payload=invalid_payload,
    )

    processor = build_processor(
        admin,
    )

    with pytest.raises(
        FileProcessorExtractionError,
        match="UTF-8",
    ):
        asyncio.run(
            processor.process_file(
                FILE_ID,
            ),
        )

    assert admin.start_count == 1
    assert admin.indexing_count == 0
    assert admin.complete_count == 0

    assert admin.failure_count == 1
    assert admin.failed_file_id == FILE_ID

    assert admin.failure_code == "EXTRACTION_FAILED"

    assert admin.failure_message is not None
    assert "UTF-8" in admin.failure_message
