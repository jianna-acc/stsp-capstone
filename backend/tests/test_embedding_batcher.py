# File: /backend/tests/test_embedding_batcher.py
# Purpose: Verifies deterministic embedding batching, chunk order,
# batch indexes, configured limits, and document requests.

from typing import Any

from app.ai import (
    ChunkingResult,
    EmbeddingBatchPreparer,
    EmbeddingTaskType,
    StudyMaterialChunk,
)
from app.core.config import Settings


def build_preparer(
    *,
    batch_size: int = 2,
) -> EmbeddingBatchPreparer:
    """Create an isolated embedding batch preparer."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "ai_embedding_batch_size": batch_size,
        "_env_file": None,
    }

    return EmbeddingBatchPreparer(
        settings=Settings(**values),
    )


def build_result(
    chunk_count: int,
) -> ChunkingResult:
    """Create one deterministic valid chunking result."""

    chunks: list[StudyMaterialChunk] = []

    for chunk_index in range(chunk_count):
        text = f"Chunk {chunk_index} study content."
        start_offset = chunk_index * 40
        end_offset = start_offset + len(text)

        chunks.append(
            StudyMaterialChunk(
                material_id="material-1",
                chunk_index=chunk_index,
                text=text,
                start_offset=start_offset,
                end_offset=end_offset,
                source_name="biology.pdf",
            ),
        )

    final_end_offset = chunks[-1].end_offset

    return ChunkingResult(
        material_id="material-1",
        original_character_count=final_end_offset,
        chunks=tuple(chunks),
        source_name="biology.pdf",
    )


def test_prepare_splits_chunks_by_batch_size() -> None:
    """Chunks must be divided using the configured batch size."""

    preparer = build_preparer(
        batch_size=2,
    )
    batches = preparer.prepare(
        build_result(5),
    )

    assert [
        len(batch.chunks)
        for batch in batches
    ] == [
        2,
        2,
        1,
    ]


def test_prepare_preserves_chunk_order() -> None:
    """Flattened batches must match the original chunk order."""

    result = build_result(5)
    preparer = build_preparer(
        batch_size=2,
    )

    batches = preparer.prepare(result)

    flattened_chunks = tuple(
        chunk
        for batch in batches
        for chunk in batch.chunks
    )

    assert flattened_chunks == result.chunks


def test_prepare_is_deterministic() -> None:
    """Identical input and settings must produce equal batches."""

    result = build_result(5)
    preparer = build_preparer(
        batch_size=2,
    )

    first_batches = preparer.prepare(result)
    second_batches = preparer.prepare(result)

    assert first_batches == second_batches


def test_prepare_handles_exact_multiple() -> None:
    """Exact multiples must not create an empty final batch."""

    preparer = build_preparer(
        batch_size=2,
    )
    batches = preparer.prepare(
        build_result(4),
    )

    assert len(batches) == 2
    assert all(
        len(batch.chunks) == 2
        for batch in batches
    )


def test_prepare_handles_one_chunk() -> None:
    """One chunk must create one one-item batch."""

    preparer = build_preparer(
        batch_size=4,
    )
    batches = preparer.prepare(
        build_result(1),
    )

    assert len(batches) == 1
    assert len(batches[0].chunks) == 1


def test_batch_indices_are_contiguous() -> None:
    """Batch indexes must start at zero without gaps."""

    preparer = build_preparer(
        batch_size=2,
    )
    batches = preparer.prepare(
        build_result(7),
    )

    assert [
        batch.batch_index
        for batch in batches
    ] == list(
        range(len(batches)),
    )


def test_build_request_uses_document_task_type() -> None:
    """Study-material batches must create document requests."""

    preparer = build_preparer(
        batch_size=2,
    )
    first_batch = preparer.prepare(
        build_result(3),
    )[0]

    request = preparer.build_request(
        first_batch,
    )

    assert (
        request.task_type
        is EmbeddingTaskType.RETRIEVAL_DOCUMENT
    )


def test_build_request_preserves_text_order() -> None:
    """Request text order must match the batch chunk order."""

    preparer = build_preparer(
        batch_size=3,
    )
    first_batch = preparer.prepare(
        build_result(3),
    )[0]

    request = preparer.build_request(
        first_batch,
    )

    assert request.texts == first_batch.texts


def test_prepare_requests_match_prepared_batches() -> None:
    """Prepared requests must correspond to batches in order."""

    result = build_result(5)
    preparer = build_preparer(
        batch_size=2,
    )

    batches = preparer.prepare(result)
    requests = preparer.prepare_requests(result)

    assert len(requests) == len(batches)

    for batch, request in zip(
        batches,
        requests,
        strict=True,
    ):
        assert request.texts == batch.texts
        assert (
            request.task_type
            is EmbeddingTaskType.RETRIEVAL_DOCUMENT
        )


def test_default_batch_size_is_respected() -> None:
    """The configured default must create a final partial batch."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "_env_file": None,
    }

    preparer = EmbeddingBatchPreparer(
        settings=Settings(**values),
    )
    batches = preparer.prepare(
        build_result(17),
    )

    assert [
        len(batch.chunks)
        for batch in batches
    ] == [
        16,
        1,
    ]