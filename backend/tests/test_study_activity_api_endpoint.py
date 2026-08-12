# File: /backend/tests/test_study_activity_api_endpoint.py
# Purpose: Verifies authentication, start, active-state,
# transition, validation, and controlled Study Activity API behavior.

from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    require_authenticated_user,
)
from app.api.study_activity_dependency import (
    get_study_activity_service,
)
from app.main import app
from app.schemas.study_activity import (
    StudyActivityBreakStartRequest,
    StudyActivityMode,
    StudyActivityResponse,
    StudyActivityStartRequest,
    StudyActivityStatus,
    StudyActivityTransitionAction,
)
from app.services.study_activity_errors import (
    StudyActivityConflictError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

PLAN_ID = UUID(
    "33333333-3333-4333-8333-333333333333",
)

SESSION_ID = UUID(
    "44444444-4444-4444-8444-444444444444",
)

ACTIVITY_ID = UUID(
    "55555555-5555-4555-8555-555555555555",
)

TIMESTAMP = datetime(
    2026,
    8,
    12,
    6,
    0,
    tzinfo=timezone.utc,
)


def _authenticated_user() -> SimpleNamespace:
    """Return a deterministic authenticated student."""

    return SimpleNamespace(
        user_id=USER_ID,
    )


def _running_activity(
    *,
    mode: StudyActivityMode = (
        StudyActivityMode.FOCUS
    ),
) -> StudyActivityResponse:
    """Return deterministic running timer data."""

    break_ends_at = (
        TIMESTAMP + timedelta(
            minutes=10,
        )
        if mode is StudyActivityMode.BREAK
        else None
    )

    return StudyActivityResponse(
        id=ACTIVITY_ID,
        subject_id=SUBJECT_ID,
        study_plan_id=PLAN_ID,
        study_session_id=SESSION_ID,
        title="Biology review",
        status=StudyActivityStatus.RUNNING,
        mode=mode,
        started_at=TIMESTAMP,
        ended_at=None,
        segment_started_at=TIMESTAMP,
        break_ends_at=break_ends_at,
        focus_seconds=1500,
        break_seconds=300,
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
    )


def _paused_activity() -> StudyActivityResponse:
    """Return deterministic paused timer data."""

    return StudyActivityResponse(
        id=ACTIVITY_ID,
        subject_id=SUBJECT_ID,
        study_plan_id=PLAN_ID,
        study_session_id=SESSION_ID,
        title="Biology review",
        status=StudyActivityStatus.PAUSED,
        mode=StudyActivityMode.FOCUS,
        started_at=TIMESTAMP,
        ended_at=None,
        segment_started_at=None,
        break_ends_at=None,
        focus_seconds=1500,
        break_seconds=300,
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
    )


class FakeStudyActivityService:
    """Return deterministic Study Activity API results."""

    def __init__(self) -> None:
        self.last_action: (
            StudyActivityTransitionAction
            | None
        ) = None

        self.last_break_minutes: int | None = None

    def get_active_activity(
        self,
        *,
        user_id: UUID,
    ) -> StudyActivityResponse | None:
        assert user_id == USER_ID

        return _running_activity()

    def start_activity(
        self,
        *,
        user_id: UUID,
        request: StudyActivityStartRequest,
    ) -> StudyActivityResponse:
        assert user_id == USER_ID
        assert request.study_session_id == SESSION_ID

        return _running_activity()

    def start_break(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        request: StudyActivityBreakStartRequest,
    ) -> StudyActivityResponse:
        assert user_id == USER_ID
        assert activity_id == ACTIVITY_ID

        self.last_break_minutes = (
            request.duration_minutes
        )

        return _running_activity(
            mode=StudyActivityMode.BREAK,
        )

    def transition_activity(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        action: StudyActivityTransitionAction,
    ) -> StudyActivityResponse:
        assert user_id == USER_ID
        assert activity_id == ACTIVITY_ID

        self.last_action = action

        if (
            action
            is StudyActivityTransitionAction.PAUSE
        ):
            return _paused_activity()

        if (
            action
            is StudyActivityTransitionAction.START_BREAK
        ):
            return _running_activity(
                mode=StudyActivityMode.BREAK,
            )

        return _running_activity()


class ConflictingStudyActivityService:
    """Simulate an existing unfinished timer."""

    def start_activity(
        self,
        *,
        user_id: UUID,
        request: StudyActivityStartRequest,
    ) -> StudyActivityResponse:
        _ = (
            user_id,
            request,
        )

        raise StudyActivityConflictError(
            "A study timer is already active.",
        )


FAKE_SERVICE = FakeStudyActivityService()


def _study_activity_service() -> FakeStudyActivityService:
    """Return the deterministic API-test service."""

    return FAKE_SERVICE


def _conflicting_service() -> ConflictingStudyActivityService:
    """Return a service that rejects timer start."""

    return ConflictingStudyActivityService()


def test_study_activity_requires_authentication() -> None:
    """Timer state may not be read anonymously."""

    with TestClient(app) as client:
        response = client.get(
            "/api/study-activity/active",
        )

    assert response.status_code == 401


def test_authenticated_user_can_read_active_timer() -> None:
    """Authenticated students can recover their unfinished timer."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/study-activity/active",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(
        ACTIVITY_ID,
    )

    assert payload["status"] == "running"
    assert payload["mode"] == "focus"
    assert payload["focus_seconds"] == 1500
    assert payload["break_seconds"] == 300


def test_authenticated_user_can_start_scheduled_timer() -> None:
    """A Study Plan session can start an actual focus timer."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/study-activity/start",
                json={
                    "study_session_id": str(
                        SESSION_ID,
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    assert (
        response.json()[
            "study_session_id"
        ]
        == str(
            SESSION_ID,
        )
    )


def test_free_study_request_requires_subject_and_title() -> None:
    """Incomplete free-study requests must fail schema validation."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/study-activity/start",
                json={
                    "subject_id": str(
                        SUBJECT_ID,
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_pause_endpoint_uses_pause_transition() -> None:
    """Pause endpoint must invoke the atomic pause action."""

    FAKE_SERVICE.last_action = None

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.post(
                (
                    "/api/study-activity/"
                    f"{ACTIVITY_ID}/pause"
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "paused"

    assert (
        FAKE_SERVICE.last_action
        is StudyActivityTransitionAction.PAUSE
    )


def test_break_endpoint_accepts_custom_duration() -> None:
    FAKE_SERVICE.last_break_minutes = None

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.post(
                (
                    "/api/study-activity/"
                    f"{ACTIVITY_ID}/break/start"
                ),
                json={
                    "duration_minutes": 10,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    payload = response.json()

    assert payload["mode"] == "break"
    assert payload["break_ends_at"] is not None
    assert FAKE_SERVICE.last_break_minutes == 10


def test_break_endpoint_defaults_to_five_minutes_without_body() -> None:
    FAKE_SERVICE.last_break_minutes = None

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.post(
                (
                    "/api/study-activity/"
                    f"{ACTIVITY_ID}/break/start"
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert FAKE_SERVICE.last_break_minutes == 5


def test_break_endpoint_rejects_invalid_duration() -> None:
    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _study_activity_service

    try:
        with TestClient(app) as client:
            response = client.post(
                (
                    "/api/study-activity/"
                    f"{ACTIVITY_ID}/break/start"
                ),
                json={
                    "duration_minutes": 0,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_start_returns_conflict_when_timer_already_exists() -> None:
    """A second unfinished timer must return a controlled 409."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_study_activity_service
    ] = _conflicting_service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/study-activity/start",
                json={
                    "study_session_id": str(
                        SESSION_ID,
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409

    assert response.json() == {
        "error_code": "STUDY_ACTIVITY_CONFLICT",
        "message": (
            "The study timer is not in a valid "
            "state for that action."
        ),
    }