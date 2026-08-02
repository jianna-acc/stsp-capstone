# File: /backend/tests/test_file_processor_preparation.py
# Purpose: Verifies that file processing performs offline AI
# preparation while preserving existing source-aware persistence.

import asyncio
from typing import Any
from uuid import UUID

import pytest

from app.ai import (
    AIChunkingError,
    StudyMaterialPreparation,
)
from app.core.config import Settings
from app.services.file_processor import (
    FileProcessorPreparationError,
    FileProcessorService,
)
from app.services.study_material_preparer import (
    StudyMaterialPreparer,
)

FILE_ID = UUID(
    "11111111-1111-1111-1111-111111111111",
)
PROCESSING_JOB_ID = UUID(
    "22222222-2222-2222-2222-222222222222",
)
USER_ID = UUID(
    "33333333-3333-3333-3333-333333333333",
)

FILENAME = "biology.txt"
MIME_TYPE = "text/plain"

PAYLOAD = (
    b"Photosynthesis converts sunlight into chemical energy. "
    b"Plants use chlorophyll to absorb light."
)


def build_settings(
    **overrides: Any,
) -> Settings:
    """Create isolated valid processing settings."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "ai_chunk_target_characters": 500,
        "ai_chunk_overlap_characters": 0,
        "ai_chunk_min_characters": 100,
        "ai_embedding_batch_size": 2,
        "ai_max_chunks_per_material": 1000,
        "_env_file": None,
    }
    values.update(overrides)

    return Settings(**values)


class FakeAdminService:
    """Provide deterministic storage and persistence operations."""

    def __init__(
        self,
        *,
        payload: bytes = PAYLOAD,
    ) -> None:
        """Create queued processing records and call tracking."""

        self.payload = payload

        self.started = False
        self.indexing = False
        self.completed = False

        self.completed_document: Any | None = None
        self.completed_chunks: list[Any] = []

        self.failures: list[
            tuple[
                UUID,
                str,
                str,
            ]
        ] = []

    async def get_study_file(
        self,
        file_id: UUID,
    ) -> dict[str, object] | None:
        """Return one valid queued study-file row."""

        assert file_id == FILE_ID

        return {
            "id": str(FILE_ID),
            "user_id": str(USER_ID),
            "subject_id": str(
                UUID(
                    "44444444-4444-4444-4444-444444444444",
                ),
            ),
            "original_filename": FILENAME,
            "storage_path": f"{USER_ID}/{FILE_ID}/{FILENAME}",
            "mime_type": MIME_TYPE,
            "size_bytes": len(self.payload),
            "processing_status": "queued",
        }

    async def get_processing_job(
        self,
        file_id: UUID,
    ) -> dict[str, object] | None:
        """Return the valid queued processing job."""

        assert file_id == FILE_ID

        return {
            "id": str(PROCESSING_JOB_ID),
            "user_id": str(USER_ID),
            "study_file_id": str(FILE_ID),
            "status": "queued",
        }

    async def start_processing(
        self,
        file_id: UUID,
    ) -> None:
        """Record the transition into reading."""

        assert file_id == FILE_ID
        self.started = True

    async def download_private_object(
        self,
        storage_path: str,
    ) -> bytes:
        """Return the deterministic plain-text payload."""

        assert storage_path
        return self.payload

    async def mark_indexing(
        self,
        file_id: UUID,
    ) -> None:
        """Record the indexing transition."""

        assert file_id == FILE_ID
        self.indexing = True

    async def complete_processing(
        self,
        file_id: UUID,
        document: Any,
        chunks: list[Any],
    ) -> None:
        """Record the existing source-aware persistence values."""

        assert file_id == FILE_ID

        self.completed = True
        self.completed_document = document
        self.completed_chunks = chunks

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Record one controlled processing failure."""

        self.failures.append(
            (
                file_id,
                error_code,
                error_message,
            ),
        )


class RecordingPreparer:
    """Record preparation input and delegate to the real service."""

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        """Create the real offline delegate and call history."""

        self._delegate = StudyMaterialPreparer(
            settings=settings,
        )

        self.calls: list[
            dict[
                str,
                str | None,
            ]
        ] = []

    def prepare(
        self,
        *,
        material_id: str,
        text: str,
        source_name: str | None = None,
    ) -> StudyMaterialPreparation:
        """Record values and perform real offline preparation."""

        self.calls.append(
            {
                "material_id": material_id,
                "text": text,
                "source_name": source_name,
            },
        )

        return self._delegate.prepare(
            material_id=material_id,
            text=text,
            source_name=source_name,
        )


class FailingPreparer:
    """Raise a deterministic controlled chunking failure."""

    def prepare(
        self,
        *,
        material_id: str,
        text: str,
        source_name: str | None = None,
    ) -> StudyMaterialPreparation:
        """Reject preparation without making an external request."""

        del material_id
        del text
        del source_name

        raise AIChunkingError(
            "Controlled preparation failure.",
        )


def test_processor_prepares_extracted_text_before_persistence() -> None:
    """Processing must send normalized extracted text to the preparer."""

    settings = build_settings()
    admin = FakeAdminService()
    preparer = RecordingPreparer(
        settings=settings,
    )

    processor = FileProcessorService(
        settings=settings,
        admin_service=admin,
        preparer=preparer,
    )

    result = asyncio.run(
        processor.process_file(
            file_id=FILE_ID,
        ),
    )

    assert len(preparer.calls) == 1

    call = preparer.calls[0]

    assert call["material_id"] == str(FILE_ID)
    assert call["source_name"] == FILENAME
    assert call["text"] == PAYLOAD.decode("utf-8")

    assert admin.started is True
    assert admin.indexing is True
    assert admin.completed is True
    assert admin.failures == []

    assert result.study_file_id == FILE_ID
    assert result.processing_job_id == PROCESSING_JOB_ID


def test_processor_keeps_source_aware_chunks_for_persistence() -> None:
    """Current database persistence must retain extractor locators."""

    settings = build_settings()
    admin = FakeAdminService()

    processor = FileProcessorService(
        settings=settings,
        admin_service=admin,
        preparer=RecordingPreparer(
            settings=settings,
        ),
    )

    result = asyncio.run(
        processor.process_file(
            file_id=FILE_ID,
        ),
    )

    assert admin.completed is True
    assert admin.completed_document is not None
    assert admin.completed_chunks

    first_chunk = admin.completed_chunks[0]

    assert first_chunk.locator_type == "document"
    assert first_chunk.locator_label == "Complete document"
    assert first_chunk.content
    assert result.chunk_count == len(
        admin.completed_chunks,
    )


def test_preparation_failure_marks_processing_failed() -> None:
    """Preparation failures must stop indexing and persistence."""

    settings = build_settings()
    admin = FakeAdminService()

    processor = FileProcessorService(
        settings=settings,
        admin_service=admin,
        preparer=FailingPreparer(),
    )

    with pytest.raises(
        FileProcessorPreparationError,
        match="Controlled preparation failure",
    ):
        asyncio.run(
            processor.process_file(
                file_id=FILE_ID,
            ),
        )

    assert admin.started is True
    assert admin.indexing is False
    assert admin.completed is False

    assert admin.failures == [
        (
            FILE_ID,
            "PREPARATION_FAILED",
            "Controlled preparation failure.",
        ),
    ]
