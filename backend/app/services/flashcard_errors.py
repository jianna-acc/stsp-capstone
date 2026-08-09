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

class FlashcardSourceNotFoundError(
    FlashcardError,
):
    """Raised when owned Flashcard source material is unavailable."""


class FlashcardSourceUnavailableError(
    FlashcardError,
):
    """Raised when Flashcard source material cannot be safely used."""

class FlashcardGenerationError(
    FlashcardError,
):
    """Raised when Flashcard AI generation cannot complete."""


class FlashcardGenerationResponseError(
    FlashcardGenerationError,
):
    """Raised when AI output cannot become valid Flashcards."""