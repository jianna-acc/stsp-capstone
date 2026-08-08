# File: /backend/app/services/reviewer_orchestration.py
# Purpose: Coordinates reviewer source loading, AI generation,
# source tracking, and persistence.

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.schemas.reviewer import (
    MAX_REVIEWER_SOURCES,
    MAX_REVIEWER_TITLE_CHARACTERS,
    ReviewerContent,
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
)
from app.services.reviewer_errors import (
    ReviewerGenerationResponseError,
    ReviewerValidationError,
)
from app.services.reviewer_generation import (
    ReviewerGenerationResult,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
)


class ReviewerSourceLoaderProtocol(
    Protocol,
):
    """Source-loading dependency required by orchestration."""

    async def load(
        self,
        *,
        user_id: UUID,
        request: ReviewerGenerateRequest,
    ) -> ReviewerSourceBundle:
        """Load complete reviewer source material."""


class ReviewerGenerationProtocol(
    Protocol,
):
    """AI-generation dependency required by orchestration."""

    async def generate(
        self,
        *,
        request: ReviewerGenerateRequest,
        source_bundle: ReviewerSourceBundle,
    ) -> ReviewerGenerationResult:
        """Generate structured reviewer content."""


class ReviewerPersistenceServiceProtocol(
    Protocol,
):
    """Persistence dependency required by orchestration."""

    def save_generated_reviewer(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: ReviewerScopeType,
        title: str,
        reviewer_length: ReviewerLength,
        content: ReviewerContent,
        sources: Sequence[
            ReviewerSource
        ],
        generation_model: str,
    ) -> ReviewerResponse:
        """Save one generated reviewer."""

    def get_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse:
        """Load one owned reviewer."""

    def save_regenerated_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
        content: ReviewerContent,
        sources: Sequence[
            ReviewerSource,
        ],
        generation_model: str,
        generated_at: datetime,
    ) -> ReviewerResponse:
        """Replace generated content on one owned reviewer."""


class ReviewerOrchestrationService:
    """Coordinate complete reviewer generation and persistence."""

    def __init__(
        self,
        *,
        source_loader: ReviewerSourceLoaderProtocol,
        generation_service: ReviewerGenerationProtocol,
        reviewer_service: ReviewerPersistenceServiceProtocol,
    ) -> None:
        self._source_loader = source_loader
        self._generation_service = generation_service
        self._reviewer_service = reviewer_service

    async def generate_reviewer(
        self,
        *,
        user_id: UUID,
        request: ReviewerGenerateRequest,
    ) -> ReviewerResponse:
        """Generate, save, and return one reviewer."""

        if not isinstance(
            request,
            ReviewerGenerateRequest,
        ):
            raise ReviewerValidationError(
                "request must be a ReviewerGenerateRequest.",
            )

        source_bundle = await self._source_loader.load(
            user_id=user_id,
            request=request,
        )

        self._validate_source_bundle(
            user_id=user_id,
            request=request,
            source_bundle=source_bundle,
        )

        sources = self._build_sources(
            source_bundle,
        )

        generation = (
            await self._generation_service.generate(
                request=request,
                source_bundle=source_bundle,
            )
        )

        self._validate_generation_metadata(
            generation=generation,
            source_bundle=source_bundle,
        )

        title = self._build_title(
            request=request,
            source_bundle=source_bundle,
        )

        return self._reviewer_service.save_generated_reviewer(
            user_id=user_id,
            subject_id=request.subject_id,
            study_file_id=request.study_file_id,
            scope_type=request.scope_type,
            title=title,
            reviewer_length=request.reviewer_length,
            content=generation.content,
            sources=sources,
            generation_model=generation.model,
        )

    async def regenerate_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse:
        """Regenerate one saved reviewer using its existing settings."""

        saved_reviewer = (
            self._reviewer_service.get_reviewer(
                user_id=user_id,
                reviewer_id=reviewer_id,
            )
        )

        request = ReviewerGenerateRequest(
            scope_type=saved_reviewer.scope_type,
            subject_id=saved_reviewer.subject_id,
            study_file_id=(
                saved_reviewer.study_file_id
            ),
            reviewer_length=(
                saved_reviewer.reviewer_length
            ),
        )

        source_bundle = (
            await self._source_loader.load(
                user_id=user_id,
                request=request,
            )
        )

        self._validate_source_bundle(
            user_id=user_id,
            request=request,
            source_bundle=source_bundle,
        )

        sources = self._build_sources(
            source_bundle,
        )

        generation = (
            await self._generation_service.generate(
                request=request,
                source_bundle=source_bundle,
            )
        )

        self._validate_generation_metadata(
            generation=generation,
            source_bundle=source_bundle,
        )

        generated_at = datetime.now(
            UTC,
        )

        return (
            self._reviewer_service.save_regenerated_reviewer(
                user_id=user_id,
                reviewer_id=reviewer_id,
                content=generation.content,
                sources=sources,
                generation_model=generation.model,
                generated_at=generated_at,
            )
        )


    def _build_sources(
        self,
        source_bundle: ReviewerSourceBundle,
    ) -> tuple[
        ReviewerSource,
        ...,
    ]:
        """Convert loaded chunks into persisted source metadata."""

        if (
            source_bundle.chunk_count
            > MAX_REVIEWER_SOURCES
        ):
            raise ReviewerValidationError(
                "The reviewer contains too many source "
                "chunks to save safely.",
            )

        return tuple(
            ReviewerSource(
                study_file_id=chunk.study_file_id,
                source_name=chunk.source_name,
                chunk_index=chunk.chunk_index,
                locator_type=chunk.locator_type,
                locator_label=chunk.locator_label,
            )
            for chunk in source_bundle.chunks
        )

    def _validate_source_bundle(
        self,
        *,
        user_id: UUID,
        request: ReviewerGenerateRequest,
        source_bundle: ReviewerSourceBundle,
    ) -> None:
        """Confirm loaded material still matches the caller."""

        if source_bundle.user_id != user_id:
            raise ReviewerValidationError(
                "Reviewer source owner does not match "
                "the authenticated user.",
            )

        if (
            source_bundle.subject_id
            != request.subject_id
        ):
            raise ReviewerValidationError(
                "Reviewer source subject does not match "
                "the request.",
            )

        if (
            source_bundle.scope_type
            != request.scope_type
        ):
            raise ReviewerValidationError(
                "Reviewer source scope does not match "
                "the request.",
            )

        if (
            source_bundle.study_file_id
            != request.study_file_id
        ):
            raise ReviewerValidationError(
                "Reviewer source file does not match "
                "the request.",
            )

    def _validate_generation_metadata(
        self,
        *,
        generation: ReviewerGenerationResult,
        source_bundle: ReviewerSourceBundle,
    ) -> None:
        """Ensure AI metadata describes the exact loaded sources."""

        source_character_count = sum(
            len(
                chunk.content,
            )
            for chunk in source_bundle.chunks
        )

        if (
            generation.source_chunk_count
            != source_bundle.chunk_count
        ):
            raise ReviewerGenerationResponseError(
                "Reviewer generation chunk metadata "
                "does not match the source bundle.",
            )

        if (
            generation.source_file_count
            != source_bundle.file_count
        ):
            raise ReviewerGenerationResponseError(
                "Reviewer generation file metadata "
                "does not match the source bundle.",
            )

        if (
            generation.source_character_count
            != source_character_count
        ):
            raise ReviewerGenerationResponseError(
                "Reviewer generation source-size metadata "
                "does not match the source bundle.",
            )

    def _build_title(
        self,
        *,
        request: ReviewerGenerateRequest,
        source_bundle: ReviewerSourceBundle,
    ) -> str:
        """Create a stable display title for the saved reviewer."""

        if (
            request.scope_type
            == ReviewerScopeType.SUBJECT
        ):
            file_word = (
                "file"
                if source_bundle.file_count == 1
                else "files"
            )

            return (
                "Subject Reviewer "
                f"({source_bundle.file_count} {file_word})"
            )

        source_name = (
            source_bundle.chunks[
                0
            ].source_name
        )

        source_stem = Path(
            source_name,
        ).stem.strip()

        if not source_stem:
            source_stem = source_name.strip()

        suffix = " Reviewer"

        maximum_stem_length = (
            MAX_REVIEWER_TITLE_CHARACTERS
            - len(
                suffix,
            )
        )

        normalized_stem = source_stem[
            :maximum_stem_length
        ].rstrip()

        if not normalized_stem:
            normalized_stem = "Study Material"

        return (
            f"{normalized_stem}{suffix}"
        )