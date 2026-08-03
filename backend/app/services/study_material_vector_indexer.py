# File: /backend/app/services/study_material_vector_indexer.py
# Purpose: Orchestrates study-material embedding, validated
# persistence-payload creation, and trusted Supabase storage.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.ai.preparation import StudyMaterialPreparation
from app.ai.vector_persistence import (
    AIChunkPersistencePayload,
    AIEmbeddingPersistenceValidationError,
    build_ai_chunk_persistence_payload,
)
from app.services.study_material_embedder import (
    StudyMaterialEmbedder,
    StudyMaterialEmbeddingError,
    StudyMaterialEmbeddingResult,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
    SupabaseAdminService,
)


class StudyMaterialVectorIndexingError(
    RuntimeError,
):
    """Base error for vector-indexing orchestration."""


class StudyMaterialVectorPreparationError(
    StudyMaterialVectorIndexingError,
):
    """Raised when preparation and persistence data conflict."""


class StudyMaterialVectorEmbeddingStepError(
    StudyMaterialVectorIndexingError,
):
    """Raised when embedding execution fails."""


class StudyMaterialVectorPersistenceStepError(
    StudyMaterialVectorIndexingError,
):
    """Raised when vector persistence fails."""


class StudyMaterialEmbedderProtocol(
    Protocol,
):
    """Embedding dependency required by the indexer."""

    async def embed_preparation(
        self,
        preparation: StudyMaterialPreparation,
    ) -> StudyMaterialEmbeddingResult:
        """Embed every prepared study-material chunk."""

        ...


class AIChunkPersistenceProtocol(
    Protocol,
):
    """Trusted persistence dependency required by the indexer."""

    async def persist_ai_chunks(
        self,
        payload: AIChunkPersistencePayload,
    ) -> int:
        """Persist validated AI chunks and embeddings."""

        ...


@dataclass(frozen=True)
class StudyMaterialVectorIndexingResult:
    """Summary of one successful vector-indexing operation."""

    study_file_id: UUID

    embedding_model: str
    embedding_dimensions: int

    chunk_count: int
    batch_count: int
    persisted_chunk_count: int


class StudyMaterialVectorIndexer:
    """Embeds prepared chunks and persists their vectors."""

    def __init__(
        self,
        *,
        embedder: StudyMaterialEmbedderProtocol,
        persistence: AIChunkPersistenceProtocol,
    ) -> None:
        self._embedder = embedder
        self._persistence = persistence

    async def index_preparation(
        self,
        *,
        study_file_id: UUID,
        preparation: StudyMaterialPreparation,
    ) -> StudyMaterialVectorIndexingResult:
        """Embed and persist one prepared study material."""

        chunking_result = preparation.chunking_result

        expected_material_id = str(
            study_file_id,
        )

        if chunking_result.material_id != expected_material_id:
            raise StudyMaterialVectorPreparationError(
                "The preparation does not belong to the target study file.",
            )

        chunks = tuple(
            chunking_result.chunks,
        )

        if not chunks:
            raise StudyMaterialVectorPreparationError(
                "At least one prepared AI chunk is required.",
            )

        if len(chunks) != preparation.chunk_count:
            raise StudyMaterialVectorPreparationError(
                "The preparation chunk count does not match its chunking result.",
            )

        try:
            embedding_result = await self._embedder.embed_preparation(
                preparation,
            )
        except StudyMaterialEmbeddingError as exc:
            raise StudyMaterialVectorEmbeddingStepError(
                "Study-material embedding failed.",
            ) from exc

        if embedding_result.chunk_count != len(chunks):
            raise StudyMaterialVectorEmbeddingStepError(
                "The embedding result count does not match the prepared chunk count.",
            )

        try:
            persistence_payload = build_ai_chunk_persistence_payload(
                study_file_id=study_file_id,
                embedding_model=(embedding_result.embedding_model),
                embedding_dimensions=(embedding_result.embedding_dimensions),
                original_character_count=(chunking_result.original_character_count),
                chunks=chunks,
                embeddings=(embedding_result.embeddings),
            )
        except AIEmbeddingPersistenceValidationError as exc:
            raise StudyMaterialVectorPreparationError(
                "The embedded chunks could not be "
                "converted into a persistence payload.",
            ) from exc

        try:
            persisted_chunk_count = await self._persistence.persist_ai_chunks(
                payload=persistence_payload,
            )
        except SupabaseAdminError as exc:
            raise StudyMaterialVectorPersistenceStepError(
                "Study-material vector persistence failed.",
            ) from exc

        if persisted_chunk_count != persistence_payload.chunk_count:
            raise StudyMaterialVectorPersistenceStepError(
                "The persisted AI-chunk count does not match the requested count.",
            )

        return StudyMaterialVectorIndexingResult(
            study_file_id=study_file_id,
            embedding_model=(embedding_result.embedding_model),
            embedding_dimensions=(embedding_result.embedding_dimensions),
            chunk_count=(persistence_payload.chunk_count),
            batch_count=(embedding_result.batch_count),
            persisted_chunk_count=(persisted_chunk_count),
        )


def create_study_material_vector_indexer(
    *,
    embedder: StudyMaterialEmbedder,
    persistence: SupabaseAdminService,
) -> StudyMaterialVectorIndexer:
    """Create the production vector-indexing orchestrator."""

    return StudyMaterialVectorIndexer(
        embedder=embedder,
        persistence=persistence,
    )
