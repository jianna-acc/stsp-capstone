# File: /backend/tests/test_academic_task_service.py
# Purpose: Verifies academic-task service CRUD coordination,
# ownership propagation, status changes, and not-found handling.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.schemas.academic_task import (
    AcademicTaskCreateRequest,
    AcademicTaskResponse,
    AcademicTaskStatus,
    AcademicTaskUpdateRequest,
)
from app.services.academic_task_errors import (
    AcademicTaskNotFoundError,
)
from app.services.academic_task_service import (
    AcademicTaskService,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

TASK_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

DEADLINE = datetime(
    2026,
    8,
    20,
    12,
    0,
    tzinfo=UTC,
)

CREATED_AT = datetime(
    2026,
    8,
    9,
    12,
    0,
    tzinfo=UTC,
)

UPDATED_AT = datetime(
    2026,
    8,
    9,
    13,
    0,
    tzinfo=UTC,
)


def _task_response(
    *,
    status: AcademicTaskStatus = AcademicTaskStatus.PENDING,
) -> AcademicTaskResponse:
    """Return one valid academic-task response."""

    return AcademicTaskResponse(
        id=TASK_ID,
        subject_id=SUBJECT_ID,
        title="Research assignment",
        description="Complete the first draft.",
        deadline=DEADLINE,
        estimated_minutes=120,
        difficulty="medium",
        task_type="assignment",
        status=status,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
    )


def _create_request() -> AcademicTaskCreateRequest:
    """Return one valid academic-task creation request."""

    return AcademicTaskCreateRequest(
        subject_id=SUBJECT_ID,
        title="Research assignment",
        description="Complete the first draft.",
        deadline=DEADLINE,
        estimated_minutes=120,
        difficulty="medium",
        task_type="assignment",
    )


class FakeAcademicTaskRepository:
    """Minimal repository double used by service tests."""

    def __init__(self) -> None:
        self.created_task = _task_response()

        self.listed_tasks: list[
            AcademicTaskResponse
        ] = [
            _task_response(),
        ]

        self.loaded_task: AcademicTaskResponse | None = (
            _task_response()
        )

        self.updated_task: AcademicTaskResponse | None = (
            _task_response(
                status=AcademicTaskStatus.IN_PROGRESS,
            )
        )

        self.delete_result = True

        self.create_call: tuple[
            UUID,
            AcademicTaskCreateRequest,
        ] | None = None

        self.list_call: tuple[
            UUID,
            int,
        ] | None = None

        self.get_call: tuple[
            UUID,
            UUID,
        ] | None = None

        self.update_call: tuple[
            UUID,
            UUID,
            AcademicTaskUpdateRequest,
        ] | None = None

        self.delete_call: tuple[
            UUID,
            UUID,
        ] | None = None

    def create_academic_task(
        self,
        *,
        user_id: UUID,
        request: AcademicTaskCreateRequest,
    ) -> AcademicTaskResponse:
        """Record and return a task creation."""

        self.create_call = (
            user_id,
            request,
        )

        return self.created_task

    def list_academic_tasks(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
    ) -> list[AcademicTaskResponse]:
        """Record and return a task listing."""

        self.list_call = (
            user_id,
            limit,
        )

        return self.listed_tasks

    def get_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> AcademicTaskResponse | None:
        """Record and return one task lookup."""

        self.get_call = (
            user_id,
            task_id,
        )

        return self.loaded_task

    def update_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        request: AcademicTaskUpdateRequest,
    ) -> AcademicTaskResponse | None:
        """Record and return one task update."""

        self.update_call = (
            user_id,
            task_id,
            request,
        )

        return self.updated_task

    def delete_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> bool:
        """Record and return deletion result."""

        self.delete_call = (
            user_id,
            task_id,
        )

        return self.delete_result


def test_create_task_uses_authenticated_owner() -> None:
    """Create must forward authenticated owner to repository."""

    repository = FakeAcademicTaskRepository()

    service = AcademicTaskService(
        repository,
    )

    request = _create_request()

    result = service.create_task(
        user_id=USER_ID,
        request=request,
    )

    assert result == repository.created_task

    assert repository.create_call == (
        USER_ID,
        request,
    )


def test_list_tasks_uses_owner_and_limit() -> None:
    """Listing must forward owner and requested limit."""

    repository = FakeAcademicTaskRepository()

    service = AcademicTaskService(
        repository,
    )

    result = service.list_tasks(
        user_id=USER_ID,
        limit=25,
    )

    assert result == repository.listed_tasks

    assert repository.list_call == (
        USER_ID,
        25,
    )


def test_get_task_returns_owned_task() -> None:
    """Existing task should be returned."""

    repository = FakeAcademicTaskRepository()

    service = AcademicTaskService(
        repository,
    )

    result = service.get_task(
        user_id=USER_ID,
        task_id=TASK_ID,
    )

    assert result == repository.loaded_task

    assert repository.get_call == (
        USER_ID,
        TASK_ID,
    )


def test_get_missing_task_raises_not_found() -> None:
    """Missing task should become a controlled service error."""

    repository = FakeAcademicTaskRepository()
    repository.loaded_task = None

    service = AcademicTaskService(
        repository,
    )

    with pytest.raises(
        AcademicTaskNotFoundError,
        match="requested academic task was not found",
    ):
        service.get_task(
            user_id=USER_ID,
            task_id=TASK_ID,
        )


def test_update_task_uses_owner_and_task_id() -> None:
    """Update must remain scoped to owner and task ID."""

    repository = FakeAcademicTaskRepository()

    service = AcademicTaskService(
        repository,
    )

    request = AcademicTaskUpdateRequest(
        title="Revised research assignment",
    )

    result = service.update_task(
        user_id=USER_ID,
        task_id=TASK_ID,
        request=request,
    )

    assert result == repository.updated_task

    assert repository.update_call == (
        USER_ID,
        TASK_ID,
        request,
    )


def test_update_missing_task_raises_not_found() -> None:
    """Missing update target should raise not found."""

    repository = FakeAcademicTaskRepository()
    repository.updated_task = None

    service = AcademicTaskService(
        repository,
    )

    with pytest.raises(
        AcademicTaskNotFoundError,
        match="requested academic task was not found",
    ):
        service.update_task(
            user_id=USER_ID,
            task_id=TASK_ID,
            request=AcademicTaskUpdateRequest(
                status="completed",
            ),
        )


def test_change_task_status_uses_partial_update() -> None:
    """Status changes should create a status-only update."""

    repository = FakeAcademicTaskRepository()

    repository.updated_task = _task_response(
        status=AcademicTaskStatus.COMPLETED,
    )

    service = AcademicTaskService(
        repository,
    )

    result = service.change_task_status(
        user_id=USER_ID,
        task_id=TASK_ID,
        status=AcademicTaskStatus.COMPLETED,
    )

    assert result.status is AcademicTaskStatus.COMPLETED

    assert repository.update_call is not None

    (
        called_user_id,
        called_task_id,
        called_request,
    ) = repository.update_call

    assert called_user_id == USER_ID
    assert called_task_id == TASK_ID

    assert called_request.status is AcademicTaskStatus.COMPLETED

    assert called_request.model_fields_set == {
        "status",
    }


def test_delete_task_uses_owner_and_task_id() -> None:
    """Delete must remain scoped to owner and task ID."""

    repository = FakeAcademicTaskRepository()

    service = AcademicTaskService(
        repository,
    )

    result = service.delete_task(
        user_id=USER_ID,
        task_id=TASK_ID,
    )

    assert result is None

    assert repository.delete_call == (
        USER_ID,
        TASK_ID,
    )


def test_delete_missing_task_raises_not_found() -> None:
    """Deleting a missing task should raise not found."""

    repository = FakeAcademicTaskRepository()
    repository.delete_result = False

    service = AcademicTaskService(
        repository,
    )

    with pytest.raises(
        AcademicTaskNotFoundError,
        match="requested academic task was not found",
    ):
        service.delete_task(
            user_id=USER_ID,
            task_id=TASK_ID,
        )