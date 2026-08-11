# File: /backend/app/services/quiz_attempt_errors.py

# Purpose: Defines controlled Quiz-attempt persistence,
# response, validation, not-found, and state-conflict errors.


class QuizAttemptError(RuntimeError):
    """Base class for controlled Quiz-attempt failures."""


class QuizAttemptValidationError(QuizAttemptError):
    """Raised when a Quiz-attempt operation is invalid."""


class QuizAttemptNotFoundError(QuizAttemptError):
    """Raised when an owned Quiz or attempt cannot be found."""


class QuizAttemptConflictError(QuizAttemptError):
    """Raised when attempt state prevents the requested operation."""


class QuizAttemptPersistenceError(QuizAttemptError):
    """Raised when Quiz-attempt persistence fails."""


class QuizAttemptResponseError(QuizAttemptError):
    """Raised when persisted Quiz-attempt data is invalid."""