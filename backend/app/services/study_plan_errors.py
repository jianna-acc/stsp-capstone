# File: /backend/app/services/study_plan_errors.py
# Purpose: Defines controlled failures for study-plan persistence
# and scheduling operations.


class StudyPlanError(Exception):
    """Base class for controlled study-plan failures."""


class StudyPlanValidationError(StudyPlanError):
    """Raised when a study-plan operation is invalid."""


class StudyPlanNotFoundError(StudyPlanError):
    """Raised when an owned study plan cannot be found."""


class StudySessionNotFoundError(StudyPlanError):
    """Raised when an owned study session cannot be found."""


class StudyPlanPersistenceError(StudyPlanError):
    """Raised when study-plan storage is unavailable."""


class StudyPlanResponseError(StudyPlanError):
    """Raised when stored study-plan data is invalid."""