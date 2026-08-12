# File: /backend/tests/test_study_activity_service.py
# Purpose: Verifies Study Activity orchestration for free study,
# scheduled sessions, conflicts, validation, and transitions.

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from uuid import UUID

import pytest

from app.repositories.study_activity_repository import (
    StudyActivityStudySessionTarget,
)
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
    StudyActivityNotFoundError,
    StudyActivityValidationError,
)
from app.services.study_activity_service import (
    StudyActivityService,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

OTHER_SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-333333333333",
)

PLAN_ID = UUID(
    "33333333-3333-4333-8333-333333333333",
)

OTHER_PLAN_ID = UUID(
    "33333333-3333-4333-8333-444444444444",
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


def _running_activity() -> StudyActivityResponse:
    """Return deterministic running timer data."""

    return StudyActivityResponse(
        id=ACTIVITY_ID,
        subject_id=SUBJECT_ID,
        study_plan_id=PLAN_ID,
        study_session_id=SESSION_ID,
        title="Biology review",
        status=StudyActivityStatus.RUNNING,
        mode=StudyActivityMode.FOCUS,
        started_at=TIMESTAMP,
        ended_at=None,
        segment_started_at=TIMESTAMP,
        focus_seconds=0,
        break_seconds=0,
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
    )


class FakeRepository:
    """Record service delegation and expose deterministic targets."""

    def __init__(self) -> None:
        self.active_activity: (
            StudyActivityResponse
            | None
        ) = None

        self.subject_available = True
        self.plan_available = True

        self.study_session_target: (
            StudyActivityStudySessionTarget
            | None
        ) = None

        self.start_call: (
            dict[
                str,
                object,
            ]
            | None
        ) = None

        self.break_call: (
            dict[
                str,
                object,
            ]
            | None
        ) = None

        self.transition_call: (
            dict[
                str,
                object,
            ]
            | None
        ) = None

    def get_active_activity(
        self,
        *,
        user_id: UUID,
    ) -> StudyActivityResponse | None:
        assert user_id == USER_ID

        return self.active_activity

    def subject_exists(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
    ) -> bool:
        assert user_id == USER_ID
        assert subject_id in {
            SUBJECT_ID,
            OTHER_SUBJECT_ID,
        }

        return self.subject_available

    def study_plan_exists(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> bool:
        assert user_id == USER_ID
        assert study_plan_id in {
            PLAN_ID,
            OTHER_PLAN_ID,
        }

        return self.plan_available

    def get_study_session_target(
        self,
        *,
        user_id: UUID,
        study_session_id: UUID,
    ) -> StudyActivityStudySessionTarget | None:
        assert user_id == USER_ID
        assert study_session_id == SESSION_ID

        return self.study_session_target

    def start_activity(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        title: str,
        study_plan_id: UUID | None,
        study_session_id: UUID | None,
    ) -> StudyActivityResponse:
        self.start_call = {
            "user_id": user_id,
            "subject_id": subject_id,
            "title": title,
            "study_plan_id": study_plan_id,
            "study_session_id": study_session_id,
        }

        return _running_activity()

    def start_break(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        duration_minutes: int,
    ) -> StudyActivityResponse:
        self.break_call = {
            "user_id": user_id,
            "activity_id": activity_id,
            "duration_minutes": duration_minutes,
        }

        return StudyActivityResponse(
            id=ACTIVITY_ID,
            subject_id=SUBJECT_ID,
            study_plan_id=PLAN_ID,
            study_session_id=SESSION_ID,
            title="Biology review",
            status=StudyActivityStatus.RUNNING,
            mode=StudyActivityMode.BREAK,
            started_at=TIMESTAMP,
            ended_at=None,
            segment_started_at=TIMESTAMP,
            break_ends_at=TIMESTAMP.replace(
                minute=10,
            ),
            focus_seconds=600,
            break_seconds=0,
            created_at=TIMESTAMP,
            updated_at=TIMESTAMP,
        )

    def transition_activity(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        action: StudyActivityTransitionAction,
    ) -> StudyActivityResponse:
        self.transition_call = {
            "user_id": user_id,
            "activity_id": activity_id,
            "action": action,
        }

        return _running_activity()


def test_free_study_uses_selected_subject_and_title() -> None:
    """Free study starts from explicitly selected trusted subject metadata."""

    repository = FakeRepository()

    service = StudyActivityService(
        repository,
    )

    result = service.start_activity(
        user_id=USER_ID,
        request=StudyActivityStartRequest(
            subject_id=SUBJECT_ID,
            title="Biology review",
        ),
    )

    assert result.id == ACTIVITY_ID

    assert repository.start_call == {
        "user_id": USER_ID,
        "subject_id": SUBJECT_ID,
        "title": "Biology review",
        "study_plan_id": None,
        "study_session_id": None,
    }


def test_scheduled_study_derives_metadata_from_owned_session() -> None:
    """Scheduled starts must not trust duplicated browser metadata."""

    repository = FakeRepository()

    repository.study_session_target = (
        StudyActivityStudySessionTarget(
            id=SESSION_ID,
            study_plan_id=PLAN_ID,
            subject_id=SUBJECT_ID,
            title="Biology review",
        )
    )

    service = StudyActivityService(
        repository,
    )

    result = service.start_activity(
        user_id=USER_ID,
        request=StudyActivityStartRequest(
            study_session_id=SESSION_ID,
        ),
    )

    assert result.id == ACTIVITY_ID

    assert repository.start_call == {
        "user_id": USER_ID,
        "subject_id": SUBJECT_ID,
        "title": "Biology review",
        "study_plan_id": PLAN_ID,
        "study_session_id": SESSION_ID,
    }


def test_start_rejects_second_unfinished_timer() -> None:
    """One student may have only one unfinished Study Activity."""

    repository = FakeRepository()

    repository.active_activity = (
        _running_activity()
    )

    service = StudyActivityService(
        repository,
    )

    with pytest.raises(
        StudyActivityConflictError,
    ):
        service.start_activity(
            user_id=USER_ID,
            request=StudyActivityStartRequest(
                subject_id=SUBJECT_ID,
                title="Another session",
            ),
        )

    assert repository.start_call is None


def test_free_study_rejects_missing_owned_subject() -> None:
    """A free-study timer cannot target another student's subject."""

    repository = FakeRepository()

    repository.subject_available = False

    service = StudyActivityService(
        repository,
    )

    with pytest.raises(
        StudyActivityNotFoundError,
    ):
        service.start_activity(
            user_id=USER_ID,
            request=StudyActivityStartRequest(
                subject_id=SUBJECT_ID,
                title="Biology review",
            ),
        )


def test_scheduled_start_rejects_mismatched_browser_metadata() -> None:
    """Duplicated browser metadata cannot override the scheduled target."""

    repository = FakeRepository()

    repository.study_session_target = (
        StudyActivityStudySessionTarget(
            id=SESSION_ID,
            study_plan_id=PLAN_ID,
            subject_id=SUBJECT_ID,
            title="Biology review",
        )
    )

    service = StudyActivityService(
        repository,
    )

    with pytest.raises(
        StudyActivityValidationError,
    ):
        service.start_activity(
            user_id=USER_ID,
            request=StudyActivityStartRequest(
                study_session_id=SESSION_ID,
                subject_id=OTHER_SUBJECT_ID,
            ),
        )


def test_transition_delegates_atomic_action() -> None:
    """Timer lifecycle changes must delegate to the repository RPC."""

    repository = FakeRepository()

    service = StudyActivityService(
        repository,
    )

    result = service.transition_activity(
        user_id=USER_ID,
        activity_id=ACTIVITY_ID,
        action=(
            StudyActivityTransitionAction.START_BREAK
        ),
    )

    assert result.id == ACTIVITY_ID

    assert repository.transition_call == {
        "user_id": USER_ID,
        "activity_id": ACTIVITY_ID,
        "action": (
            StudyActivityTransitionAction.START_BREAK
        ),
    }

def test_start_break_delegates_duration_to_repository() -> None:
    repository = FakeRepository()

    service = StudyActivityService(
        repository,
    )

    result = service.start_break(
        user_id=USER_ID,
        activity_id=ACTIVITY_ID,
        request=StudyActivityBreakStartRequest(
            duration_minutes=10,
        ),
    )

    assert result.mode is StudyActivityMode.BREAK
    assert result.break_ends_at is not None

    assert repository.break_call == {
        "user_id": USER_ID,
        "activity_id": ACTIVITY_ID,
        "duration_minutes": 10,
    }

