# File: /backend/app/schemas/generated_study_plan.py
# Purpose: Defines the internal Track D contract used when
# persisting a generated study plan and its generated sessions.

from __future__ import annotations

from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.schemas.study_plan import (
    StudyPlanResponse,
    StudySessionResponse,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)


class GeneratedStudyPlanPersistenceRequest(BaseModel):
    """Validated generated plan ready for persistence."""

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

    generated_at: datetime

    sessions: tuple[
        GeneratedStudySession,
        ...,
    ] = Field(
        min_length=1,
        max_length=500,
    )

    @model_validator(
        mode="after",
    )
    def validate_generated_plan(
        self,
    ) -> GeneratedStudyPlanPersistenceRequest:
        """Validate plan range and generated-session boundaries."""

        normalized_title = self.title.strip()

        if not normalized_title:
            raise ValueError(
                "title must contain visible characters",
            )

        if self.generated_at.tzinfo is None:
            raise ValueError(
                "generated_at must include timezone information",
            )

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

        for session in self.sessions:
            session_start = session.starts_at.date()
            session_end = session.ends_at.date()

            if (
                session_start < self.starts_on
                or session_end > self.ends_on
            ):
                raise ValueError(
                    "generated session must fall "
                    "inside the study-plan range",
                )

        object.__setattr__(
            self,
            "title",
            normalized_title,
        )

        return self


class GeneratedStudyPlanPersistenceResult(BaseModel):
    """Persisted generated plan and its sessions."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    plan: StudyPlanResponse

    sessions: tuple[
        StudySessionResponse,
        ...,
    ]