# File: /backend/app/services/quiz_errors.py

# Purpose: Defines controlled Quiz-domain errors for validation,
# persistence, response parsing, generation, and orchestration.


class QuizError(RuntimeError):
    """Base error for controlled Quiz failures."""


class QuizValidationError(QuizError):
    """Raised when Quiz input is invalid."""


class QuizPersistenceError(QuizError):
    """Raised when Quiz persistence fails."""


class QuizResponseError(QuizError):
    """Raised when stored Quiz data cannot be parsed."""


class QuizNotFoundError(QuizError):
    """Raised when an owned Quiz cannot be found."""


class QuizSourceNotFoundError(QuizError):
    """Raised when Quiz source material cannot be found."""


class QuizSourceUnavailableError(QuizError):
    """Raised when Quiz source material is not ready."""


class QuizGenerationError(QuizError):
    """Raised when the AI provider cannot generate a Quiz."""


class QuizGenerationResponseError(QuizError):
    """Raised when generated Quiz content is unusable."""