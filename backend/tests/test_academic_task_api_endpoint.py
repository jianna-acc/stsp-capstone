# File: /backend/tests/test_academic_task_api_endpoint.py
# Purpose: Tests authenticated academic-task API endpoints without
# requiring live Supabase services.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.academic_task_dependency import (
    get_academic_task_service,
)
from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.routes.academic_tasks import (
    router as academic_task_router,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.schemas.academic_task import (
    AcademicTaskCreateRequest,
    AcademicTaskResponse,
    AcademicTaskStatus,
    AcademicTaskUpdateRequest,
)
from app.services.academic_task_errors import (
    AcademicTaskNotFoundError,
    AcademicTaskPersistenceError,
    AcademicTaskResponseError,
    AcademicTaskValidationError,
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


def make_task(
    *,
    title: str = "Research assignment",
    status: AcademicTaskStatus = AcademicTaskStatus.PENDING,
) -> AcademicTaskResponse:
    """Return one safe academic-task API response."""

    now = datetime.now(
        UTC,
    )

    return AcademicTaskResponse(
        id=TASK_ID,
        subject_id=SUBJECT_ID,
        title=title,
        description="Complete the first draft.",
        deadline=DEADLINE,
        estimated_minutes=120,
        difficulty="medium",
        task_type="assignment",
        status=status,
        created_at=now,
        updated_at=now,
    )


class FakeAcademicTaskService:
    """Record synchronous academic-task API operations."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error

        self.calls: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def _raise_error(
        self,
    ) -> None:
        """Raise the configured controlled service error."""

        if self.error is not None:
            raise self.error

    def create_task(
        self,
        *,
        user_id: UUID,
        request: AcademicTaskCreateRequest,
    ) -> AcademicTaskResponse:
        """Record task creation."""

        self.calls.append(
            (
                "create",
                user_id,
                request,
            )
        )

        self._raise_error()

        return make_task()

    def list_tasks(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
    ) -> list[AcademicTaskResponse]:
        """Record task listing."""

        self.calls.append(
            (
                "list",
                user_id,
                limit,
            )
        )

        self._raise_error()

        return [
            make_task(),
        ]

    def get_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> AcademicTaskResponse:
        """Record one task lookup."""

        self.calls.append(
            (
                "get",
                user_id,
                task_id,
            )
        )

        self._raise_error()

        return make_task()

    def update_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        request: AcademicTaskUpdateRequest,
    ) -> AcademicTaskResponse:
        """Record one general task update."""

        self.calls.append(
            (
                "update",
                user_id,
                task_id,
                request,
            )
        )

        self._raise_error()

        updates: dict[
            str,
            object,
        ] = {}

        if request.title is not None:
            updates[
                "title"
            ] = request.title

        if request.status is not None:
            updates[
                "status"
            ] = request.status

        return make_task().model_copy(
            update=updates,
        )

    def change_task_status(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        status: AcademicTaskStatus,
    ) -> AcademicTaskResponse:
        """Record a status-only task update."""

        self.calls.append(
            (
                "status",
                user_id,
                task_id,
                status,
            )
        )

        self._raise_error()

        return make_task(
            status=status,
        )

    def delete_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> None:
        """Record one task deletion."""

        self.calls.append(
            (
                "delete",
                user_id,
                task_id,
            )
        )

        self._raise_error()


class UnusedFakeSupabaseClient:
    """Placeholder when real Supabase authentication is unused."""

    auth = object()


def create_test_client(
    *,
    service: FakeAcademicTaskService | None = None,
    authenticated: bool = True,
) -> TestClient:
    """Create an isolated academic-task API application."""

    app = FastAPI()

    app.include_router(
        academic_task_router,
        prefix="/api",
    )

    task_service = (
        service
        if service is not None
        else FakeAcademicTaskService()
    )

    app.dependency_overrides[
        get_academic_task_service
    ] = lambda: task_service

    app.dependency_overrides[
        get_supabase_client
    ] = lambda: UnusedFakeSupabaseClient()

    if authenticated:
        app.dependency_overrides[
            require_authenticated_user
        ] = lambda: AuthenticatedUser(
            user_id=USER_ID,
        )

    return TestClient(
        app,
    )


def valid_create_payload() -> dict[
    str,
    object,
]:
    """Return one valid task-creation JSON payload."""

    return {
        "subject_id": str(
            SUBJECT_ID,
        ),
        "title": "Research assignment",
        "description": "Complete the first draft.",
        "deadline": DEADLINE.isoformat(),
        "estimated_minutes": 120,
        "difficulty": "medium",
        "task_type": "assignment",
    }


def test_create_task_uses_authenticated_owner() -> None:
    """Creation must use authenticated ownership."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            "/api/academic-tasks",
            json=valid_create_payload(),
        )

    assert response.status_code == 201

    body = response.json()

    assert body[
        "id"
    ] == str(
        TASK_ID,
    )

    assert body[
        "subject_id"
    ] == str(
        SUBJECT_ID,
    )

    assert body[
        "title"
    ] == "Research assignment"

    assert body[
        "status"
    ] == "pending"

    assert "user_id" not in body

    assert len(
        service.calls,
    ) == 1

    call = service.calls[
        0
    ]

    assert call[
        0
    ] == "create"

    assert call[
        1
    ] == USER_ID

    request = call[
        2
    ]

    assert isinstance(
        request,
        AcademicTaskCreateRequest,
    )

    assert request.subject_id == SUBJECT_ID
    assert request.title == "Research assignment"
    assert request.estimated_minutes == 120


def test_create_task_rejects_client_user_id() -> None:
    """Clients must not control academic-task ownership."""

    service = FakeAcademicTaskService()

    payload = valid_create_payload()

    payload[
        "user_id"
    ] = str(
        UUID(
            "44444444-4444-4444-8444-444444444444"
        )
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            "/api/academic-tasks",
            json=payload,
        )

    assert response.status_code == 422
    assert service.calls == []


def test_create_task_rejects_invalid_payload() -> None:
    """Invalid task creation input must fail validation."""

    service = FakeAcademicTaskService()

    payload = valid_create_payload()
    payload[
        "estimated_minutes"
    ] = 0

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            "/api/academic-tasks",
            json=payload,
        )

    assert response.status_code == 422
    assert service.calls == []


def test_list_tasks_uses_authenticated_owner_and_default_limit() -> None:
    """Default task list must use authenticated ownership."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks",
        )

    assert response.status_code == 200

    body = response.json()

    assert len(
        body[
            "items"
        ],
    ) == 1

    assert body[
        "items"
    ][
        0
    ][
        "id"
    ] == str(
        TASK_ID,
    )

    assert service.calls == [
        (
            "list",
            USER_ID,
            100,
        )
    ]


def test_list_tasks_accepts_custom_limit() -> None:
    """Task list endpoint should forward a valid limit."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks?limit=25",
        )

    assert response.status_code == 200

    assert service.calls == [
        (
            "list",
            USER_ID,
            25,
        )
    ]


def test_invalid_list_limit_returns_422() -> None:
    """FastAPI must enforce task list bounds."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks?limit=101",
        )

    assert response.status_code == 422
    assert service.calls == []


def test_get_task_uses_authenticated_owner() -> None:
    """Single-task retrieval must remain ownership scoped."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            f"/api/academic-tasks/{TASK_ID}",
        )

    assert response.status_code == 200

    assert response.json()[
        "id"
    ] == str(
        TASK_ID,
    )

    assert service.calls == [
        (
            "get",
            USER_ID,
            TASK_ID,
        )
    ]


def test_invalid_task_uuid_returns_422() -> None:
    """Malformed task IDs must fail before service execution."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks/not-a-uuid",
        )

    assert response.status_code == 422
    assert service.calls == []


def test_update_task_uses_authenticated_owner() -> None:
    """Task updates must use authenticated ownership."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.patch(
            f"/api/academic-tasks/{TASK_ID}",
            json={
                "title": "Revised assignment",
                "status": "in_progress",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "title"
    ] == "Revised assignment"

    assert body[
        "status"
    ] == "in_progress"

    assert len(
        service.calls,
    ) == 1

    call = service.calls[
        0
    ]

    assert call[
        0
    ] == "update"

    assert call[
        1
    ] == USER_ID

    assert call[
        2
    ] == TASK_ID

    request = call[
        3
    ]

    assert isinstance(
        request,
        AcademicTaskUpdateRequest,
    )

    assert request.title == "Revised assignment"

    assert (
        request.status
        is AcademicTaskStatus.IN_PROGRESS
    )


def test_update_task_rejects_empty_payload() -> None:
    """Empty partial updates must fail validation."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.patch(
            f"/api/academic-tasks/{TASK_ID}",
            json={},
        )

    assert response.status_code == 422
    assert service.calls == []


def test_status_change_uses_authenticated_owner() -> None:
    """Dedicated status changes must use authenticated ownership."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.patch(
            (
                f"/api/academic-tasks/"
                f"{TASK_ID}/status"
            ),
            json={
                "status": "completed",
            },
        )

    assert response.status_code == 200

    assert response.json()[
        "status"
    ] == "completed"

    assert service.calls == [
        (
            "status",
            USER_ID,
            TASK_ID,
            AcademicTaskStatus.COMPLETED,
        )
    ]


def test_status_change_rejects_invalid_status() -> None:
    """Unknown task statuses must fail request validation."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.patch(
            (
                f"/api/academic-tasks/"
                f"{TASK_ID}/status"
            ),
            json={
                "status": "almost-done",
            },
        )

    assert response.status_code == 422
    assert service.calls == []


def test_status_change_rejects_extra_fields() -> None:
    """Status endpoint should accept only the status field."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.patch(
            (
                f"/api/academic-tasks/"
                f"{TASK_ID}/status"
            ),
            json={
                "status": "completed",
                "user_id": str(
                    USER_ID,
                ),
            },
        )

    assert response.status_code == 422
    assert service.calls == []


def test_delete_task_returns_no_content() -> None:
    """Successful deletion must return HTTP 204."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.delete(
            f"/api/academic-tasks/{TASK_ID}",
        )

    assert response.status_code == 204
    assert response.content == b""

    assert service.calls == [
        (
            "delete",
            USER_ID,
            TASK_ID,
        )
    ]


def test_missing_task_returns_404() -> None:
    """Owned lookup failures must return a safe 404."""

    service = FakeAcademicTaskService(
        error=AcademicTaskNotFoundError(
            "internal missing-task detail",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            f"/api/academic-tasks/{TASK_ID}",
        )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "ACADEMIC_TASK_NOT_FOUND",
        "message": (
            "The requested academic task was not found."
        ),
    }

    assert (
        "internal missing-task detail"
        not in response.text
    )


def test_validation_failure_returns_400() -> None:
    """Controlled domain validation errors must return 400."""

    service = FakeAcademicTaskService(
        error=AcademicTaskValidationError(
            "internal validation detail",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks",
        )

    assert response.status_code == 400

    assert response.json()[
        "error_code"
    ] == "ACADEMIC_TASK_VALIDATION_FAILED"

    assert (
        "internal validation detail"
        not in response.text
    )


def test_persistence_failure_returns_503() -> None:
    """Academic-task storage failures must return 503."""

    service = FakeAcademicTaskService(
        error=AcademicTaskPersistenceError(
            "database unavailable",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks",
        )

    assert response.status_code == 503

    assert response.json() == {
        "error_code": "ACADEMIC_TASK_PERSISTENCE_FAILED",
        "message": (
            "Academic-task storage is temporarily unavailable."
        ),
    }

    assert "database unavailable" not in response.text


def test_invalid_stored_response_returns_500() -> None:
    """Invalid stored task data must return a safe server error."""

    service = FakeAcademicTaskService(
        error=AcademicTaskResponseError(
            "malformed database row",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/academic-tasks",
        )

    assert response.status_code == 500

    assert response.json() == {
        "error_code": "ACADEMIC_TASK_RESPONSE_FAILED",
        "message": (
            "Stored academic-task data could not be processed."
        ),
    }

    assert "malformed database row" not in response.text


def test_missing_authentication_returns_401() -> None:
    """Academic-task endpoints must require authentication."""

    service = FakeAcademicTaskService()

    with create_test_client(
        service=service,
        authenticated=False,
    ) as client:
        response = client.get(
            "/api/academic-tasks",
        )

    assert response.status_code == 401
    assert service.calls == []