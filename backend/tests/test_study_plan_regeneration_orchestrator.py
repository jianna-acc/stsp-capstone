# File: /backend/tests/test_study_plan_regeneration_orchestrator.py
# Purpose: Tests generated-plan regeneration while preserving
# manual sessions as blocked study time.

from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import uuid4

import pytest

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_plan import (
    StudyPlanResponse,
    StudySessionListResponse,
    StudySessionResponse,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
    SchedulableTask,
    StudyScheduleResult,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)
from app.services.study_plan_regeneration_orchestrator import (
    StudyPlanRegenerationOrchestrator,
)

_NOW = datetime(
    2026,
    8,
    11,
    1,
    0,
    tzinfo=timezone.utc,
)


def _plan(
    *,
    generated: bool = True,
) -> StudyPlanResponse:
    return StudyPlanResponse(
        id=uuid4(),
        title="Finals Plan",
        starts_on=date(
            2026,
            8,
            11,
        ),
        ends_on=date(
            2026,
            8,
            20,
        ),
        status="active",
        generation_mode=(
            "generated"
            if generated
            else "manual"
        ),
        generated_at=(
            _NOW
            if generated
            else None
        ),
        created_at=_NOW,
        updated_at=_NOW,
    )


def _manual_session(
    plan_id,
) -> StudySessionResponse:
    return StudySessionResponse(
        id=uuid4(),
        study_plan_id=plan_id,
        subject_id=uuid4(),
        title="Manual review",
        starts_at=datetime(
            2026,
            8,
            11,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        ends_at=datetime(
            2026,
            8,
            11,
            11,
            0,
            tzinfo=timezone.utc,
        ),
        status="planned",
        origin="manual",
        notes=None,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _task() -> SchedulableTask:
    return SchedulableTask(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="Study Biology",
        deadline=datetime(
            2026,
            8,
            20,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        estimated_minutes=60,
        priority_weight=5,
    )


class _PlanServiceStub:
    def __init__(
        self,
        plan,
        manual_sessions,
    ) -> None:
        self.plan = plan
        self.manual_sessions = (
            manual_sessions
        )

    def get_study_plan(
        self,
        **kwargs,
    ):
        return self.plan

    def list_manual_study_sessions(
        self,
        **kwargs,
    ):
        return StudySessionListResponse(
            items=tuple(
                self.manual_sessions,
            ),
        )


class _GenerationServiceStub:
    def __init__(
        self,
        result,
    ) -> None:
        self.result = result
        self.request = None

    def generate_schedule(
        self,
        **kwargs,
    ):
        self.request = kwargs

        return self.result


class _RegenerationServiceStub:
    def __init__(
        self,
        result,
    ) -> None:
        self.result = result
        self.request = None

    def replace_generated_schedule(
        self,
        **kwargs,
    ):
        self.request = kwargs

        return self.result


def test_regeneration_blocks_manual_sessions_and_preserves_plan_id() -> None:
    plan = _plan()
    manual = _manual_session(
        plan.id,
    )

    generated = GeneratedStudySession(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="Generated review",
        starts_at=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        ends_at=datetime(
            2026,
            8,
            11,
            13,
            0,
            tzinfo=timezone.utc,
        ),
        duration_minutes=60,
    )

    schedule = StudyScheduleResult(
        sessions=(
            generated,
        ),
        unscheduled_tasks=(),
    )

    persisted = (
        GeneratedStudyPlanPersistenceResult(
            plan=plan,
            sessions=(
                manual,
            ),
        )
    )

    generation_service = (
        _GenerationServiceStub(
            schedule,
        )
    )

    regeneration_service = (
        _RegenerationServiceStub(
            persisted,
        )
    )

    orchestrator = (
        StudyPlanRegenerationOrchestrator(
            study_plan_service=(
                _PlanServiceStub(
                    plan,
                    [manual],
                )
            ),
            generation_service=(
                generation_service
            ),
            regeneration_service=(
                regeneration_service
            ),
            clock=lambda: _NOW,
        )
    )

    result = orchestrator.regenerate(
        user_id=uuid4(),
        study_plan_id=plan.id,
        tasks=(
            _task(),
        ),
    )

    assert (
        generation_service.request
        is not None
    )

    blocked = (
        generation_service.request[
            "blocked_windows"
        ]
    )

    assert len(
        blocked,
    ) == 1

    assert (
        blocked[0].starts_at
        == manual.starts_at
    )

    assert (
        generation_service.request[
            "not_before"
        ]
        == _NOW
    )

    assert (
        regeneration_service.request[
            "study_plan_id"
        ]
        == plan.id
    )

    assert (
        result.plan.id
        == plan.id
    )


def test_regeneration_rejects_manual_plan() -> None:
    plan = _plan(
        generated=False,
    )

    orchestrator = (
        StudyPlanRegenerationOrchestrator(
            study_plan_service=(
                _PlanServiceStub(
                    plan,
                    [],
                )
            ),
            generation_service=(
                _GenerationServiceStub(
                    StudyScheduleResult()
                )
            ),
            regeneration_service=(
                _RegenerationServiceStub(
                    GeneratedStudyPlanPersistenceResult(
                        plan=plan,
                        sessions=(),
                    )
                )
            ),
            clock=lambda: _NOW,
        )
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        orchestrator.regenerate(
            user_id=uuid4(),
            study_plan_id=plan.id,
            tasks=(
                _task(),
            ),
        )