# File: /backend/app/services/quiz_orchestration.py

# Purpose: Coordinates Quiz source loading, AI generation,
# validation, and atomic persistence.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.quiz import (
    QuizDifficulty,
    QuizGeneratedContent,
    QuizGenerateRequest,
    QuizResponse,
    QuizScopeType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizGenerationResponseError,
    QuizValidationError,
)
from app.services.quiz_generation import (
    QuizGenerationResult,
)
from app.services.quiz_source_loader import (
    QuizSourceBundle,
)


class QuizSourceLoaderProtocol(
    Protocol,
):
    """Source-loading dependency required by Quiz orchestration."""

    async def load(
        self,
        *,
        user_id: UUID,
        request: QuizGenerateRequest,
    ) -> QuizSourceBundle:
        """Load complete Quiz source material."""


class QuizGenerationProtocol(
    Protocol,
):
    """AI-generation dependency required by Quiz orchestration."""

    async def generate(
        self,
        *,
        request: QuizGenerateRequest,
        source_bundle: QuizSourceBundle,
    ) -> QuizGenerationResult:
        """Generate validated structured Quiz content."""


class QuizPersistenceServiceProtocol(
    Protocol,
):
    """Persistence dependency required by Quiz orchestration."""

    def save_generated_quiz(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: QuizScopeType,
        quiz_type: QuizType,
        difficulty: QuizDifficulty,
        question_count: int,
        content: QuizGeneratedContent,
        generation_model: str,
    ) -> QuizResponse:
        """Save one generated Quiz."""


class QuizOrchestrationService:
    """Coordinate complete Quiz generation and persistence."""

    def __init__(
        self,
        *,
        source_loader: QuizSourceLoaderProtocol,
        generation_service: QuizGenerationProtocol,
        quiz_service: QuizPersistenceServiceProtocol,
    ) -> None:
        self._source_loader = source_loader
        self._generation_service = generation_service
        self._quiz_service = quiz_service

    async def generate_quiz(
        self,
        *,
        user_id: UUID,
        request: QuizGenerateRequest,
    ) -> QuizResponse:
        """Generate, atomically save, and return one Quiz."""

        if not isinstance(
            request,
            QuizGenerateRequest,
        ):
            raise QuizValidationError(
                "request must be a QuizGenerateRequest.",
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

        generation = await self._generation_service.generate(
            request=request,
            source_bundle=source_bundle,
        )

        self._validate_generation_metadata(
            generation=generation,
            source_bundle=source_bundle,
            request=request,
        )

        return self._quiz_service.save_generated_quiz(
            user_id=user_id,
            subject_id=request.subject_id,
            study_file_id=request.study_file_id,
            scope_type=request.scope_type,
            quiz_type=request.quiz_type,
            difficulty=request.difficulty,
            question_count=request.question_count,
            content=generation.content,
            generation_model=generation.model,
        )

    def _validate_source_bundle(
        self,
        *,
        user_id: UUID,
        request: QuizGenerateRequest,
        source_bundle: QuizSourceBundle,
    ) -> None:
        """Confirm loaded material still matches the caller."""

        if source_bundle.user_id != user_id:
            raise QuizValidationError(
                "Quiz source owner does not match "
                "the authenticated user.",
            )

        if (
            source_bundle.subject_id
            != request.subject_id
        ):
            raise QuizValidationError(
                "Quiz source subject does not match "
                "the request.",
            )

        if (
            source_bundle.scope_type
            != request.scope_type
        ):
            raise QuizValidationError(
                "Quiz source scope does not match "
                "the request.",
            )

        if (
            source_bundle.study_file_id
            != request.study_file_id
        ):
            raise QuizValidationError(
                "Quiz source file does not match "
                "the request.",
            )

    def _validate_generation_metadata(
        self,
        *,
        generation: QuizGenerationResult,
        source_bundle: QuizSourceBundle,
        request: QuizGenerateRequest,
    ) -> None:
        """Ensure generated metadata describes the exact sources."""

        if (
            generation.source_chunk_count
            != source_bundle.chunk_count
        ):
            raise QuizGenerationResponseError(
                "Quiz generation chunk metadata does not "
                "match the source bundle.",
            )

        if (
            generation.source_file_count
            != source_bundle.file_count
        ):
            raise QuizGenerationResponseError(
                "Quiz generation file metadata does not "
                "match the source bundle.",
            )

        if (
            generation.source_character_count
            != source_bundle.character_count
        ):
            raise QuizGenerationResponseError(
                "Quiz generation source-size metadata does "
                "not match the source bundle.",
            )

        if (
            len(
                generation.content.questions,
            )
            != request.question_count
        ):
            raise QuizGenerationResponseError(
                "Quiz generation question count does not "
                "match the request.",
            )