# File: /backend/app/services/academic_task_service.py
# Purpose: Coordinates authenticated academic-task CRUD operations
# between the API layer and academic-task repository.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.academic_task import (
    AcademicTaskCreateRequest,
    AcademicTaskResponse,
    AcademicTaskStatus,
    AcademicTaskUpdateRequest,
)
from app.services.academic_task_errors import (
    AcademicTaskNotFoundError,
)


class AcademicTaskRepositoryProtocol(
    Protocol,
):
    """Persistence operations required by the task service."""

    def create_academic_task(
        self,
        *,
        user_id: UUID,
        request: AcademicTaskCreateRequest,
    ) -> AcademicTaskResponse: ...

    def list_academic_tasks(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
    ) -> list[AcademicTaskResponse]: ...

    def get_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> AcademicTaskResponse | None: ...

    def update_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        request: AcademicTaskUpdateRequest,
    ) -> AcademicTaskResponse | None: ...

    def delete_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> bool: ...


class AcademicTaskService:
    """Coordinates student-owned academic-task operations."""

    def __init__(
        self,
        repository: AcademicTaskRepositoryProtocol,
    ) -> None:
        self._repository = repository

    def create_task(
        self,
        *,
        user_id: UUID,
        request: AcademicTaskCreateRequest,
    ) -> AcademicTaskResponse:
        """Create one academic task for the authenticated student."""

        return self._repository.create_academic_task(
            user_id=user_id,
            request=request,
        )

    def list_tasks(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
    ) -> list[AcademicTaskResponse]:
        """Return academic tasks owned by the student."""

        return self._repository.list_academic_tasks(
            user_id=user_id,
            limit=limit,
        )

    def get_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> AcademicTaskResponse:
        """Return one owned academic task or raise not found."""

        task = self._repository.get_academic_task(
            user_id=user_id,
            task_id=task_id,
        )

        if task is None:
            raise AcademicTaskNotFoundError(
                "The requested academic task was not found.",
            )

        return task

    def update_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        request: AcademicTaskUpdateRequest,
    ) -> AcademicTaskResponse:
        """Update one owned academic task."""

        task = self._repository.update_academic_task(
            user_id=user_id,
            task_id=task_id,
            request=request,
        )

        if task is None:
            raise AcademicTaskNotFoundError(
                "The requested academic task was not found.",
            )

        return task

    def change_task_status(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        status: AcademicTaskStatus,
    ) -> AcademicTaskResponse:
        """Change only the workflow status of one owned task."""

        request = AcademicTaskUpdateRequest(
            status=status,
        )

        return self.update_task(
            user_id=user_id,
            task_id=task_id,
            request=request,
        )

    def delete_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> None:
        """Delete one owned academic task."""

        deleted = self._repository.delete_academic_task(
            user_id=user_id,
            task_id=task_id,
        )

        if not deleted:
            raise AcademicTaskNotFoundError(
                "The requested academic task was not found.",
            )