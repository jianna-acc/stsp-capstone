# File: /backend/app/services/generated_study_plan_service.py
# Purpose: Validates and persists generated Track D schedules
# without depending on the unfinished Academic Tasks track.

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import (
    date,
    datetime,
    timezone,
)
from typing import (
    Protocol,
)
from uuid import UUID

from pydantic import ValidationError

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceRequest,
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)


class _GeneratedStudyPlanRepository(
    Protocol,
):
    def persist_generated_plan(
        self,
        *,
        user_id: UUID,
        request: GeneratedStudyPlanPersistenceRequest,
    ) -> GeneratedStudyPlanPersistenceResult: ...


def _utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(
        timezone.utc,
    )


class GeneratedStudyPlanService:
    """Validates generated output before persistence."""

    def __init__(
        self,
        repository: _GeneratedStudyPlanRepository,
        *,
        clock: Callable[
            [],
            datetime,
        ] = _utc_now,
    ) -> None:
        self._repository = repository
        self._clock = clock

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
    ) -> GeneratedStudyPlanPersistenceResult:
        """Persist one generated study plan and its sessions."""

        try:
            request = GeneratedStudyPlanPersistenceRequest(
                title=title,
                starts_on=starts_on,
                ends_on=ends_on,
                generated_at=self._clock(),
                sessions=tuple(
                    sessions,
                ),
            )

        except ValidationError as exc:
            raise StudyPlanValidationError(
                "Generated study-plan persistence "
                "input was invalid.",
            ) from exc

        return self._repository.persist_generated_plan(
            user_id=user_id,
            request=request,
        )