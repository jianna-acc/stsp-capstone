# File: /backend/tests/test_study_schedule_generation_service.py
# Purpose: Verifies Track D generation orchestration remains
# independent from Academic Tasks while using real onboarding context.

from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import pytest

from app.schemas.study_scheduler import (
    GeneratedStudySession,
    SchedulableTask,
    SchedulerAvailabilitySlot,
    SchedulerPreferences,
    StudyScheduleRequest,
    StudyScheduleResult,
)
from app.schemas.study_scheduler_context import (
    StudySchedulerContext,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)
from app.services.study_schedule_generation_service import (
    StudyScheduleGenerationService,
)
from app.services.study_scheduler import (
    StudyScheduler,
)

USER_ID = uuid4()
TASK_ID = uuid4()
SUBJECT_ID = uuid4()


def _task(
    *,
    estimated_minutes: int = 60,
) -> SchedulableTask:
    """Return one generic schedulable task."""

    return SchedulableTask(
        task_id=TASK_ID,
        subject_id=SUBJECT_ID,
        title="Review Chapter 4",
        deadline=datetime(
            2026,
            8,
            10,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        estimated_minutes=(
            estimated_minutes
        ),
        priority_weight=3,
    )


def _context() -> StudySchedulerContext:
    """Return existing onboarding scheduling context."""

    return StudySchedulerContext(
        preferences=SchedulerPreferences(
            timezone="Asia/Manila",
            preferred_session_minutes=60,
            minimum_session_minutes=15,
        ),
        availability=(
            SchedulerAvailabilitySlot(
                day_of_week=1,
                start_time="18:00:00",
                end_time="20:00:00",
            ),
        ),
    )


class FakeContextService:
    """Records context-service calls."""

    def __init__(
        self,
        context: StudySchedulerContext,
    ) -> None:
        self.context = context

        self.user_ids = []

    def get_scheduler_context(
        self,
        *,
        user_id,
    ) -> StudySchedulerContext:
        self.user_ids.append(
            user_id,
        )

        return self.context


class FailingContextService:
    """Represents incomplete onboarding context."""

    def get_scheduler_context(
        self,
        *,
        user_id,
    ) -> StudySchedulerContext:
        del user_id

        raise StudyPlanValidationError(
            "missing scheduling context",
        )


class FakeScheduler:
    """Records the generated scheduler request."""

    def __init__(
        self,
    ) -> None:
        self.request: (
            StudyScheduleRequest
            | None
        ) = None

        self.result = StudyScheduleResult(
            sessions=(),
            unscheduled_tasks=(),
        )

    def generate(
        self,
        request: StudyScheduleRequest,
    ) -> StudyScheduleResult:
        self.request = request

        return self.result


def test_generation_loads_authenticated_user_context() -> None:
    """The orchestrator must load context for the given user."""

    context_service = FakeContextService(
        _context(),
    )

    scheduler = FakeScheduler()

    service = StudyScheduleGenerationService(
        context_service=context_service,
        scheduler=scheduler,
    )

    service.generate_schedule(
        user_id=USER_ID,
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
        tasks=(
            _task(),
        ),
    )

    assert context_service.user_ids == [
        USER_ID,
    ]


def test_generation_uses_existing_preferences() -> None:
    """Existing onboarding preferences should reach scheduler."""

    scheduler = FakeScheduler()

    service = StudyScheduleGenerationService(
        context_service=FakeContextService(
            _context(),
        ),
        scheduler=scheduler,
    )

    service.generate_schedule(
        user_id=USER_ID,
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
        tasks=(
            _task(),
        ),
    )

    assert scheduler.request is not None

    assert (
        scheduler.request.preferences.timezone
        == "Asia/Manila"
    )

    assert (
        scheduler.request.preferences
        .preferred_session_minutes
        == 60
    )

    assert (
        scheduler.request.availability
        == _context().availability
    )


def test_generation_preserves_generic_tasks() -> None:
    """Generic tasks should pass unchanged to scheduler."""

    task = _task()

    scheduler = FakeScheduler()

    service = StudyScheduleGenerationService(
        context_service=FakeContextService(
            _context(),
        ),
        scheduler=scheduler,
    )

    service.generate_schedule(
        user_id=USER_ID,
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
        tasks=(
            task,
        ),
    )

    assert scheduler.request is not None

    assert scheduler.request.tasks == (
        task,
    )


def test_generation_rejects_empty_tasks() -> None:
    """Generating without tasks should fail safely."""

    service = StudyScheduleGenerationService(
        context_service=FakeContextService(
            _context(),
        ),
        scheduler=FakeScheduler(),
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        service.generate_schedule(
            user_id=USER_ID,
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
            tasks=(),
        )


def test_generation_rejects_invalid_date_range() -> None:
    """Reversed plan dates should become controlled errors."""

    service = StudyScheduleGenerationService(
        context_service=FakeContextService(
            _context(),
        ),
        scheduler=FakeScheduler(),
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        service.generate_schedule(
            user_id=USER_ID,
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
            tasks=(
                _task(),
            ),
        )


def test_generation_propagates_missing_context() -> None:
    """Incomplete onboarding should remain a controlled error."""

    service = StudyScheduleGenerationService(
        context_service=(
            FailingContextService()
        ),
        scheduler=FakeScheduler(),
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        service.generate_schedule(
            user_id=USER_ID,
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
            tasks=(
                _task(),
            ),
        )


def test_generation_runs_real_scheduler_with_context() -> None:
    """Real scheduler should consume the assembled request."""

    service = StudyScheduleGenerationService(
        context_service=FakeContextService(
            _context(),
        ),
        scheduler=StudyScheduler(),
    )

    result = service.generate_schedule(
        user_id=USER_ID,
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
        tasks=(
            _task(),
        ),
    )

    assert len(
        result.sessions,
    ) == 1

    session: GeneratedStudySession = (
        result.sessions[0]
    )

    assert session.task_id == TASK_ID

    assert session.subject_id == SUBJECT_ID

    assert session.starts_at.hour == 18

    assert (
        session.starts_at.utcoffset()
        == timedelta(
            hours=8,
        )
    )

    assert (
        session.ends_at
        - session.starts_at
        == timedelta(
            minutes=60,
        )
    )

    assert result.unscheduled_tasks == ()