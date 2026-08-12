# File: /backend/app/services/study_activity_errors.py
# Purpose: Defines controlled failures for actual study-activity
# timer operations.


class StudyActivityError(Exception):
    """Base controlled Study Activity failure."""


class StudyActivityValidationError(
    StudyActivityError,
):
    """Study Activity request or target is invalid."""


class StudyActivityNotFoundError(
    StudyActivityError,
):
    """Requested Study Activity resource does not exist or is not owned."""


class StudyActivityConflictError(
    StudyActivityError,
):
    """Timer state conflicts with the requested operation."""


class StudyActivityPersistenceError(
    StudyActivityError,
):
    """Study Activity storage is temporarily unavailable."""


class StudyActivityResponseError(
    StudyActivityError,
):
    """Stored Study Activity data could not be safely parsed."""