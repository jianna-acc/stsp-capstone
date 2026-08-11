# File: /backend/app/services/generated_study_plan_regeneration_service.py
# Purpose: Validates generated replacement schedules before
# transactional persistence on an existing generated study plan.

from __future__ import annotations

from collections.abc import (
    Callable,
    Sequence,
)
from datetime import (
    datetime,
    timezone,
)
from typing import Protocol
from uuid import UUID

from pydantic import ValidationError

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.generated_study_plan_regeneration import (
    GeneratedStudyPlanRegenerationRequest,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)


class _GeneratedStudyPlanRegenerationRepository(
    Protocol,
):
    def replace_generated_schedule(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request:
            GeneratedStudyPlanRegenerationRequest,
    ) -> GeneratedStudyPlanPersistenceResult: ...


def _utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(
        timezone.utc,
    )


class GeneratedStudyPlanRegenerationService:
    """Validates and persists a replacement generated schedule."""

    def __init__(
        self,
        repository:
            _GeneratedStudyPlanRegenerationRepository,
        *,
        clock: Callable[
            [],
            datetime,
        ] = _utc_now,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def replace_generated_schedule(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        sessions: Sequence[
            GeneratedStudySession
        ],
    ) -> GeneratedStudyPlanPersistenceResult:
        """Replace generated sessions on one generated plan."""

        try:
            request = (
                GeneratedStudyPlanRegenerationRequest(
                    generated_at=(
                        self._clock()
                    ),
                    sessions=tuple(
                        sessions,
                    ),
                )
            )

        except ValidationError as exc:
            raise StudyPlanValidationError(
                "Generated study-plan regeneration "
                "input was invalid.",
            ) from exc

        return (
            self._repository
            .replace_generated_schedule(
                user_id=user_id,
                study_plan_id=study_plan_id,
                request=request,
            )
        )