# File: /backend/app/services/reviewer_errors.py
# Purpose: Defines controlled reviewer validation,
# persistence, source-loading, response, and not-found failures.


class ReviewerError(RuntimeError):
    """Base error for reviewer operations."""


class ReviewerValidationError(ReviewerError):
    """Raised when a reviewer request is invalid."""


class ReviewerPersistenceError(ReviewerError):
    """Raised when reviewer database access fails."""


class ReviewerResponseError(ReviewerError):
    """Raised when persisted reviewer data is invalid."""


class ReviewerNotFoundError(ReviewerError):
    """Raised when an owned reviewer cannot be found."""


class ReviewerSourceError(ReviewerError):
    """Base error for reviewer source-material loading."""


class ReviewerSourceNotFoundError(
    ReviewerSourceError,
):
    """Raised when no eligible source material exists."""


class ReviewerSourceUnavailableError(
    ReviewerSourceError,
):
    """Raised when reviewer source data is unavailable or invalid."""

class ReviewerGenerationError(ReviewerError):
    """Raised when the AI provider cannot generate a reviewer."""


class ReviewerGenerationResponseError(
    ReviewerGenerationError,
):
    """Raised when generated reviewer content is invalid."""