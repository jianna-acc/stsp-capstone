# File: /backend/app/services/flashcard_errors.py
# Purpose: Defines controlled domain errors for Flashcard
# validation, persistence, and response processing.


class FlashcardError(Exception):
    """Base error for controlled Flashcard failures."""


class FlashcardValidationError(
    FlashcardError,
):
    """Raised when a Flashcard operation is invalid."""


class FlashcardPersistenceError(
    FlashcardError,
):
    """Raised when Flashcard database access fails."""


class FlashcardResponseError(
    FlashcardError,
):
    """Raised when persisted Flashcard data is malformed."""