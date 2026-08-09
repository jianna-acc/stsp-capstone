# File: /backend/tests/test_study_plan_service.py
# Purpose: Verifies Track D study-plan business rules independently
# of Supabase and unfinished cross-track integrations.

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import pytest

from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanGenerationMode,
    StudyPlanResponse,
    StudyPlanStatus,
    StudySessionCreateRequest,
    StudySessionOrigin,
    StudySessionResponse,
    StudySessionStatus,
)
from app.services.study_plan_errors import (
    StudyPlanNotFoundError,
    StudyPlanValidationError,
    StudySessionNotFoundError,
)
from app.services.study_plan_service import (
    StudyPlanService,
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


class FakeStudyPlanRepository:
    def __init__(self) -> None:
        self.plan: StudyPlanResponse | None = (
            _plan()
        )
        self.session = _session()
        self.plan_deleted = True
        self.session_deleted = True

    def create_study_plan(
        self,
        *,
        user_id,
        request,
    ):
        del user_id, request
        return _plan()

    def list_study_plans(
        self,
        *,
        user_id,
        limit=50,
    ):
        del user_id, limit
        return (
            []
            if self.plan is None
            else [
                self.plan,
            ]
        )

    def get_study_plan(
        self,
        *,
        user_id,
        study_plan_id,
    ):
        del user_id, study_plan_id
        return self.plan

    def delete_study_plan(
        self,
        *,
        user_id,
        study_plan_id,
    ):
        del user_id, study_plan_id
        return self.plan_deleted

    def create_study_session(
        self,
        *,
        user_id,
        study_plan_id,
        request,
    ):
        del user_id, study_plan_id, request
        return self.session

    def list_study_sessions(
        self,
        *,
        user_id,
        study_plan_id,
        limit=200,
    ):
        del user_id, study_plan_id, limit
        return [
            self.session,
        ]

    def delete_study_session(
        self,
        *,
        user_id,
        study_plan_id,
        study_session_id,
    ):
        del user_id
        del study_plan_id
        del study_session_id

        return self.session_deleted


def test_create_study_plan_returns_repository_result() -> None:
    service = StudyPlanService(
        FakeStudyPlanRepository(),
    )

    result = service.create_study_plan(
        user_id=USER_ID,
        request=StudyPlanCreateRequest(
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
        ),
    )

    assert result.id == PLAN_ID


def test_get_missing_study_plan_raises() -> None:
    repository = FakeStudyPlanRepository()
    repository.plan = None

    service = StudyPlanService(
        repository,
    )

    with pytest.raises(
        StudyPlanNotFoundError,
    ):
        service.get_study_plan(
            user_id=USER_ID,
            study_plan_id=PLAN_ID,
        )


def test_delete_missing_study_plan_raises() -> None:
    repository = FakeStudyPlanRepository()
    repository.plan_deleted = False

    service = StudyPlanService(
        repository,
    )

    with pytest.raises(
        StudyPlanNotFoundError,
    ):
        service.delete_study_plan(
            user_id=USER_ID,
            study_plan_id=PLAN_ID,
        )


def test_create_session_inside_plan_succeeds() -> None:
    service = StudyPlanService(
        FakeStudyPlanRepository(),
    )

    starts_at = datetime(
        2026,
        8,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    result = service.create_study_session(
        user_id=USER_ID,
        study_plan_id=PLAN_ID,
        request=StudySessionCreateRequest(
            subject_id=SUBJECT_ID,
            title="Practice",
            starts_at=starts_at,
            ends_at=(
                starts_at
                + timedelta(
                    hours=1,
                )
            ),
        ),
    )

    assert result.id == SESSION_ID


def test_create_session_outside_plan_rejected() -> None:
    service = StudyPlanService(
        FakeStudyPlanRepository(),
    )

    starts_at = datetime(
        2026,
        8,
        20,
        10,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        service.create_study_session(
            user_id=USER_ID,
            study_plan_id=PLAN_ID,
            request=StudySessionCreateRequest(
                subject_id=SUBJECT_ID,
                title="Practice",
                starts_at=starts_at,
                ends_at=(
                    starts_at
                    + timedelta(
                        hours=1,
                    )
                ),
            ),
        )


def test_list_sessions_requires_existing_plan() -> None:
    repository = FakeStudyPlanRepository()
    repository.plan = None

    service = StudyPlanService(
        repository,
    )

    with pytest.raises(
        StudyPlanNotFoundError,
    ):
        service.list_study_sessions(
            user_id=USER_ID,
            study_plan_id=PLAN_ID,
        )


def test_delete_missing_session_raises() -> None:
    repository = FakeStudyPlanRepository()
    repository.session_deleted = False

    service = StudyPlanService(
        repository,
    )

    with pytest.raises(
        StudySessionNotFoundError,
    ):
        service.delete_study_session(
            user_id=USER_ID,
            study_plan_id=PLAN_ID,
            study_session_id=SESSION_ID,
        )