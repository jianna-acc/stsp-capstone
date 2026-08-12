# File: /backend/app/schemas/flashcard_review.py
# Purpose: Defines Flashcard self-assessment review API contracts.

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class FlashcardReviewOutcome(
    StrEnum,
):
    """Supported student Flashcard self-assessment outcomes."""

    KNOWN = "known"
    REVIEW_AGAIN = "review_again"


class FlashcardReviewCreateRequest(
    BaseModel,
):
    """Request to persist one Flashcard study review event."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    card_position: int = Field(
        ge=0,
    )

    outcome: FlashcardReviewOutcome


class FlashcardReviewResponse(
    BaseModel,
):
    """Persisted Flashcard review event returned to the student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    deck_id: UUID

    card_position: int = Field(
        ge=0,
    )

    outcome: FlashcardReviewOutcome

    reviewed_at: datetime