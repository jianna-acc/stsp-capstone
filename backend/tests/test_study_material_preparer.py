# File: /backend/tests/test_study_material_preparer.py
# Purpose: Verifies complete offline study-material preparation from
# extracted text through chunks, batches, and embedding requests.

from typing import Any

import pytest

from app.ai import (
    ChunkingResult,
    EmbeddingBatch,
    EmbeddingRequest,
    EmbeddingTaskType,
    StudyMaterialChunk,
    StudyMaterialPreparation,
)
from app.core.config import Settings
from app.services.study_material_preparer import (
    StudyMaterialPreparer,
)


def build_settings(
    **overrides: Any,
) -> Settings:
    """Create isolated preparation settings."""

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


def build_chunk(
    *,
    chunk_index: int,
    text: str,
    start_offset: int,
) -> StudyMaterialChunk:
    """Create one valid preparation-test chunk."""

    return StudyMaterialChunk(
        material_id="material-1",
        chunk_index=chunk_index,
        text=text,
        start_offset=start_offset,
        end_offset=start_offset + len(text),
        source_name="biology.pdf",
    )


def build_chunking_result() -> ChunkingResult:
    """Create one valid two-chunk result."""

    first = build_chunk(
        chunk_index=0,
        text="First chunk.",
        start_offset=0,
    )
    second = build_chunk(
        chunk_index=1,
        text="Second chunk.",
        start_offset=20,
    )

    return ChunkingResult(
        material_id="material-1",
        original_character_count=33,
        chunks=(
            first,
            second,
        ),
        source_name="biology.pdf",
    )


def test_prepare_short_material_creates_complete_result() -> None:
    """Short extracted text must produce one complete preparation."""

    preparer = StudyMaterialPreparer(
        settings=build_settings(),
    )

    result = preparer.prepare(
        material_id="material-1",
        text="Photosynthesis converts sunlight into chemical energy.",
        source_name="biology.pdf",
    )

    assert result.material_id == "material-1"
    assert result.chunk_count == 1
    assert result.batch_count == 1
    assert len(result.embedding_requests) == 1


def test_prepare_preserves_material_metadata() -> None:
    """Material and source metadata must reach every prepared chunk."""

    preparer = StudyMaterialPreparer(
        settings=build_settings(),
    )

    result = preparer.prepare(
        material_id="material-42",
        text="x" * 700,
        source_name="lesson.txt",
    )

    assert result.material_id == "material-42"
    assert result.chunking_result.source_name == "lesson.txt"

    for chunk in result.chunking_result.chunks:
        assert chunk.material_id == "material-42"
        assert chunk.source_name == "lesson.txt"


def test_prepare_creates_multiple_batches() -> None:
    """Multiple chunks must be divided using the configured batch size."""

    preparer = StudyMaterialPreparer(
        settings=build_settings(
            ai_embedding_batch_size=2,
        ),
    )

    result = preparer.prepare(
        material_id="material-1",
        text="x" * 1300,
        source_name="biology.pdf",
    )

    assert result.chunk_count == 3
    assert result.batch_count == 2
    assert [len(batch.chunks) for batch in result.batches] == [
        2,
        1,
    ]


def test_embedding_requests_use_document_task_type() -> None:
    """Prepared study-material requests must use document retrieval."""

    preparer = StudyMaterialPreparer(
        settings=build_settings(),
    )

    result = preparer.prepare(
        material_id="material-1",
        text="x" * 1300,
    )

    assert all(
        request.task_type is EmbeddingTaskType.RETRIEVAL_DOCUMENT
        for request in result.embedding_requests
    )


def test_embedding_request_texts_match_batches() -> None:
    """Each request must preserve its corresponding batch text order."""

    preparer = StudyMaterialPreparer(
        settings=build_settings(),
    )

    result = preparer.prepare(
        material_id="material-1",
        text="x" * 1300,
    )

    for batch, request in zip(
        result.batches,
        result.embedding_requests,
        strict=True,
    ):
        assert request.texts == batch.texts


def test_preparation_is_deterministic() -> None:
    """Identical extracted text must produce identical preparation."""

    preparer = StudyMaterialPreparer(
        settings=build_settings(
            ai_chunk_overlap_characters=50,
        ),
    )

    first = preparer.prepare(
        material_id="material-1",
        text=" ".join(f"term-{index}" for index in range(300)),
        source_name="notes.txt",
    )
    second = preparer.prepare(
        material_id="material-1",
        text=" ".join(f"term-{index}" for index in range(300)),
        source_name="notes.txt",
    )

    assert first == second


def test_preparation_rejects_empty_batches() -> None:
    """Preparation must contain at least one embedding batch."""

    chunking_result = build_chunking_result()

    with pytest.raises(
        ValueError,
        match="at least one embedding batch",
    ):
        StudyMaterialPreparation(
            chunking_result=chunking_result,
            batches=(),
            embedding_requests=(),
        )


def test_preparation_rejects_batch_request_count_mismatch() -> None:
    """Every batch must have one corresponding request."""

    chunking_result = build_chunking_result()
    batch = EmbeddingBatch(
        batch_index=0,
        chunks=chunking_result.chunks,
    )

    with pytest.raises(
        ValueError,
        match="counts must match",
    ):
        StudyMaterialPreparation(
            chunking_result=chunking_result,
            batches=(batch,),
            embedding_requests=(
                EmbeddingRequest(
                    texts=batch.texts,
                    task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
                ),
                EmbeddingRequest(
                    texts=batch.texts,
                    task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
                ),
            ),
        )


def test_preparation_rejects_reordered_chunks() -> None:
    """Prepared batches must preserve original chunk order."""

    chunking_result = build_chunking_result()
    reversed_batch = EmbeddingBatch(
        batch_index=0,
        chunks=tuple(
            reversed(chunking_result.chunks),
        ),
    )

    with pytest.raises(
        ValueError,
        match="preserve every chunk in order",
    ):
        StudyMaterialPreparation(
            chunking_result=chunking_result,
            batches=(reversed_batch,),
            embedding_requests=(
                EmbeddingRequest(
                    texts=reversed_batch.texts,
                    task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
                ),
            ),
        )


def test_preparation_rejects_request_text_mismatch() -> None:
    """Request text must correspond exactly to its prepared batch."""

    chunking_result = build_chunking_result()
    batch = EmbeddingBatch(
        batch_index=0,
        chunks=chunking_result.chunks,
    )

    with pytest.raises(
        ValueError,
        match="texts must match",
    ):
        StudyMaterialPreparation(
            chunking_result=chunking_result,
            batches=(batch,),
            embedding_requests=(
                EmbeddingRequest(
                    texts=("Different text",),
                    task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
                ),
            ),
        )
