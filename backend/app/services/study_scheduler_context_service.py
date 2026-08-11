# File: /backend/app/services/study_scheduler_context_service.py
# Purpose: Provides validated existing student scheduling context
# to the independent Track D scheduler.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.study_scheduler_context import (
    StudySchedulerContext,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)


class _StudySchedulerContextRepository(
    Protocol,
):
    def get_scheduler_context(
        self,
        *,
        user_id: UUID,
    ) -> StudySchedulerContext | None: ...


class StudySchedulerContextService:
    """Coordinates loading of student scheduling preferences."""

    def __init__(
        self,
        repository: _StudySchedulerContextRepository,
    ) -> None:
        self._repository = repository

    def get_scheduler_context(
        self,
        *,
        user_id: UUID,
    ) -> StudySchedulerContext:
        """Return complete scheduling context for one student."""

        context = (
            self._repository
            .get_scheduler_context(
                user_id=user_id,
            )
        )

        if context is None:
            raise StudyPlanValidationError(
                "Study scheduling requires "
                "completed study preferences "
                "and availability.",
            )

        return context