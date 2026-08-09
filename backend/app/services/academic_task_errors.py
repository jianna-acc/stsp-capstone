# File: /backend/app/services/academic_task_errors.py
# Purpose: Defines controlled errors used by the academic-task
# repository, service, and API layers.


class AcademicTaskError(Exception):
    """Base error for academic-task operations."""


class AcademicTaskValidationError(
    AcademicTaskError,
):
    """Raised when an academic-task operation is invalid."""


class AcademicTaskPersistenceError(
    AcademicTaskError,
):
    """Raised when academic-task persistence fails."""


class AcademicTaskResponseError(
    AcademicTaskError,
):
    """Raised when stored academic-task data is invalid."""


class AcademicTaskNotFoundError(
    AcademicTaskError,
):
    """Raised when an owned academic task does not exist."""