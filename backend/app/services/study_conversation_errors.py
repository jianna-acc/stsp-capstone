# File: /backend/app/services/study_conversation_errors.py
# Purpose: Defines controlled domain errors for saved Study
# Assistant conversations and messages.


class StudyConversationError(
    Exception,
):
    """Base error for Study Conversation operations."""


class StudyConversationValidationError(
    StudyConversationError,
):
    """Raised when conversation input or filters are invalid."""


class StudyConversationNotFoundError(
    StudyConversationError,
):
    """Raised when an owned conversation cannot be found."""


class StudyConversationPersistenceError(
    StudyConversationError,
):
    """Raised when conversation data cannot be persisted."""


class StudyConversationResponseError(
    StudyConversationError,
):
    """Raised when persisted conversation data is malformed."""