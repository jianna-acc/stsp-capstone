# File: /backend/tests/test_study_plan_generation_api_endpoint.py
# Purpose: Verifies the Track D generate-and-save endpoint
# without registering it in the shared application router.

from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.routes import study_plan_generation
from app.api.study_plan_generation_dependency import (
    get_study_plan_generation_orchestrator,
)
from app.schemas.study_plan import (
    StudyPlanGenerationMode,
    StudyPlanResponse,
    StudyPlanStatus,
    StudySessionOrigin,
    StudySessionResponse,
    StudySessionStatus,
)
from app.schemas.study_plan_generation_api import (
    StudyPlanGenerationResponse,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
)

USER_ID = uuid4()
PLAN_ID = uuid4()
SESSION_ID = uuid4()
TASK_ID = uuid4()
SUBJECT_ID = uuid4()

NOW = datetime(
    2026,
    8,
    10,
    8,
    0,
    tzinfo=timezone.utc,
)

SESSION_START = datetime(
    2026,
    8,
    10,
    18,
    0,
    tzinfo=timezone(
        timedelta(
            hours=8,
        )
    ),
)

SESSION_END = SESSION_START + timedelta(
    minutes=60,
)


def _response() -> StudyPlanGenerationResponse:
    return StudyPlanGenerationResponse(
        plan=StudyPlanResponse(
            id=PLAN_ID,
            title="Finals Plan",
            starts_on=date(
                2026,
                8,
                10,
            ),
            ends_on=date(
                2026,
                8,
                10,
            ),
            status=StudyPlanStatus.ACTIVE,
            generation_mode=(
                StudyPlanGenerationMode.GENERATED
            ),
            generated_at=NOW,
            created_at=NOW,
            updated_at=NOW,
        ),
        sessions=(
            StudySessionResponse(
                id=SESSION_ID,
                study_plan_id=PLAN_ID,
                subject_id=SUBJECT_ID,
                title="Review Chapter 4",
                starts_at=SESSION_START,
                ends_at=SESSION_END,
                status=StudySessionStatus.PLANNED,
                origin=StudySessionOrigin.GENERATED,
                notes=None,
                created_at=NOW,
                updated_at=NOW,
            ),
        ),
        unscheduled_tasks=(),
    )


class FakeOrchestrator:
    def __init__(
        self,
    ) -> None:
        self.calls = []
        self.error = None

    def generate_and_save(
        self,
        *,
        user_id,
        title,
        starts_on,
        ends_on,
        tasks,
    ):
        if self.error is not None:
            raise self.error

        self.calls.append(
            (
                user_id,
                title,
                starts_on,
                ends_on,
                tasks,
            )
        )

        return _response()


def _client(
    orchestrator: FakeOrchestrator,
) -> TestClient:
    application = FastAPI()

    application.include_router(
        study_plan_generation.router,
        prefix="/api",
    )

    async def override_authenticated_user(
    ) -> AuthenticatedUser:
        return AuthenticatedUser(
            user_id=USER_ID,
        )

    def override_orchestrator(
    ) -> FakeOrchestrator:
        return orchestrator

    application.dependency_overrides[
        require_authenticated_user
    ] = override_authenticated_user

    application.dependency_overrides[
        get_study_plan_generation_orchestrator
    ] = override_orchestrator

    return TestClient(
        application,
    )


def _payload() -> dict[
    str,
    object,
]:
    return {
        "title": "Finals Plan",
        "starts_on": "2026-08-10",
        "ends_on": "2026-08-10",
        "tasks": [
            {
                "task_id": str(
                    TASK_ID,
                ),
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "title": "Review Chapter 4",
                "deadline": (
                    "2026-08-11T12:00:00+00:00"
                ),
                "estimated_minutes": 60,
                "priority_weight": 3,
            },
        ],
    }


def test_endpoint_uses_authenticated_owner() -> None:
    """Generation must use the authenticated student."""

    orchestrator = FakeOrchestrator()

    with _client(
        orchestrator,
    ) as client:
        response = client.post(
            "/api/study-plan-generation",
            json=_payload(),
        )

    assert response.status_code == 201

    assert orchestrator.calls[0][0] == USER_ID


def test_endpoint_returns_persisted_plan() -> None:
    """The saved generated plan should be returned."""

    orchestrator = FakeOrchestrator()

    with _client(
        orchestrator,
    ) as client:
        response = client.post(
            "/api/study-plan-generation",
            json=_payload(),
        )

    assert response.status_code == 201

    assert (
        response.json()[
            "plan"
        ][
            "id"
        ]
        == str(
            PLAN_ID,
        )
    )

    assert len(
        response.json()[
            "sessions"
        ]
    ) == 1


def test_generation_validation_error_is_safe() -> None:
    """Controlled generation failures should return HTTP 400."""

    orchestrator = FakeOrchestrator()

    orchestrator.error = (
        StudyPlanValidationError(
            "internal generation detail",
        )
    )

    with _client(
        orchestrator,
    ) as client:
        response = client.post(
            "/api/study-plan-generation",
            json=_payload(),
        )

    assert response.status_code == 400

    assert response.json() == {
        "error_code": (
            "STUDY_PLAN_GENERATION_INVALID"
        ),
        "message": (
            "The requested study plan could not "
            "be generated."
        ),
    }


def test_generation_persistence_error_is_safe() -> None:
    """Storage failures should return HTTP 503."""

    orchestrator = FakeOrchestrator()

    orchestrator.error = (
        StudyPlanPersistenceError(
            "internal storage detail",
        )
    )

    with _client(
        orchestrator,
    ) as client:
        response = client.post(
            "/api/study-plan-generation",
            json=_payload(),
        )

    assert response.status_code == 503

    assert (
        response.json()[
            "error_code"
        ]
        == "STUDY_PLAN_PERSISTENCE_FAILED"
    )


def test_generation_response_error_is_safe() -> None:
    """Invalid persisted responses should return HTTP 500."""

    orchestrator = FakeOrchestrator()

    orchestrator.error = StudyPlanResponseError(
        "internal response detail",
    )

    with _client(
        orchestrator,
    ) as client:
        response = client.post(
            "/api/study-plan-generation",
            json=_payload(),
        )

    assert response.status_code == 500

    assert (
        response.json()[
            "error_code"
        ]
        == "STUDY_PLAN_RESPONSE_FAILED"
    )