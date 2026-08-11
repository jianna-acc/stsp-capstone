# File: /backend/tests/test_study_plan_api_endpoint.py
# Purpose: Verifies authenticated Track D API behavior without
# registering the router in the shared application router.

from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import (
    UUID,
    uuid4,
)

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.routes import study_plans
from app.api.study_plan_dependency import (
    get_study_plan_service,
)
from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanGenerationMode,
    StudyPlanListResponse,
    StudyPlanResponse,
    StudyPlanStatus,
    StudySessionCreateRequest,
    StudySessionListResponse,
    StudySessionOrigin,
    StudySessionResponse,
    StudySessionStatus,
)
from app.services.study_plan_errors import (
    StudyPlanError,
    StudyPlanNotFoundError,
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
    StudySessionNotFoundError,
)

USER_ID = uuid4()
PLAN_ID = uuid4()
SESSION_ID = uuid4()
SUBJECT_ID = uuid4()

NOW = datetime(
    2026,
    8,
    10,
    8,
    0,
    tzinfo=timezone.utc,
)


def _plan() -> StudyPlanResponse:
    """Return one valid persisted study plan."""

    return StudyPlanResponse(
        id=PLAN_ID,
        title="Finals Review",
        starts_on=date(
            2026,
            8,
            10,
        ),
        ends_on=date(
            2026,
            8,
            17,
        ),
        status=StudyPlanStatus.ACTIVE,
        generation_mode=(
            StudyPlanGenerationMode.MANUAL
        ),
        generated_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _session() -> StudySessionResponse:
    """Return one valid persisted study session."""

    return StudySessionResponse(
        id=SESSION_ID,
        study_plan_id=PLAN_ID,
        subject_id=SUBJECT_ID,
        title="Review Chapter 4",
        starts_at=NOW,
        ends_at=(
            NOW
            + timedelta(
                hours=1,
            )
        ),
        status=StudySessionStatus.PLANNED,
        origin=StudySessionOrigin.MANUAL,
        notes=None,
        created_at=NOW,
        updated_at=NOW,
    )


class FakeStudyPlanService:
    """Deterministic service double for isolated API tests."""

    def __init__(
        self,
    ) -> None:
        self.error: StudyPlanError | None = None

        self.calls: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def _raise_if_needed(
        self,
    ) -> None:
        if self.error is not None:
            raise self.error

    def create_study_plan(
        self,
        *,
        user_id: UUID,
        request: StudyPlanCreateRequest,
    ) -> StudyPlanResponse:
        self._raise_if_needed()

        self.calls.append(
            (
                "create_study_plan",
                user_id,
                request,
            )
        )

        return _plan()

    def list_study_plans(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> StudyPlanListResponse:
        self._raise_if_needed()

        self.calls.append(
            (
                "list_study_plans",
                user_id,
                limit,
            )
        )

        return StudyPlanListResponse(
            items=(
                _plan(),
            ),
        )

    def get_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> StudyPlanResponse:
        self._raise_if_needed()

        self.calls.append(
            (
                "get_study_plan",
                user_id,
                study_plan_id,
            )
        )

        return _plan()

    def delete_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> None:
        self._raise_if_needed()

        self.calls.append(
            (
                "delete_study_plan",
                user_id,
                study_plan_id,
            )
        )

    def create_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request: StudySessionCreateRequest,
    ) -> StudySessionResponse:
        self._raise_if_needed()

        self.calls.append(
            (
                "create_study_session",
                user_id,
                study_plan_id,
                request,
            )
        )

        return _session()

    def list_study_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        limit: int = 200,
    ) -> StudySessionListResponse:
        self._raise_if_needed()

        self.calls.append(
            (
                "list_study_sessions",
                user_id,
                study_plan_id,
                limit,
            )
        )

        return StudySessionListResponse(
            items=(
                _session(),
            ),
        )

    def delete_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        study_session_id: UUID,
    ) -> None:
        self._raise_if_needed()

        self.calls.append(
            (
                "delete_study_session",
                user_id,
                study_plan_id,
                study_session_id,
            )
        )


def _create_test_client(
    service: FakeStudyPlanService,
) -> TestClient:
    """Create an isolated FastAPI app containing only Track D."""

    application = FastAPI()

    application.include_router(
        study_plans.router,
        prefix="/api",
    )

    async def override_authenticated_user(
    ) -> AuthenticatedUser:
        return AuthenticatedUser(
            user_id=USER_ID,
        )

    def override_study_plan_service(
    ) -> FakeStudyPlanService:
        return service

    application.dependency_overrides[
        require_authenticated_user
    ] = override_authenticated_user

    application.dependency_overrides[
        get_study_plan_service
    ] = override_study_plan_service

    return TestClient(
        application,
    )


def test_create_study_plan_uses_authenticated_owner() -> None:
    """Plan creation must use the authenticated student."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/study-plans",
            json={
                "title": "Finals Review",
                "starts_on": "2026-08-10",
                "ends_on": "2026-08-17",
            },
        )

    assert response.status_code == 201

    assert (
        service.calls[0][0]
        == "create_study_plan"
    )

    assert (
        service.calls[0][1]
        == USER_ID
    )


def test_list_study_plans_returns_owned_items() -> None:
    """Students should receive their service-provided plans."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            "/api/study-plans",
        )

    assert response.status_code == 200

    body = response.json()

    assert len(
        body[
            "items"
        ]
    ) == 1

    assert (
        body[
            "items"
        ][0]["id"]
        == str(
            PLAN_ID,
        )
    )


def test_get_study_plan_returns_owned_plan() -> None:
    """An owned plan should be returned by identifier."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            f"/api/study-plans/{PLAN_ID}",
        )

    assert response.status_code == 200

    assert (
        response.json()[
            "id"
        ]
        == str(
            PLAN_ID,
        )
    )


def test_delete_study_plan_returns_no_content() -> None:
    """Successful plan deletion should return HTTP 204."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.delete(
            f"/api/study-plans/{PLAN_ID}",
        )

    assert response.status_code == 204
    assert response.content == b""


def test_create_study_session_uses_plan_and_owner() -> None:
    """Manual session creation must preserve owner and plan."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.post(
            (
                f"/api/study-plans/"
                f"{PLAN_ID}/sessions"
            ),
            json={
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "title": "Review Chapter 4",
                "starts_at": (
                    "2026-08-10T08:00:00+00:00"
                ),
                "ends_at": (
                    "2026-08-10T09:00:00+00:00"
                ),
            },
        )

    assert response.status_code == 201

    assert (
        service.calls[0][0]
        == "create_study_session"
    )

    assert service.calls[0][1] == USER_ID
    assert service.calls[0][2] == PLAN_ID


def test_list_study_sessions_returns_items() -> None:
    """Students should receive sessions from their plan."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            (
                f"/api/study-plans/"
                f"{PLAN_ID}/sessions"
            ),
        )

    assert response.status_code == 200

    assert len(
        response.json()[
            "items"
        ]
    ) == 1


def test_delete_study_session_returns_no_content() -> None:
    """Successful session deletion should return HTTP 204."""

    service = FakeStudyPlanService()

    with _create_test_client(
        service,
    ) as client:
        response = client.delete(
            (
                f"/api/study-plans/"
                f"{PLAN_ID}/sessions/"
                f"{SESSION_ID}"
            ),
        )

    assert response.status_code == 204
    assert response.content == b""


def test_validation_error_is_safe() -> None:
    """Controlled validation errors should return HTTP 400."""

    service = FakeStudyPlanService()

    service.error = StudyPlanValidationError(
        "internal validation detail",
    )

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            "/api/study-plans",
        )

    assert response.status_code == 400

    assert response.json() == {
        "error_code": (
            "STUDY_PLAN_VALIDATION_FAILED"
        ),
        "message": (
            "The study-plan operation is invalid."
        ),
    }


def test_missing_plan_error_is_safe() -> None:
    """Missing study plans should return HTTP 404."""

    service = FakeStudyPlanService()

    service.error = StudyPlanNotFoundError(
        "internal plan detail",
    )

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            f"/api/study-plans/{PLAN_ID}",
        )

    assert response.status_code == 404

    assert (
        response.json()[
            "error_code"
        ]
        == "STUDY_PLAN_NOT_FOUND"
    )


def test_missing_session_error_is_safe() -> None:
    """Missing study sessions should return HTTP 404."""

    service = FakeStudyPlanService()

    service.error = StudySessionNotFoundError(
        "internal session detail",
    )

    with _create_test_client(
        service,
    ) as client:
        response = client.delete(
            (
                f"/api/study-plans/"
                f"{PLAN_ID}/sessions/"
                f"{SESSION_ID}"
            ),
        )

    assert response.status_code == 404

    assert (
        response.json()[
            "error_code"
        ]
        == "STUDY_SESSION_NOT_FOUND"
    )


def test_persistence_error_is_safe() -> None:
    """Storage failures should return HTTP 503."""

    service = FakeStudyPlanService()

    service.error = StudyPlanPersistenceError(
        "internal storage detail",
    )

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            "/api/study-plans",
        )

    assert response.status_code == 503

    assert (
        response.json()[
            "error_code"
        ]
        == "STUDY_PLAN_PERSISTENCE_FAILED"
    )


def test_response_error_is_safe() -> None:
    """Invalid stored responses should return HTTP 500."""

    service = FakeStudyPlanService()

    service.error = StudyPlanResponseError(
        "internal response detail",
    )

    with _create_test_client(
        service,
    ) as client:
        response = client.get(
            "/api/study-plans",
        )

    assert response.status_code == 500

    assert (
        response.json()[
            "error_code"
        ]
        == "STUDY_PLAN_RESPONSE_FAILED"
    )