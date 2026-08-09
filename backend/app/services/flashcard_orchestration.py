# File: /backend/app/services/flashcard_orchestration.py
# Purpose: Coordinates authenticated Flashcard source loading,
# AI generation, deterministic title creation, and persistence.

from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.schemas.flashcard import (
    MAX_FLASHCARD_TITLE_CHARACTERS,
    FlashcardDeckResponse,
    FlashcardGenerateRequest,
    FlashcardScopeType,
)
from app.services.flashcard_errors import (
    FlashcardOrchestrationError,
)
from app.services.flashcard_generation import (
    FlashcardGenerationResult,
)
from app.services.flashcard_source_loader import (
    FlashcardSourceBundle,
)

_FLASHCARD_TITLE_SUFFIX = " Flashcards"
_SUBJECT_FLASHCARD_TITLE = "Study Flashcards"


class _FlashcardSourceLoader(
    Protocol,
):
    async def load(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> FlashcardSourceBundle:
        """Load complete owned Flashcard source material."""


class _FlashcardGenerationService(
    Protocol,
):
    async def generate(
        self,
        *,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> FlashcardGenerationResult:
        """Generate validated Flashcard content."""


class _FlashcardPersistenceService(
    Protocol,
):
    def create_deck(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: FlashcardScopeType,
        title: str,
        requested_card_count: int,
        cards: object,
        sources: object,
        generation_model: str,
    ) -> FlashcardDeckResponse:
        """Persist one validated generated deck."""


class FlashcardOrchestrationService:
    """Run the complete authenticated Flashcard generation flow."""

    def __init__(
        self,
        *,
        source_loader: _FlashcardSourceLoader,
        generation_service: _FlashcardGenerationService,
        flashcard_service: _FlashcardPersistenceService,
    ) -> None:
        self._source_loader = source_loader
        self._generation_service = generation_service
        self._flashcard_service = flashcard_service

    async def generate_deck(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> FlashcardDeckResponse:
        """Generate, validate, and persist one Flashcard deck."""

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

        title = self._build_title(
            request=request,
            source_bundle=source_bundle,
        )

        return self._flashcard_service.create_deck(
            user_id=user_id,
            subject_id=request.subject_id,
            study_file_id=request.study_file_id,
            scope_type=request.scope_type,
            title=title,
            requested_card_count=request.card_count,
            cards=generation.content.cards,
            sources=source_bundle.sources,
            generation_model=generation.model,
        )

    def _validate_source_bundle(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> None:
        """Reject inconsistent data before invoking the AI provider."""

        if source_bundle.user_id != user_id:
            raise FlashcardOrchestrationError(
                "Flashcard source ownership does not match "
                "the authenticated user.",
            )

        if (
            source_bundle.subject_id
            != request.subject_id
        ):
            raise FlashcardOrchestrationError(
                "Flashcard source subject does not match "
                "the generation request.",
            )

        if (
            source_bundle.scope_type
            is not request.scope_type
        ):
            raise FlashcardOrchestrationError(
                "Flashcard source scope does not match "
                "the generation request.",
            )

        if (
            request.scope_type
            is FlashcardScopeType.FILE
            and source_bundle.study_file_id
            != request.study_file_id
        ):
            raise FlashcardOrchestrationError(
                "Flashcard source file does not match "
                "the generation request.",
            )

        if (
            request.scope_type
            is FlashcardScopeType.SUBJECT
            and source_bundle.study_file_id is not None
        ):
            raise FlashcardOrchestrationError(
                "Subject Flashcard generation cannot use "
                "a single-file source bundle.",
            )

    def _build_title(
        self,
        *,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> str:
        """Build a deterministic title within the schema limit."""

        if (
            request.scope_type
            is FlashcardScopeType.SUBJECT
        ):
            return _SUBJECT_FLASHCARD_TITLE

        source_name = source_bundle.chunks[
            0
        ].source_name.strip()

        source_stem = Path(
            source_name,
        ).stem.strip()

        if not source_stem:
            source_stem = "Study"

        available_base_characters = (
            MAX_FLASHCARD_TITLE_CHARACTERS
            - len(
                _FLASHCARD_TITLE_SUFFIX,
            )
        )

        source_stem = source_stem[
            :available_base_characters
        ].rstrip()

        if not source_stem:
            source_stem = "Study"

        return (
            source_stem
            + _FLASHCARD_TITLE_SUFFIX
        )