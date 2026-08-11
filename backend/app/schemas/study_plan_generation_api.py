# File: /backend/app/schemas/study_plan_generation_api.py
# Purpose: Defines the Track D API contract for generating and
# persisting a study plan from generic schedulable tasks.

from __future__ import annotations

from datetime import date
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.study_plan import (
    StudyPlanResponse,
    StudySessionResponse,
)
from app.schemas.study_scheduler import (
    SchedulableTask,
    UnscheduledTask,
)


class StudyPlanGenerationRequest(BaseModel):
    """Authenticated request to generate and save a study plan."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    title: str = Field(
        min_length=1,
        max_length=160,
    )

    starts_on: date
    ends_on: date

    tasks: tuple[
        SchedulableTask,
        ...,
    ] = Field(
        min_length=1,
        max_length=500,
    )

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Normalize user-visible plan title."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "title must contain visible characters",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_date_range(
        self,
    ) -> Self:
        """Validate the requested study-plan date range."""

        if self.ends_on < self.starts_on:
            raise ValueError(
                "ends_on must not be before starts_on",
            )

        if (
            self.ends_on
            - self.starts_on
        ).days > 366:
            raise ValueError(
                "study plan cannot exceed 366 days",
            )

        return self

class StudyPlanRegenerationRequest(BaseModel):
    """Request to rebuild one existing generated study plan."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    tasks: tuple[
        SchedulableTask,
        ...,
    ] = Field(
        min_length=1,
        max_length=500,
    )

class StudyPlanGenerationResponse(BaseModel):
    """Saved generated plan plus any remaining unscheduled work."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    plan: StudyPlanResponse

    sessions: tuple[
        StudySessionResponse,
        ...,
    ]

    unscheduled_tasks: tuple[
        UnscheduledTask,
        ...,
    ]