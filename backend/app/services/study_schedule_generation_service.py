# File: /backend/app/services/study_schedule_generation_service.py
# Purpose: Orchestrates Track D schedule generation by combining
# generic schedulable tasks with the student's existing onboarding context.

from __future__ import annotations

from collections.abc import Sequence
from datetime import (
    date,
    datetime,
)
from typing import Protocol
from uuid import UUID

from pydantic import ValidationError

from app.schemas.study_scheduler import (
    SchedulableTask,
    SchedulerBlockedWindow,
    StudyScheduleRequest,
    StudyScheduleResult,
)
from app.schemas.study_scheduler_context import (
    StudySchedulerContext,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)


class _StudySchedulerContextService(
    Protocol,
):
    def get_scheduler_context(
        self,
        *,
        user_id: UUID,
    ) -> StudySchedulerContext: ...


class _StudyScheduler(
    Protocol,
):
    def generate(
        self,
        request: StudyScheduleRequest,
    ) -> StudyScheduleResult: ...


class StudyScheduleGenerationService:
    """Combines student context and generic tasks for scheduling."""

    def __init__(
        self,
        *,
        context_service: _StudySchedulerContextService,
        scheduler: _StudyScheduler,
    ) -> None:
        self._context_service = context_service
        self._scheduler = scheduler

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
    ) -> StudyScheduleResult:
        """Generate a study schedule using existing preferences."""

        context = (
            self._context_service
            .get_scheduler_context(
                user_id=user_id,
            )
        )

        try:
            request = StudyScheduleRequest(
                starts_on=starts_on,
                ends_on=ends_on,
                tasks=tuple(
                    tasks,
                ),
                availability=(
                    context.availability
                ),
                blocked_windows=tuple(
                    blocked_windows,
                ),
                not_before=not_before,

                preferences=(
                    context.preferences
                ),
            )

        except ValidationError as exc:
            raise StudyPlanValidationError(
                "Study schedule generation "
                "input was invalid.",
            ) from exc

        return self._scheduler.generate(
            request,
        )