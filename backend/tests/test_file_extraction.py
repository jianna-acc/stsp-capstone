# File: /backend/tests/test_file_processor.py
# Purpose: Tests the reusable file-processing service without
# making real Supabase or Storage requests.

import asyncio
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest

from app.core.config import Settings
from app.services.file_processor import (
    FileProcessorExtractionError,
    FileProcessorService,
)

FILE_ID = UUID(
    "f0dbc2c6-3e77-4609-a5b5-ecf8f64b60c7",
)

JOB_ID = UUID(
    "9b8d5ad3-6f55-477a-b916-72cf668dc76d",
)

USER_ID = UUID(
    "03d2e3d6-06c3-41ad-a466-fcb5fbedbf42",
)


class FakeSupabaseAdminService:
    """Small in-memory substitute for SupabaseAdminService."""

    def __init__(
        self,
        payload: bytes,
        mime_type: str = "text/plain",
        file_status: str = "queued",
        job_status: str = "queued",
    ) -> None:
        self.payload = payload
        self.start_called = False
        self.indexing_called = False
        self.complete_called = False
        self.failure_called = False

        self.study_file: dict[str, Any] = {
            "id": str(FILE_ID),
            "user_id": str(USER_ID),
            "subject_id": str(
                UUID(
                    "611ba51a-3d06-4cac-a53c-56efd609f9cb",
                ),
            ),
            "original_filename": "lesson.txt",
            "storage_path": (f"{USER_ID}/materials/lesson.txt"),
            "mime_type": mime_type,
            "size_bytes": len(payload),
            "processing_status": file_status,
        }

        self.processing_job: dict[str, Any] = {
            "id": str(JOB_ID),
            "user_id": str(USER_ID),
            "study_file_id": str(FILE_ID),
            "status": job_status,
            "attempt_count": 0,
            "started_at": None,
            "completed_at": None,
            "error_code": None,
            "error_message": None,
        }

    async def get_study_file(
        self,
        file_id: UUID,
    ) -> dict[str, Any] | None:
        assert file_id == FILE_ID
        return self.study_file

    async def get_processing_job(
        self,
        file_id: UUID,
    ) -> dict[str, Any] | None:
        assert file_id == FILE_ID
        return self.processing_job

    async def download_private_object(
        self,
        storage_path: str,
    ) -> bytes:
        assert storage_path
        return self.payload

    async def start_processing(
        self,
        file_id: UUID,
    ) -> None:
        assert file_id == FILE_ID

        self.start_called = True

        self.study_file["processing_status"] = "reading"

        self.processing_job["status"] = "processing"

    async def mark_indexing(
        self,
        file_id: UUID,
    ) -> None:
        assert file_id == FILE_ID

        self.indexing_called = True

        self.study_file["processing_status"] = "indexing"

    async def complete_processing(
        self,
        file_id: UUID,
        document: Any,
        chunks: list[Any],
    ) -> None:
        assert file_id == FILE_ID
        assert document.character_count > 0
        assert len(chunks) > 0

        self.complete_called = True

        self.study_file["processing_status"] = "ready"

        self.processing_job["status"] = "completed"

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        assert file_id == FILE_ID
        assert error_code
        assert error_message

        self.failure_called = True

        self.study_file["processing_status"] = "failed"

        self.processing_job["status"] = "failed"


def build_settings() -> Settings:
    """Build only the Settings values needed by the service."""

    return cast(
        Settings,
        SimpleNamespace(
            max_processing_file_bytes=(20 * 1024 * 1024),
        ),
    )


def test_process_queued_file() -> None:
    """Queued work should be started and completed."""

    admin = FakeSupabaseAdminService(
        payload=b"Reusable file processing service.",
    )

    processor = FileProcessorService(
        settings=build_settings(),
        admin_service=admin,
    )

    result = asyncio.run(
        processor.process_file(
            file_id=FILE_ID,
        ),
    )

    assert result.study_file_id == FILE_ID
    assert result.processing_job_id == JOB_ID
    assert result.processing_status == "ready"
    assert result.job_status == "completed"
    assert result.character_count > 0
    assert result.chunk_count >= 1

    assert admin.start_called is True
    assert admin.indexing_called is True
    assert admin.complete_called is True
    assert admin.failure_called is False


def test_process_already_claimed_file() -> None:
    """A worker-claimed job should not be started twice."""

    admin = FakeSupabaseAdminService(
        payload=b"Already claimed processing job.",
        file_status="reading",
        job_status="processing",
    )

    processor = FileProcessorService(
        settings=build_settings(),
        admin_service=admin,
    )

    result = asyncio.run(
        processor.process_file(
            file_id=FILE_ID,
        ),
    )

    assert result.processing_status == "ready"
    assert result.job_status == "completed"

    assert admin.start_called is False
    assert admin.indexing_called is True
    assert admin.complete_called is True


def test_validate_queued_source() -> None:
    """Validation should download but not process the file."""

    admin = FakeSupabaseAdminService(
        payload=b"Queued source validation.",
    )

    processor = FileProcessorService(
        settings=build_settings(),
        admin_service=admin,
    )

    result = asyncio.run(
        processor.validate_source(
            file_id=FILE_ID,
        ),
    )

    assert result.study_file_id == FILE_ID
    assert result.processing_job_id == JOB_ID

    assert result.expected_size_bytes == result.downloaded_size_bytes

    assert result.processing_status == "queued"
    assert result.job_status == "queued"

    assert admin.start_called is False
    assert admin.complete_called is False


def test_extraction_failure_marks_job_failed() -> None:
    """Extraction errors should preserve a failed job state."""

    admin = FakeSupabaseAdminService(
        payload=b"Unsupported file content.",
        mime_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )

    processor = FileProcessorService(
        settings=build_settings(),
        admin_service=admin,
    )

    with pytest.raises(
        FileProcessorExtractionError,
        match="not supported",
    ):
        asyncio.run(
            processor.process_file(
                file_id=FILE_ID,
            ),
        )

    assert admin.start_called is True
    assert admin.complete_called is False
    assert admin.failure_called is True

    assert admin.study_file["processing_status"] == "failed"

    assert admin.processing_job["status"] == "failed"
