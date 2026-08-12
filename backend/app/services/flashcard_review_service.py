# File: /backend/app/services/flashcard_review_service.py
# Purpose: Coordinates durable Flashcard self-assessment reviews.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.flashcard_review import (
    FlashcardReviewOutcome,
    FlashcardReviewResponse,
)


class _FlashcardReviewRepository(
    Protocol,
):
    """Persistence required by FlashcardReviewService."""

    def create_review(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        card_position: int,
        outcome: FlashcardReviewOutcome,
    ) -> FlashcardReviewResponse: ...


class FlashcardReviewService:
    """Coordinates Flashcard self-assessment persistence."""

    def __init__(
        self,
        repository: _FlashcardReviewRepository,
    ) -> None:
        self._repository = repository

    def record_review(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        card_position: int,
        outcome: FlashcardReviewOutcome,
    ) -> FlashcardReviewResponse:
        """Persist one student Flashcard review outcome."""

        return self._repository.create_review(
            user_id=user_id,
            deck_id=deck_id,
            card_position=card_position,
            outcome=outcome,
        )