# File: /backend/tests/test_file_processor_vector_indexing.py
# Purpose: Tests file-processing vector-index integration and
# controlled failure codes without external service calls.

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest

from app.ai.preparation import StudyMaterialPreparation
from app.core.config import Settings
from app.services.file_processor import (
    FileProcessorEmbeddingError,
    FileProcessorPreparationError,
    FileProcessorService,
    FileProcessorVectorPersistenceError,
)
from app.services.study_material_vector_indexer import (
    StudyMaterialVectorEmbeddingStepError,
    StudyMaterialVectorPersistenceStepError,
    StudyMaterialVectorPreparationError,
)

FILE_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

JOB_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

USER_ID = UUID(
    "33333333-3333-4333-8333-333333333333",
)

FILE_BYTES = b"Alpha study material."


def make_settings() -> Settings:
    """Create the settings required by FileProcessorService."""

    return cast(
        Settings,
        SimpleNamespace(
            max_processing_file_bytes=20_971_520,
        ),
    )


class FakeAdminService:
    """Provide an in-memory file-processing database boundary."""

    def __init__(
        self,
    ) -> None:
        self.events: list[str] = []

        self.study_file: dict[str, object] = {
            "id": str(FILE_ID),
            "user_id": str(USER_ID),
            "storage_path": (f"{USER_ID}/subject/{FILE_ID}/lecture.txt"),
            "original_filename": "lecture.txt",
            "mime_type": "text/plain",
            "size_bytes": len(FILE_BYTES),
            "processing_status": "queued",
        }

        self.processing_job: dict[str, object] = {
            "id": str(JOB_ID),
            "user_id": str(USER_ID),
            "study_file_id": str(FILE_ID),
            "status": "queued",
        }

        self.completed = False

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
        assert file_id == FILE_ID

        return self.study_file

    async def get_processing_job(
        self,
        file_id: UUID,
    ) -> dict[str, object] | None:
        assert file_id == FILE_ID

        return self.processing_job

    async def start_processing(
        self,
        file_id: UUID,
    ) -> None:
        assert file_id == FILE_ID

        self.events.append(
            "start_processing",
        )

        self.study_file["processing_status"] = "reading"

        self.processing_job["status"] = "processing"

    async def download_private_object(
        self,
        storage_path: str,
    ) -> bytes:
        assert storage_path

        self.events.append(
            "download",
        )

        return FILE_BYTES

    async def mark_indexing(
        self,
        file_id: UUID,
    ) -> None:
        assert file_id == FILE_ID

        self.events.append(
            "mark_indexing",
        )

        self.study_file["processing_status"] = "indexing"

    async def complete_processing(
        self,
        file_id: UUID,
        document: Any,
        chunks: list[Any],
    ) -> None:
        assert file_id == FILE_ID
        assert document.extracted_text
        assert chunks

        self.events.append(
            "complete_processing",
        )

        self.completed = True

        self.study_file["processing_status"] = "ready"

        self.processing_job["status"] = "completed"

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        self.events.append(
            f"fail:{error_code}",
        )

        self.failures.append(
            (
                file_id,
                error_code,
                error_message,
            ),
        )

        self.study_file["processing_status"] = "failed"

        self.processing_job["status"] = "failed"


class RecordingPreparer:
    """Return one preparation object and record its input."""

    def __init__(
        self,
        events: list[str],
    ) -> None:
        self.events = events

        self.preparation = cast(
            StudyMaterialPreparation,
            SimpleNamespace(
                marker="prepared",
            ),
        )

    def prepare(
        self,
        *,
        material_id: str,
        text: str,
        source_name: str | None = None,
    ) -> StudyMaterialPreparation:
        assert material_id == str(
            FILE_ID,
        )

        assert text == ("Alpha study material.")

        assert source_name == ("lecture.txt")

        self.events.append(
            "prepare",
        )

        return self.preparation


class RecordingVectorIndexer:
    """Record vector-indexing input or raise a configured error."""

    def __init__(
        self,
        *,
        events: list[str],
        error: Exception | None = None,
    ) -> None:
        self.events = events
        self.error = error

        self.calls: list[
            tuple[
                UUID,
                StudyMaterialPreparation,
            ]
        ] = []

    async def index_preparation(
        self,
        *,
        study_file_id: UUID,
        preparation: StudyMaterialPreparation,
    ) -> object:
        self.events.append(
            "vector_index",
        )

        self.calls.append(
            (
                study_file_id,
                preparation,
            ),
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            chunk_count=1,
        )


def make_processor(
    *,
    admin: FakeAdminService,
    vector_indexer: RecordingVectorIndexer | None,
) -> tuple[
    FileProcessorService,
    RecordingPreparer,
]:
    """Create one fully isolated processor."""

    preparer = RecordingPreparer(
        events=admin.events,
    )

    processor = FileProcessorService(
        settings=make_settings(),
        admin_service=cast(
            Any,
            admin,
        ),
        preparer=preparer,
        vector_indexer=vector_indexer,
    )

    return processor, preparer


def test_vector_indexing_runs_before_completion() -> None:
    """AI vectors must persist while the file is indexing."""

    admin = FakeAdminService()

    vector_indexer = RecordingVectorIndexer(
        events=admin.events,
    )

    processor, preparer = make_processor(
        admin=admin,
        vector_indexer=vector_indexer,
    )

    result = asyncio.run(
        processor.process_file(
            file_id=FILE_ID,
        ),
    )

    assert result.processing_status == "ready"
    assert result.job_status == "completed"

    assert admin.completed is True
    assert admin.failures == []

    assert admin.events == [
        "start_processing",
        "download",
        "prepare",
        "mark_indexing",
        "vector_index",
        "complete_processing",
    ]

    assert vector_indexer.calls == [
        (
            FILE_ID,
            preparer.preparation,
        ),
    ]


def test_processor_can_skip_optional_vector_indexer() -> None:
    """Existing isolated processor tests may omit vector indexing."""

    admin = FakeAdminService()

    processor, _ = make_processor(
        admin=admin,
        vector_indexer=None,
    )

    result = asyncio.run(
        processor.process_file(
            file_id=FILE_ID,
        ),
    )

    assert result.processing_status == "ready"

    assert admin.events == [
        "start_processing",
        "download",
        "prepare",
        "mark_indexing",
        "complete_processing",
    ]


def test_vector_preparation_failure_uses_existing_code() -> None:
    """Vector preparation conflicts remain preparation failures."""

    admin = FakeAdminService()

    vector_indexer = RecordingVectorIndexer(
        events=admin.events,
        error=StudyMaterialVectorPreparationError(
            "Prepared chunks are inconsistent.",
        ),
    )

    processor, _ = make_processor(
        admin=admin,
        vector_indexer=vector_indexer,
    )

    with pytest.raises(
        FileProcessorPreparationError,
        match="inconsistent",
    ):
        asyncio.run(
            processor.process_file(
                file_id=FILE_ID,
            ),
        )

    assert admin.completed is False

    assert admin.failures == [
        (
            FILE_ID,
            "PREPARATION_FAILED",
            "Prepared chunks are inconsistent.",
        ),
    ]


def test_embedding_failure_is_controlled() -> None:
    """Embedding errors use EMBEDDING_FAILED."""

    admin = FakeAdminService()

    vector_indexer = RecordingVectorIndexer(
        events=admin.events,
        error=(
            StudyMaterialVectorEmbeddingStepError(
                "Embedding provider unavailable.",
            )
        ),
    )

    processor, _ = make_processor(
        admin=admin,
        vector_indexer=vector_indexer,
    )

    with pytest.raises(
        FileProcessorEmbeddingError,
        match="provider unavailable",
    ):
        asyncio.run(
            processor.process_file(
                file_id=FILE_ID,
            ),
        )

    assert admin.completed is False

    assert admin.failures == [
        (
            FILE_ID,
            "EMBEDDING_FAILED",
            "Embedding provider unavailable.",
        ),
    ]


def test_vector_persistence_failure_is_controlled() -> None:
    """Vector database errors use VECTOR_PERSISTENCE_FAILED."""

    admin = FakeAdminService()

    vector_indexer = RecordingVectorIndexer(
        events=admin.events,
        error=(
            StudyMaterialVectorPersistenceStepError(
                "Vector RPC failed.",
            )
        ),
    )

    processor, _ = make_processor(
        admin=admin,
        vector_indexer=vector_indexer,
    )

    with pytest.raises(
        FileProcessorVectorPersistenceError,
        match="Vector RPC failed",
    ):
        asyncio.run(
            processor.process_file(
                file_id=FILE_ID,
            ),
        )

    assert admin.completed is False

    assert admin.failures == [
        (
            FILE_ID,
            "VECTOR_PERSISTENCE_FAILED",
            "Vector RPC failed.",
        ),
    ]
