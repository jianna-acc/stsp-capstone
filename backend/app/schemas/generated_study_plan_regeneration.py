# File: /backend/app/schemas/generated_study_plan_regeneration.py
# Purpose: Defines validated persistence input for replacing the
# generated sessions belonging to an existing generated study plan.

from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.schemas.study_scheduler import (
    GeneratedStudySession,
)


class GeneratedStudyPlanRegenerationRequest(
    BaseModel,
):
    """Validated replacement generated schedule."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    generated_at: datetime

    sessions: tuple[
        GeneratedStudySession,
        ...,
    ] = Field(
        min_length=1,
        max_length=500,
    )

    @field_validator(
        "generated_at",
    )
    @classmethod
    def validate_generated_at(
        cls,
        value: datetime,
    ) -> datetime:
        """Require an absolute regeneration timestamp."""

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "generated_at must include "
                "timezone information.",
            )

        return value