# File: /backend/app/services/academic_task_priority_service.py
# Purpose: Orchestrates academic-task priority scoring using
# task data and authenticated student learning context.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.repositories.academic_task_priority_context_repository import (
    AcademicTaskPriorityContextData,
)
from app.schemas.academic_task import (
    AcademicTaskResponse,
)
from app.services.academic_task_errors import (
    AcademicTaskResponseError,
)
from app.services.academic_task_priority import (
    AcademicTaskPriorityInput,
    AcademicTaskPriorityResult,
    calculate_academic_task_priority,
)
from app.services.academic_task_priority_context import (
    calculate_available_study_minutes,
    resolve_output_confidence,
)


class AcademicTaskPriorityContextRepositoryProtocol(
    Protocol,
):
    """Student context required by task priority scoring."""

    def load_priority_context(
        self,
        *,
        user_id: UUID,
    ) -> AcademicTaskPriorityContextData: ...


@dataclass(
    frozen=True,
    slots=True,
)
class AcademicTaskPriorityEvaluation:
    """One task together with its calculated priority."""

    task: AcademicTaskResponse
    priority: AcademicTaskPriorityResult


class AcademicTaskPriorityService:
    """Coordinates deterministic priority scoring for owned tasks."""

    def __init__(
        self,
        context_repository: (
            AcademicTaskPriorityContextRepositoryProtocol
        ),
    ) -> None:
        self._context_repository = context_repository

    def score_task(
        self,
        *,
        user_id: UUID,
        task: AcademicTaskResponse,
        now: datetime,
    ) -> AcademicTaskPriorityEvaluation:
        """Calculate priority for one academic task."""

        context = (
            self._context_repository
            .load_priority_context(
                user_id=user_id,
            )
        )

        return self._score_with_context(
            task=task,
            context=context,
            now=now,
        )

    def score_tasks(
        self,
        *,
        user_id: UUID,
        tasks: list[
            AcademicTaskResponse
        ],
        now: datetime,
    ) -> list[
        AcademicTaskPriorityEvaluation
    ]:
        """Calculate priorities while loading student context once."""

        if not tasks:
            return []

        context = (
            self._context_repository
            .load_priority_context(
                user_id=user_id,
            )
        )

        return [
            self._score_with_context(
                task=task,
                context=context,
                now=now,
            )
            for task in tasks
        ]

    def _score_with_context(
        self,
        *,
        task: AcademicTaskResponse,
        context: AcademicTaskPriorityContextData,
        now: datetime,
    ) -> AcademicTaskPriorityEvaluation:
        """Resolve context and calculate one task priority."""

        try:
            output_confidence = (
                resolve_output_confidence(
                    output_type=task.output_type,
                    confidence_levels=(
                        context.confidence_levels
                    ),
                )
            )

            if (
                context.availability_slots
            ):
                available_minutes = (
                    calculate_available_study_minutes(
                        slots=(
                            context.availability_slots
                        ),
                        now=now,
                        deadline=task.deadline,
                        timezone_name=(
                            context.timezone_name
                        ),
                    )
                )
            else:
                available_minutes = None

            priority = (
                calculate_academic_task_priority(
                    AcademicTaskPriorityInput(
                        deadline=task.deadline,
                        estimated_minutes=(
                            task.estimated_minutes
                        ),
                        difficulty=task.difficulty,
                        status=task.status,
                        output_confidence_level=(
                            output_confidence
                        ),
                        previous_performance_percent=None,
                        available_study_minutes_until_deadline=(
                            available_minutes
                        ),
                    ),
                    now=now,
                )
            )

        except ValueError as exc:
            raise AcademicTaskResponseError(
                "Stored student priority context was invalid.",
            ) from exc

        return AcademicTaskPriorityEvaluation(
            task=task,
            priority=priority,
        )