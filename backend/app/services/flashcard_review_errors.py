# File: /backend/app/services/flashcard_review_errors.py
# Purpose: Defines controlled failures for Flashcard review persistence.

from app.services.flashcard_errors import (
    FlashcardError,
)


class FlashcardReviewError(
    FlashcardError,
):
    """Base controlled error for Flashcard review operations."""


class FlashcardReviewValidationError(
    FlashcardReviewError,
):
    """Raised when a Flashcard review request is invalid."""


class FlashcardReviewNotFoundError(
    FlashcardReviewError,
):
    """Raised when the owned Flashcard review target is unavailable."""


class FlashcardReviewPersistenceError(
    FlashcardReviewError,
):
    """Raised when Flashcard review storage cannot be accessed."""


class FlashcardReviewResponseError(
    FlashcardReviewError,
):
    """Raised when persisted Flashcard review data is malformed."""