# File: /backend/tests/test_generated_study_plan_service.py
# Purpose: Verifies generated Track D schedules are validated
# before being handed to persistence.

from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import pytest

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_plan import (
    StudyPlanGenerationMode,
    StudyPlanResponse,
    StudyPlanStatus,
    StudySessionOrigin,
    StudySessionResponse,
    StudySessionStatus,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)
from app.services.generated_study_plan_service import (
    GeneratedStudyPlanService,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)

USER_ID = uuid4()
PLAN_ID = uuid4()
SESSION_ID = uuid4()
TASK_ID = uuid4()
SUBJECT_ID = uuid4()

GENERATED_AT = datetime(
    2026,
    8,
    10,
    7,
    0,
    tzinfo=timezone.utc,
)

STARTS_AT = datetime(
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

ENDS_AT = STARTS_AT + timedelta(
    minutes=60,
)


def _generated_session(
) -> GeneratedStudySession:
    return GeneratedStudySession(
        task_id=TASK_ID,
        subject_id=SUBJECT_ID,
        title="Review Chapter 4",
        starts_at=STARTS_AT,
        ends_at=ENDS_AT,
        duration_minutes=60,
    )


def _persistence_result(
) -> GeneratedStudyPlanPersistenceResult:
    plan = StudyPlanResponse(
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
        generated_at=GENERATED_AT,
        created_at=GENERATED_AT,
        updated_at=GENERATED_AT,
    )

    session = StudySessionResponse(
        id=SESSION_ID,
        study_plan_id=PLAN_ID,
        subject_id=SUBJECT_ID,
        title="Review Chapter 4",
        starts_at=STARTS_AT,
        ends_at=ENDS_AT,
        status=StudySessionStatus.PLANNED,
        origin=StudySessionOrigin.GENERATED,
        notes=None,
        created_at=GENERATED_AT,
        updated_at=GENERATED_AT,
    )

    return GeneratedStudyPlanPersistenceResult(
        plan=plan,
        sessions=(
            session,
        ),
    )


class FakeRepository:
    def __init__(
        self,
    ) -> None:
        self.calls = []

        self.result = _persistence_result()

    def persist_generated_plan(
        self,
        *,
        user_id,
        request,
    ):
        self.calls.append(
            (
                user_id,
                request,
            )
        )

        return self.result


def _service(
    repository: FakeRepository,
) -> GeneratedStudyPlanService:
    return GeneratedStudyPlanService(
        repository,
        clock=lambda: GENERATED_AT,
    )


def test_service_persists_generated_plan() -> None:
    """Valid generated output should reach persistence."""

    repository = FakeRepository()

    result = _service(
        repository,
    ).persist_generated_plan(
        user_id=USER_ID,
        title="  Finals Plan  ",
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
        sessions=(
            _generated_session(),
        ),
    )

    assert result == repository.result
    assert len(repository.calls) == 1

    user_id, request = repository.calls[0]

    assert user_id == USER_ID
    assert request.title == "Finals Plan"
    assert request.generated_at == GENERATED_AT
    assert len(request.sessions) == 1


def test_service_rejects_empty_sessions() -> None:
    """A generated plan must contain at least one session."""

    repository = FakeRepository()

    with pytest.raises(
        StudyPlanValidationError,
    ):
        _service(
            repository,
        ).persist_generated_plan(
            user_id=USER_ID,
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
            sessions=(),
        )

    assert repository.calls == []


def test_service_rejects_reversed_range() -> None:
    """Generated plans must use a valid date range."""

    repository = FakeRepository()

    with pytest.raises(
        StudyPlanValidationError,
    ):
        _service(
            repository,
        ).persist_generated_plan(
            user_id=USER_ID,
            title="Finals Plan",
            starts_on=date(
                2026,
                8,
                11,
            ),
            ends_on=date(
                2026,
                8,
                10,
            ),
            sessions=(
                _generated_session(),
            ),
        )


def test_service_rejects_session_outside_plan() -> None:
    """Generated sessions must remain within plan dates."""

    repository = FakeRepository()

    with pytest.raises(
        StudyPlanValidationError,
    ):
        _service(
            repository,
        ).persist_generated_plan(
            user_id=USER_ID,
            title="Finals Plan",
            starts_on=date(
                2026,
                8,
                11,
            ),
            ends_on=date(
                2026,
                8,
                11,
            ),
            sessions=(
                _generated_session(),
            ),
        )