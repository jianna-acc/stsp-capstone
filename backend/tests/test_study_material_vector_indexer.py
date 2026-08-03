# File: /backend/tests/test_study_material_vector_indexer.py
# Purpose: Tests embedding and persistence orchestration with
# mocked dependencies and no external service calls.

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest

from app.ai.chunking import StudyMaterialChunk
from app.ai.preparation import StudyMaterialPreparation
from app.ai.vector_persistence import (
    AIChunkPersistencePayload,
)
from app.services.study_material_embedder import (
    StudyMaterialEmbeddingResult,
    StudyMaterialEmbeddingValidationError,
)
from app.services.study_material_vector_indexer import (
    StudyMaterialVectorEmbeddingStepError,
    StudyMaterialVectorIndexer,
    StudyMaterialVectorPersistenceStepError,
    StudyMaterialVectorPreparationError,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
)

STUDY_FILE_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

OTHER_FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

EMBEDDING_DIMENSIONS = 768


def make_vector(
    value: float = 0.125,
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> tuple[float, ...]:
    """Create one embedding vector."""

    return tuple(
        value
        for _ in range(
            dimensions,
        )
    )


def make_chunk(
    *,
    material_id: str = str(STUDY_FILE_ID),
    chunk_index: int = 0,
    text: str = "Alpha",
    start_offset: int = 0,
) -> StudyMaterialChunk:
    """Create one valid prepared chunk."""

    return StudyMaterialChunk(
        material_id=material_id,
        chunk_index=chunk_index,
        text=text,
        start_offset=start_offset,
        end_offset=(start_offset + len(text)),
        source_name="lecture.txt",
    )


def make_preparation(
    *,
    material_id: str = str(STUDY_FILE_ID),
    chunks: tuple[
        StudyMaterialChunk,
        ...,
    ]
    | None = None,
    preparation_chunk_count: int | None = None,
    original_character_count: int | None = None,
) -> StudyMaterialPreparation:
    """Create a preparation-shaped test object."""

    resolved_chunks = (
        chunks
        if chunks is not None
        else (
            make_chunk(
                material_id=material_id,
            ),
        )
    )

    resolved_character_count = (
        original_character_count
        if original_character_count is not None
        else max(chunk.end_offset for chunk in resolved_chunks)
    )

    resolved_chunk_count = (
        preparation_chunk_count
        if preparation_chunk_count is not None
        else len(
            resolved_chunks,
        )
    )

    return cast(
        StudyMaterialPreparation,
        SimpleNamespace(
            chunking_result=SimpleNamespace(
                material_id=material_id,
                original_character_count=(resolved_character_count),
                chunks=resolved_chunks,
            ),
            chunk_count=resolved_chunk_count,
            batches=(
                SimpleNamespace(
                    batch_index=0,
                    chunks=resolved_chunks,
                ),
            ),
            embedding_requests=(
                SimpleNamespace(
                    texts=tuple(chunk.text for chunk in resolved_chunks),
                ),
            ),
        ),
    )


class StubEmbedder:
    """Returns one configured embedding result or error."""

    def __init__(
        self,
        *,
        result: StudyMaterialEmbeddingResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error

        self.preparations: list[StudyMaterialPreparation] = []

    async def embed_preparation(
        self,
        preparation: StudyMaterialPreparation,
    ) -> StudyMaterialEmbeddingResult:
        """Return the configured embedding result."""

        self.preparations.append(
            preparation,
        )

        if self.error is not None:
            raise self.error

        if self.result is None:
            raise AssertionError(
                "No embedding result was configured.",
            )

        return self.result


class StubPersistence:
    """Records one persistence request."""

    def __init__(
        self,
        *,
        stored_count: int | None = None,
        error: Exception | None = None,
    ) -> None:
        self.stored_count = stored_count
        self.error = error

        self.payloads: list[AIChunkPersistencePayload] = []

    async def persist_ai_chunks(
        self,
        payload: AIChunkPersistencePayload,
    ) -> int:
        """Return the configured stored count."""

        self.payloads.append(
            payload,
        )

        if self.error is not None:
            raise self.error

        if self.stored_count is None:
            return payload.chunk_count

        return self.stored_count


def make_embedding_result(
    *,
    embeddings: tuple[
        tuple[float, ...],
        ...,
    ]
    | None = None,
    embedding_dimensions: int = EMBEDDING_DIMENSIONS,
    batch_count: int = 1,
) -> StudyMaterialEmbeddingResult:
    """Create one embedding-execution result."""

    resolved_embeddings = embeddings if embeddings is not None else (make_vector(),)

    return StudyMaterialEmbeddingResult(
        embedding_model=("gemini-embedding-2"),
        embedding_dimensions=(embedding_dimensions),
        embeddings=resolved_embeddings,
        batch_count=batch_count,
    )


def test_embeds_builds_payload_and_persists() -> None:
    """The orchestration executes every required step."""

    preparation = make_preparation()

    embedder = StubEmbedder(
        result=make_embedding_result(),
    )

    persistence = StubPersistence()

    indexer = StudyMaterialVectorIndexer(
        embedder=embedder,
        persistence=persistence,
    )

    result = asyncio.run(
        indexer.index_preparation(
            study_file_id=STUDY_FILE_ID,
            preparation=preparation,
        ),
    )

    assert result.study_file_id == STUDY_FILE_ID

    assert result.embedding_model == ("gemini-embedding-2")

    assert result.embedding_dimensions == 768
    assert result.chunk_count == 1
    assert result.batch_count == 1
    assert result.persisted_chunk_count == 1

    assert embedder.preparations == [
        preparation,
    ]

    assert (
        len(
            persistence.payloads,
        )
        == 1
    )

    payload = persistence.payloads[0]

    assert payload.study_file_id == STUDY_FILE_ID
    assert payload.chunk_count == 1

    assert payload.records[0].content == ("Alpha")

    assert (
        len(
            payload.records[0].embedding,
        )
        == 768
    )


def test_rejects_mismatched_study_file() -> None:
    """Preparation must belong to the target file."""

    preparation = make_preparation(
        material_id=str(
            OTHER_FILE_ID,
        ),
    )

    embedder = StubEmbedder(
        result=make_embedding_result(),
    )

    persistence = StubPersistence()

    with pytest.raises(
        StudyMaterialVectorPreparationError,
        match="target study file",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert embedder.preparations == []
    assert persistence.payloads == []


def test_rejects_empty_prepared_chunks() -> None:
    """The preparation must contain AI chunks."""

    preparation = cast(
        StudyMaterialPreparation,
        SimpleNamespace(
            chunking_result=SimpleNamespace(
                material_id=str(
                    STUDY_FILE_ID,
                ),
                original_character_count=0,
                chunks=(),
            ),
            chunk_count=0,
        ),
    )

    embedder = StubEmbedder(
        result=make_embedding_result(),
    )

    persistence = StubPersistence()

    with pytest.raises(
        StudyMaterialVectorPreparationError,
        match="At least one prepared AI chunk",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert embedder.preparations == []
    assert persistence.payloads == []


def test_rejects_preparation_chunk_count_mismatch() -> None:
    """Preparation count must match its chunking result."""

    preparation = make_preparation(
        preparation_chunk_count=2,
    )

    embedder = StubEmbedder(
        result=make_embedding_result(),
    )

    persistence = StubPersistence()

    with pytest.raises(
        StudyMaterialVectorPreparationError,
        match="chunk count",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert embedder.preparations == []
    assert persistence.payloads == []


def test_wraps_embedding_failure() -> None:
    """Embedding errors become orchestration errors."""

    preparation = make_preparation()

    embedder = StubEmbedder(
        error=(
            StudyMaterialEmbeddingValidationError(
                "Provider returned invalid vectors.",
            )
        ),
    )

    persistence = StubPersistence()

    with pytest.raises(
        StudyMaterialVectorEmbeddingStepError,
        match="embedding failed",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert (
        len(
            embedder.preparations,
        )
        == 1
    )

    assert persistence.payloads == []


def test_rejects_embedding_count_mismatch() -> None:
    """Embedding count must match prepared chunks."""

    preparation = make_preparation()

    embedder = StubEmbedder(
        result=make_embedding_result(
            embeddings=(
                make_vector(),
                make_vector(
                    value=0.25,
                ),
            ),
        ),
    )

    persistence = StubPersistence()

    with pytest.raises(
        StudyMaterialVectorEmbeddingStepError,
        match="embedding result count",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert persistence.payloads == []


def test_wraps_payload_validation_failure() -> None:
    """Invalid vector metadata cannot reach persistence."""

    preparation = make_preparation()

    embedder = StubEmbedder(
        result=make_embedding_result(
            embedding_dimensions=767,
        ),
    )

    persistence = StubPersistence()

    with pytest.raises(
        StudyMaterialVectorPreparationError,
        match="persistence payload",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert persistence.payloads == []


def test_wraps_supabase_persistence_failure() -> None:
    """Supabase failures become persistence-step errors."""

    preparation = make_preparation()

    embedder = StubEmbedder(
        result=make_embedding_result(),
    )

    persistence = StubPersistence(
        error=SupabaseAdminError(
            "Supabase RPC failed.",
        ),
    )

    with pytest.raises(
        StudyMaterialVectorPersistenceStepError,
        match="vector persistence failed",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert (
        len(
            persistence.payloads,
        )
        == 1
    )


def test_rejects_unexpected_persisted_count() -> None:
    """Stored count must match the payload count."""

    preparation = make_preparation()

    embedder = StubEmbedder(
        result=make_embedding_result(),
    )

    persistence = StubPersistence(
        stored_count=0,
    )

    with pytest.raises(
        StudyMaterialVectorPersistenceStepError,
        match="persisted AI-chunk count",
    ):
        asyncio.run(
            StudyMaterialVectorIndexer(
                embedder=embedder,
                persistence=persistence,
            ).index_preparation(
                study_file_id=STUDY_FILE_ID,
                preparation=preparation,
            ),
        )

    assert (
        len(
            persistence.payloads,
        )
        == 1
    )
