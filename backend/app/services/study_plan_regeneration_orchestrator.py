# File: /backend/app/services/study_plan_regeneration_orchestrator.py
# Purpose: Rebuilds an existing generated study plan using the
# student's latest tasks, availability, and preserved manual sessions.

from __future__ import annotations

from collections.abc import (
    Callable,
    Sequence,
)
from datetime import (
    date,
    datetime,
    timezone,
)
from typing import Protocol
from uuid import UUID

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_plan import (
    StudyPlanResponse,
    StudySessionListResponse,
)
from app.schemas.study_plan_generation_api import (
    StudyPlanGenerationResponse,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
    SchedulableTask,
    SchedulerBlockedWindow,
    StudyScheduleResult,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)


class _StudyPlanService(
    Protocol,
):
    def get_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> StudyPlanResponse: ...

    def list_manual_study_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        limit: int = 500,
    ) -> StudySessionListResponse: ...


class _StudyScheduleGenerationService(
    Protocol,
):
    def generate_schedule(
        self,
        *,
        user_id: UUID,
        starts_on: date,
        ends_on: date,
        tasks: Sequence[
            SchedulableTask
        ],
        blocked_windows: Sequence[
            SchedulerBlockedWindow
        ] = (),
        not_before: datetime | None = None,
    ) -> StudyScheduleResult: ...


class _GeneratedStudyPlanRegenerationService(
    Protocol,
):
    def replace_generated_schedule(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        sessions: Sequence[
            GeneratedStudySession
        ],
    ) -> GeneratedStudyPlanPersistenceResult: ...


def _utc_now() -> datetime:
    """Return an aware current UTC timestamp."""

    return datetime.now(
        timezone.utc,
    )


class StudyPlanRegenerationOrchestrator:
    """Rebuild an existing generated plan without losing manual work."""

    def __init__(
        self,
        *,
        study_plan_service: _StudyPlanService,
        generation_service:
            _StudyScheduleGenerationService,
        regeneration_service:
            _GeneratedStudyPlanRegenerationService,
        clock: Callable[
            [],
            datetime,
        ] = _utc_now,
    ) -> None:
        self._study_plan_service = (
            study_plan_service
        )
        self._generation_service = (
            generation_service
        )
        self._regeneration_service = (
            regeneration_service
        )
        self._clock = clock

    def regenerate(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        tasks: Sequence[
            SchedulableTask
        ],
    ) -> StudyPlanGenerationResponse:
        """Rebuild generated sessions for one existing plan."""

        plan = (
            self._study_plan_service
            .get_study_plan(
                user_id=user_id,
                study_plan_id=study_plan_id,
            )
        )

        if (
            plan.generation_mode
            != "generated"
        ):
            raise StudyPlanValidationError(
                "Only generated study plans "
                "can be regenerated.",
            )

        manual_sessions = (
            self._study_plan_service
            .list_manual_study_sessions(
                user_id=user_id,
                study_plan_id=study_plan_id,
                limit=500,
            )
        )

        blocked_windows = tuple(
            SchedulerBlockedWindow(
                starts_at=(
                    session.starts_at
                ),
                ends_at=(
                    session.ends_at
                ),
            )
            for session
            in manual_sessions.items
        )

        schedule = (
            self._generation_service
            .generate_schedule(
                user_id=user_id,
                starts_on=plan.starts_on,
                ends_on=plan.ends_on,
                tasks=tasks,
                blocked_windows=(
                    blocked_windows
                ),
                not_before=(
                    self._clock()
                ),
            )
        )

        if not schedule.sessions:
            raise StudyPlanValidationError(
                "No future study sessions could "
                "be scheduled for this plan.",
            )

        persisted = (
            self._regeneration_service
            .replace_generated_schedule(
                user_id=user_id,
                study_plan_id=study_plan_id,
                sessions=schedule.sessions,
            )
        )

        return StudyPlanGenerationResponse(
            plan=persisted.plan,
            sessions=persisted.sessions,
            unscheduled_tasks=(
                schedule.unscheduled_tasks
            ),
        )