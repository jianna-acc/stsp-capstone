# File: /backend/app/services/flashcard_service.py
# Purpose: Provides the application-facing persistence service
# for generated and saved Flashcard decks.

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.schemas.flashcard import (
    FlashcardDeckResponse,
    FlashcardItem,
    FlashcardScopeType,
    FlashcardSource,
)
from app.schemas.flashcard_summary import (
    FlashcardDeckSummary,
)


class _FlashcardRepository(
    Protocol,
):
    """Persistence operations required by FlashcardService."""

    def create_deck(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: FlashcardScopeType,
        title: str,
        requested_card_count: int,
        cards: Sequence[
            FlashcardItem,
        ],
        sources: Sequence[
            FlashcardSource,
        ],
        generation_model: str,
    ) -> FlashcardDeckResponse: ...

    def list_decks(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
    ) -> tuple[
        FlashcardDeckSummary,
        ...,
    ]: ...

    def get_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> FlashcardDeckResponse | None: ...

    def delete_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> bool: ...


class FlashcardService:
    """Coordinates saved Flashcard persistence operations."""

    def __init__(
        self,
        repository: _FlashcardRepository,
    ) -> None:
        self._repository = repository

    def create_deck(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: FlashcardScopeType,
        title: str,
        requested_card_count: int,
        cards: Sequence[
            FlashcardItem,
        ],
        sources: Sequence[
            FlashcardSource,
        ],
        generation_model: str,
    ) -> FlashcardDeckResponse:
        """Persist one generated Flashcard deck."""

        return self._repository.create_deck(
            user_id=user_id,
            subject_id=subject_id,
            study_file_id=study_file_id,
            scope_type=scope_type,
            title=title,
            requested_card_count=requested_card_count,
            cards=cards,
            sources=sources,
            generation_model=generation_model,
        )

    def list_decks(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
    ) -> tuple[
        FlashcardDeckSummary,
        ...,
    ]:
        """Return saved decks belonging to the student."""

        return self._repository.list_decks(
            user_id=user_id,
            subject_id=subject_id,
        )

    def get_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> FlashcardDeckResponse | None:
        """Return one owned Flashcard deck."""

        return self._repository.get_deck(
            user_id=user_id,
            deck_id=deck_id,
        )

    def delete_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> bool:
        """Delete one owned Flashcard deck."""

        return self._repository.delete_deck(
            user_id=user_id,
            deck_id=deck_id,
        )