# File: /backend/tests/test_study_plan_generation_orchestrator.py
# Purpose: Verifies Track D generate-and-save orchestration
# combines scheduling and persistence safely.

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
    SchedulableTask,
    StudyScheduleResult,
    UnscheduledTask,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)
from app.services.study_plan_generation_orchestrator import (
    StudyPlanGenerationOrchestrator,
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


def _task() -> SchedulableTask:
    return SchedulableTask(
        task_id=TASK_ID,
        subject_id=SUBJECT_ID,
        title="Review Chapter 4",
        deadline=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        estimated_minutes=120,
        priority_weight=3,
    )


def _generated_session() -> GeneratedStudySession:
    return GeneratedStudySession(
        task_id=TASK_ID,
        subject_id=SUBJECT_ID,
        title="Review Chapter 4",
        starts_at=SESSION_START,
        ends_at=SESSION_END,
        duration_minutes=60,
    )


def _persisted_result(
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
        generated_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )

    session = StudySessionResponse(
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
    )

    return GeneratedStudyPlanPersistenceResult(
        plan=plan,
        sessions=(
            session,
        ),
    )


class FakeGenerationService:
    def __init__(
        self,
        result: StudyScheduleResult,
    ) -> None:
        self.result = result
        self.calls = []

    def generate_schedule(
        self,
        *,
        user_id,
        starts_on,
        ends_on,
        tasks,
    ):
        self.calls.append(
            (
                user_id,
                starts_on,
                ends_on,
                tasks,
            )
        )

        return self.result


class FakePersistenceService:
    def __init__(
        self,
    ) -> None:
        self.calls = []
        self.result = _persisted_result()

    def persist_generated_plan(
        self,
        *,
        user_id,
        title,
        starts_on,
        ends_on,
        sessions,
    ):
        self.calls.append(
            (
                user_id,
                title,
                starts_on,
                ends_on,
                sessions,
            )
        )

        return self.result


def test_orchestrator_generates_for_authenticated_user() -> None:
    """Generation must use the authenticated owner."""

    generation = FakeGenerationService(
        StudyScheduleResult(
            sessions=(
                _generated_session(),
            ),
            unscheduled_tasks=(),
        )
    )

    persistence = FakePersistenceService()

    orchestrator = StudyPlanGenerationOrchestrator(
        generation_service=generation,
        persistence_service=persistence,
    )

    orchestrator.generate_and_save(
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
        tasks=(
            _task(),
        ),
    )

    assert generation.calls[0][0] == USER_ID


def test_orchestrator_persists_generated_sessions() -> None:
    """Generated sessions should be passed to persistence."""

    generated_session = _generated_session()

    generation = FakeGenerationService(
        StudyScheduleResult(
            sessions=(
                generated_session,
            ),
            unscheduled_tasks=(),
        )
    )

    persistence = FakePersistenceService()

    orchestrator = StudyPlanGenerationOrchestrator(
        generation_service=generation,
        persistence_service=persistence,
    )

    orchestrator.generate_and_save(
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
        tasks=(
            _task(),
        ),
    )

    assert len(
        persistence.calls,
    ) == 1

    assert persistence.calls[0][0] == USER_ID
    assert persistence.calls[0][1] == "Finals Plan"

    assert persistence.calls[0][4] == (
        generated_session,
    )


def test_orchestrator_preserves_unscheduled_work() -> None:
    """Partial generation should expose remaining work."""

    unscheduled = UnscheduledTask(
        task_id=TASK_ID,
        remaining_minutes=60,
    )

    generation = FakeGenerationService(
        StudyScheduleResult(
            sessions=(
                _generated_session(),
            ),
            unscheduled_tasks=(
                unscheduled,
            ),
        )
    )

    persistence = FakePersistenceService()

    result = StudyPlanGenerationOrchestrator(
        generation_service=generation,
        persistence_service=persistence,
    ).generate_and_save(
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
        tasks=(
            _task(),
        ),
    )

    assert result.plan.id == PLAN_ID

    assert result.unscheduled_tasks == (
        unscheduled,
    )


def test_orchestrator_does_not_persist_empty_schedule() -> None:
    """Nothing should persist when no session can be scheduled."""

    generation = FakeGenerationService(
        StudyScheduleResult(
            sessions=(),
            unscheduled_tasks=(
                UnscheduledTask(
                    task_id=TASK_ID,
                    remaining_minutes=120,
                ),
            ),
        )
    )

    persistence = FakePersistenceService()

    orchestrator = StudyPlanGenerationOrchestrator(
        generation_service=generation,
        persistence_service=persistence,
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        orchestrator.generate_and_save(
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
            tasks=(
                _task(),
            ),
        )

    assert persistence.calls == []