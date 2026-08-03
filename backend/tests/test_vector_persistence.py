# File: /backend/tests/test_vector_persistence.py
# Purpose: Tests AI-chunk validation and Supabase RPC
# payload serialization without external service calls.

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

import pytest

from app.ai.chunking import StudyMaterialChunk
from app.ai.vector_persistence import (
    AI_VECTOR_DIMENSIONS,
    AIEmbeddingPersistenceValidationError,
    build_ai_chunk_persistence_payload,
)

STUDY_FILE_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)


def make_chunk(
    *,
    chunk_index: int = 0,
    material_id: str | None = None,
    text: str = "Alpha",
    start_offset: int = 0,
    source_name: str | None = "lecture.txt",
) -> StudyMaterialChunk:
    """Create one valid study-material chunk."""

    resolved_material_id = (
        material_id if material_id is not None else str(STUDY_FILE_ID)
    )

    return StudyMaterialChunk(
        material_id=resolved_material_id,
        chunk_index=chunk_index,
        text=text,
        start_offset=start_offset,
        end_offset=(start_offset + len(text)),
        source_name=source_name,
    )


def make_embedding(
    *,
    value: float = 0.125,
) -> tuple[float, ...]:
    """Create one valid 768-dimensional embedding."""

    return tuple(
        value
        for _ in range(
            AI_VECTOR_DIMENSIONS,
        )
    )


def build_payload(
    *,
    chunks: Sequence[StudyMaterialChunk] | None = None,
    embeddings: Sequence[Sequence[float]] | None = None,
    embedding_model: str = "gemini-embedding-2",
    embedding_dimensions: int = (AI_VECTOR_DIMENSIONS),
    original_character_count: int = 5,
):
    """Build a payload with overridable test values."""

    resolved_chunks = (
        list(chunks)
        if chunks is not None
        else [
            make_chunk(),
        ]
    )

    resolved_embeddings = (
        list(embeddings)
        if embeddings is not None
        else [
            make_embedding(),
        ]
    )

    return build_ai_chunk_persistence_payload(
        study_file_id=STUDY_FILE_ID,
        embedding_model=embedding_model,
        embedding_dimensions=(embedding_dimensions),
        original_character_count=(original_character_count),
        chunks=resolved_chunks,
        embeddings=resolved_embeddings,
    )


def test_builds_serializable_rpc_payload() -> None:
    """Valid chunks and vectors produce the RPC contract."""

    payload = build_payload()

    assert payload.chunk_count == 1

    assert payload.embedding_model == ("gemini-embedding-2")

    assert payload.embedding_dimensions == 768

    rpc_payload = payload.to_rpc_payload()

    assert rpc_payload["p_study_file_id"] == str(
        STUDY_FILE_ID,
    )

    assert rpc_payload["p_embedding_model"] == "gemini-embedding-2"

    assert rpc_payload["p_embedding_dimensions"] == 768

    assert rpc_payload["p_original_character_count"] == 5

    serialized_chunk = rpc_payload["p_chunks"][0]

    assert serialized_chunk["chunk_index"] == 0

    assert serialized_chunk["content"] == "Alpha"

    assert serialized_chunk["start_offset"] == 0

    assert serialized_chunk["end_offset"] == 5

    assert serialized_chunk["source_name"] == "lecture.txt"

    assert (
        len(
            serialized_chunk["embedding"],
        )
        == 768
    )

    assert serialized_chunk["metadata"]["material_id"] == str(
        STUDY_FILE_ID,
    )

    assert serialized_chunk["metadata"]["chunk_key"]


def test_normalizes_embedding_model() -> None:
    """Surrounding model whitespace is removed."""

    payload = build_payload(
        embedding_model=("  gemini-embedding-2  "),
    )

    assert payload.embedding_model == ("gemini-embedding-2")


def test_rejects_empty_embedding_model() -> None:
    """The embedding model cannot be empty."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="embedding model is required",
    ):
        build_payload(
            embedding_model="   ",
        )


def test_rejects_long_embedding_model() -> None:
    """The model name must fit the database column contract."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="model name is too long",
    ):
        build_payload(
            embedding_model="m" * 121,
        )


def test_rejects_non_768_dimensions() -> None:
    """The payload must match vector(768)."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="must equal 768",
    ):
        build_payload(
            embedding_dimensions=767,
        )


def test_rejects_invalid_character_count() -> None:
    """The normalized material length must be positive."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="character count must be positive",
    ):
        build_payload(
            original_character_count=0,
        )


def test_rejects_empty_chunks() -> None:
    """At least one prepared chunk must exist."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="At least one AI chunk",
    ):
        build_payload(
            chunks=[],
            embeddings=[],
        )


def test_rejects_chunk_embedding_count_mismatch() -> None:
    """Every prepared chunk must have one vector."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="exactly one embedding",
    ):
        build_payload(
            chunks=[
                make_chunk(),
            ],
            embeddings=[],
        )


def test_rejects_noncontiguous_chunk_indexes() -> None:
    """Chunk indexes must begin at zero and remain ordered."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="contiguous",
    ):
        build_payload(
            chunks=[
                make_chunk(
                    chunk_index=1,
                ),
            ],
        )


def test_rejects_mismatched_material_id() -> None:
    """Chunks must belong to the requested study file."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="target study file",
    ):
        build_payload(
            chunks=[
                make_chunk(
                    material_id=("22222222-2222-4222-8222-222222222222"),
                ),
            ],
        )


def test_rejects_chunk_past_material_length() -> None:
    """Offsets cannot exceed the normalized material."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="exceed",
    ):
        build_payload(
            original_character_count=4,
        )


def test_rejects_wrong_embedding_length() -> None:
    """Every vector must contain 768 values."""

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="wrong number of dimensions",
    ):
        build_payload(
            embeddings=[
                (0.1,) * 767,
            ],
        )


def test_rejects_nonnumeric_embedding_value() -> None:
    """Vector entries must contain only real numbers."""

    invalid_embedding = [
        0.1
        for _ in range(
            AI_VECTOR_DIMENSIONS,
        )
    ]

    invalid_embedding[10] = "invalid"

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="real numbers",
    ):
        build_payload(
            embeddings=[
                invalid_embedding,
            ],
        )


def test_rejects_boolean_embedding_value() -> None:
    """Boolean values must not be accepted as numeric vectors."""

    invalid_embedding = [
        0.1
        for _ in range(
            AI_VECTOR_DIMENSIONS,
        )
    ]

    invalid_embedding[10] = True

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="real numbers",
    ):
        build_payload(
            embeddings=[
                invalid_embedding,
            ],
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_rejects_nonfinite_embedding_values(
    invalid_value: float,
) -> None:
    """NaN and infinite vector entries cannot be persisted."""

    invalid_embedding = [
        0.1
        for _ in range(
            AI_VECTOR_DIMENSIONS,
        )
    ]

    invalid_embedding[10] = invalid_value

    with pytest.raises(
        AIEmbeddingPersistenceValidationError,
        match="must be finite",
    ):
        build_payload(
            embeddings=[
                invalid_embedding,
            ],
        )
