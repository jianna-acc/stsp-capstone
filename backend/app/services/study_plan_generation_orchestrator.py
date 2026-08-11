# File: /backend/app/services/study_plan_generation_orchestrator.py
# Purpose: Combines Track D schedule generation and generated-plan
# persistence into one authenticated application operation.

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol
from uuid import UUID

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_plan_generation_api import (
    StudyPlanGenerationResponse,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
    SchedulableTask,
    StudyScheduleResult,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)


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
    ) -> StudyScheduleResult: ...


class _GeneratedStudyPlanService(
    Protocol,
):
    def persist_generated_plan(
        self,
        *,
        user_id: UUID,
        title: str,
        starts_on: date,
        ends_on: date,
        sessions: Sequence[
            GeneratedStudySession
        ],
    ) -> GeneratedStudyPlanPersistenceResult: ...


class StudyPlanGenerationOrchestrator:
    """Generates and persists one student study plan."""

    def __init__(
        self,
        *,
        generation_service: _StudyScheduleGenerationService,
        persistence_service: _GeneratedStudyPlanService,
    ) -> None:
        self._generation_service = generation_service
        self._persistence_service = persistence_service

    def generate_and_save(
        self,
        *,
        user_id: UUID,
        title: str,
        starts_on: date,
        ends_on: date,
        tasks: Sequence[
            SchedulableTask
        ],
    ) -> StudyPlanGenerationResponse:
        """Generate sessions and persist the resulting plan."""

        schedule = (
            self._generation_service
            .generate_schedule(
                user_id=user_id,
                starts_on=starts_on,
                ends_on=ends_on,
                tasks=tasks,
            )
        )

        if not schedule.sessions:
            raise StudyPlanValidationError(
                "No study sessions could be scheduled "
                "within the requested date range.",
            )

        persisted = (
            self._persistence_service
            .persist_generated_plan(
                user_id=user_id,
                title=title,
                starts_on=starts_on,
                ends_on=ends_on,
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