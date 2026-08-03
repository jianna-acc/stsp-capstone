# File: /backend/app/ai/vector_persistence.py
# Purpose: Validates AI chunks and embedding vectors and
# serializes them for trusted Supabase persistence.

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Any
from uuid import UUID

from app.ai.chunking import StudyMaterialChunk

AI_VECTOR_DIMENSIONS = 768

MAX_AI_CHUNKS_PER_PERSISTENCE = 10_000

MAX_EMBEDDING_MODEL_LENGTH = 120

MAX_SOURCE_NAME_LENGTH = 255


class AIEmbeddingPersistenceValidationError(
    ValueError,
):
    """Raised when AI chunks cannot be safely persisted."""


@dataclass(frozen=True)
class AIChunkEmbeddingRecord:
    """One AI chunk paired with its validated embedding."""

    chunk_index: int
    content: str

    start_offset: int
    end_offset: int

    source_name: str | None

    embedding: tuple[float, ...]

    metadata: dict[str, Any]

    def to_rpc_chunk(
        self,
    ) -> dict[str, Any]:
        """Serialize one record for the persistence RPC."""

        return {
            "chunk_index": self.chunk_index,
            "content": self.content,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "source_name": self.source_name,
            "embedding": list(
                self.embedding,
            ),
            "metadata": dict(
                self.metadata,
            ),
        }


@dataclass(frozen=True)
class AIChunkPersistencePayload:
    """Validated RPC payload for one study material."""

    study_file_id: UUID

    embedding_model: str
    embedding_dimensions: int

    original_character_count: int

    records: tuple[
        AIChunkEmbeddingRecord,
        ...,
    ]

    @property
    def chunk_count(
        self,
    ) -> int:
        """Return the number of serialized AI chunks."""

        return len(
            self.records,
        )

    def to_rpc_payload(
        self,
    ) -> dict[str, Any]:
        """Serialize this payload for Supabase PostgREST."""

        return {
            "p_study_file_id": str(
                self.study_file_id,
            ),
            "p_embedding_model": (self.embedding_model),
            "p_embedding_dimensions": (self.embedding_dimensions),
            "p_original_character_count": (self.original_character_count),
            "p_chunks": [record.to_rpc_chunk() for record in self.records],
        }


def build_ai_chunk_persistence_payload(
    *,
    study_file_id: UUID,
    embedding_model: str,
    embedding_dimensions: int,
    original_character_count: int,
    chunks: Sequence[StudyMaterialChunk],
    embeddings: Sequence[Sequence[float]],
) -> AIChunkPersistencePayload:
    """Validate chunks and vectors and build an RPC payload."""

    normalized_embedding_model = embedding_model.strip()

    if not normalized_embedding_model:
        raise AIEmbeddingPersistenceValidationError(
            "The embedding model is required.",
        )

    if (
        len(
            normalized_embedding_model,
        )
        > MAX_EMBEDDING_MODEL_LENGTH
    ):
        raise AIEmbeddingPersistenceValidationError(
            "The embedding model name is too long.",
        )

    if embedding_dimensions != AI_VECTOR_DIMENSIONS:
        raise AIEmbeddingPersistenceValidationError(
            "Embedding dimensions must equal 768.",
        )

    if original_character_count < 1:
        raise AIEmbeddingPersistenceValidationError(
            "The original character count must be positive.",
        )

    if not chunks:
        raise AIEmbeddingPersistenceValidationError(
            "At least one AI chunk is required.",
        )

    if len(chunks) > MAX_AI_CHUNKS_PER_PERSISTENCE:
        raise AIEmbeddingPersistenceValidationError(
            "The AI chunk count exceeds the persistence limit.",
        )

    if len(chunks) != len(embeddings):
        raise AIEmbeddingPersistenceValidationError(
            "Every AI chunk must have exactly one embedding.",
        )

    expected_material_id = str(
        study_file_id,
    )

    records: list[AIChunkEmbeddingRecord] = []

    for expected_index, (
        chunk,
        embedding,
    ) in enumerate(
        zip(
            chunks,
            embeddings,
            strict=True,
        ),
    ):
        _validate_chunk(
            chunk=chunk,
            expected_index=expected_index,
            expected_material_id=expected_material_id,
            original_character_count=(original_character_count),
        )

        normalized_embedding = _normalize_embedding(
            embedding=embedding,
            expected_dimensions=(embedding_dimensions),
        )

        normalized_source_name = _normalize_source_name(
            source_name=chunk.source_name,
        )

        records.append(
            AIChunkEmbeddingRecord(
                chunk_index=chunk.chunk_index,
                content=chunk.text,
                start_offset=(chunk.start_offset),
                end_offset=(chunk.end_offset),
                source_name=(normalized_source_name),
                embedding=(normalized_embedding),
                metadata={
                    "chunk_key": (chunk.chunk_key),
                    "material_id": (chunk.material_id),
                },
            ),
        )

    return AIChunkPersistencePayload(
        study_file_id=study_file_id,
        embedding_model=(normalized_embedding_model),
        embedding_dimensions=(embedding_dimensions),
        original_character_count=(original_character_count),
        records=tuple(
            records,
        ),
    )


def _validate_chunk(
    *,
    chunk: StudyMaterialChunk,
    expected_index: int,
    expected_material_id: str,
    original_character_count: int,
) -> None:
    """Validate one prepared study-material chunk."""

    if chunk.chunk_index != expected_index:
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk indexes must be contiguous and begin at zero.",
        )

    if chunk.material_id != expected_material_id:
        raise AIEmbeddingPersistenceValidationError(
            "Every AI chunk must belong to the target study file.",
        )

    if not chunk.text:
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk content cannot be empty.",
        )

    if chunk.text != chunk.text.strip():
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk content must already be normalized.",
        )

    if chunk.start_offset < 0:
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk start offsets cannot be negative.",
        )

    if chunk.end_offset <= chunk.start_offset:
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk end offsets must follow their start offsets.",
        )

    if chunk.end_offset > original_character_count:
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk offsets exceed the normalized material length.",
        )

    if (
        len(
            chunk.text,
        )
        != chunk.end_offset - chunk.start_offset
    ):
        raise AIEmbeddingPersistenceValidationError(
            "AI chunk content does not match its character offsets.",
        )


def _normalize_source_name(
    *,
    source_name: str | None,
) -> str | None:
    """Normalize and validate an optional source filename."""

    if source_name is None:
        return None

    normalized_source_name = source_name.strip()

    if not normalized_source_name:
        return None

    if (
        len(
            normalized_source_name,
        )
        > MAX_SOURCE_NAME_LENGTH
    ):
        raise AIEmbeddingPersistenceValidationError(
            "The AI chunk source name is too long.",
        )

    return normalized_source_name


def _normalize_embedding(
    *,
    embedding: Sequence[float],
    expected_dimensions: int,
) -> tuple[float, ...]:
    """Validate one embedding and return immutable floats."""

    if isinstance(
        embedding,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        raise AIEmbeddingPersistenceValidationError(
            "An embedding must be a numeric sequence.",
        )

    if len(embedding) != expected_dimensions:
        raise AIEmbeddingPersistenceValidationError(
            "An embedding has the wrong number of dimensions.",
        )

    normalized_values: list[float] = []

    for value in embedding:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            Real,
        ):
            raise AIEmbeddingPersistenceValidationError(
                "Embedding values must be real numbers.",
            )

        normalized_value = float(
            value,
        )

        if not isfinite(
            normalized_value,
        ):
            raise AIEmbeddingPersistenceValidationError(
                "Embedding values must be finite.",
            )

        normalized_values.append(
            normalized_value,
        )

    return tuple(
        normalized_values,
    )
