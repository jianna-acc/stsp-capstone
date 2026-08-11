# File: /backend/app/schemas/study_plan.py
# Purpose: Defines validated API and persistence contracts for
# student study plans and scheduled study sessions.

from __future__ import annotations

from datetime import (
    date,
    datetime,
)
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

MAX_STUDY_PLAN_TITLE_CHARACTERS = 160
MAX_STUDY_SESSION_TITLE_CHARACTERS = 160
MAX_STUDY_SESSION_NOTES_CHARACTERS = 2_000

MAX_STUDY_PLAN_SPAN_DAYS = 366
MAX_STUDY_SESSION_DURATION_SECONDS = (
    8 * 60 * 60
)


class StudyPlanStatus(StrEnum):
    """Supported lifecycle states for study plans."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class StudyPlanGenerationMode(StrEnum):
    """Supported sources of study-plan creation."""

    MANUAL = "manual"
    GENERATED = "generated"


class StudySessionStatus(StrEnum):
    """Supported progress states for study sessions."""

    PLANNED = "planned"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class StudySessionOrigin(StrEnum):
    """Supported origins for scheduled study sessions."""

    MANUAL = "manual"
    GENERATED = "generated"


class StudyPlanCreateRequest(BaseModel):
    """Request to create one manual study plan."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    title: str = Field(
        min_length=1,
        max_length=MAX_STUDY_PLAN_TITLE_CHARACTERS,
    )

    starts_on: date

    ends_on: date

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Trim and validate the plan title."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Study-plan title must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_date_range(
        self,
    ) -> Self:
        """Keep study-plan dates ordered and reasonably bounded."""

        date_span = (
            self.ends_on
            - self.starts_on
        ).days

        if date_span < 0:
            raise ValueError(
                "Study-plan end date cannot be "
                "before its start date.",
            )

        if (
            date_span
            > MAX_STUDY_PLAN_SPAN_DAYS
        ):
            raise ValueError(
                "Study-plan date range cannot "
                "exceed 366 days.",
            )

        return self


class StudyPlanResponse(BaseModel):
    """Persisted study plan returned to its owner."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_STUDY_PLAN_TITLE_CHARACTERS,
    )

    starts_on: date

    ends_on: date

    status: StudyPlanStatus

    generation_mode: StudyPlanGenerationMode

    generated_at: datetime | None = None

    created_at: datetime

    updated_at: datetime

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Trim persisted plan titles."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Study-plan title must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_plan(
        self,
    ) -> Self:
        """Validate persisted plan dates and generation metadata."""

        date_span = (
            self.ends_on
            - self.starts_on
        ).days

        if date_span < 0:
            raise ValueError(
                "Study-plan end date cannot be "
                "before its start date.",
            )

        if (
            date_span
            > MAX_STUDY_PLAN_SPAN_DAYS
        ):
            raise ValueError(
                "Study-plan date range cannot "
                "exceed 366 days.",
            )

        if (
            self.generation_mode
            == StudyPlanGenerationMode.MANUAL
            and self.generated_at is not None
        ):
            raise ValueError(
                "Manual study plans cannot have "
                "generated_at.",
            )

        if (
            self.generation_mode
            == StudyPlanGenerationMode.GENERATED
            and self.generated_at is None
        ):
            raise ValueError(
                "Generated study plans require "
                "generated_at.",
            )

        return self


class StudyPlanListResponse(BaseModel):
    """List of study plans belonging to one student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    items: tuple[
        StudyPlanResponse,
        ...,
    ] = ()


class StudySessionCreateRequest(BaseModel):
    """Request to manually add one scheduled study session."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    subject_id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_STUDY_SESSION_TITLE_CHARACTERS,
    )

    starts_at: datetime

    ends_at: datetime

    notes: str | None = Field(
        default=None,
        max_length=MAX_STUDY_SESSION_NOTES_CHARACTERS,
    )

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Trim the session title."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Study-session title must not be empty.",
            )

        return normalized

    @field_validator(
        "notes",
    )
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        """Trim optional notes and convert blank notes to null."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @model_validator(
        mode="after",
    )
    def validate_schedule(
        self,
    ) -> Self:
        """Require timezone-aware, ordered session timestamps."""

        _validate_session_schedule(
            starts_at=self.starts_at,
            ends_at=self.ends_at,
        )

        return self


class StudySessionResponse(BaseModel):
    """Persisted study session returned to its owner."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    study_plan_id: UUID

    subject_id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_STUDY_SESSION_TITLE_CHARACTERS,
    )

    starts_at: datetime

    ends_at: datetime

    status: StudySessionStatus

    origin: StudySessionOrigin

    notes: str | None = Field(
        default=None,
        max_length=MAX_STUDY_SESSION_NOTES_CHARACTERS,
    )

    created_at: datetime

    updated_at: datetime

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Trim persisted study-session titles."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Study-session title must not be empty.",
            )

        return normalized

    @field_validator(
        "notes",
    )
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize optional persisted session notes."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @model_validator(
        mode="after",
    )
    def validate_schedule(
        self,
    ) -> Self:
        """Validate persisted session timestamps."""

        _validate_session_schedule(
            starts_at=self.starts_at,
            ends_at=self.ends_at,
        )

        return self


class StudySessionListResponse(BaseModel):
    """List of sessions belonging to one study plan."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    items: tuple[
        StudySessionResponse,
        ...,
    ] = ()


def _validate_session_schedule(
    *,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    """Validate timezone awareness, order, and maximum duration."""

    if (
        starts_at.tzinfo is None
        or starts_at.utcoffset() is None
        or ends_at.tzinfo is None
        or ends_at.utcoffset() is None
    ):
        raise ValueError(
            "Study-session timestamps must "
            "include timezone information.",
        )

    if starts_at >= ends_at:
        raise ValueError(
            "Study-session end time must be "
            "after its start time.",
        )

    duration_seconds = (
        ends_at
        - starts_at
    ).total_seconds()

    if (
        duration_seconds
        > MAX_STUDY_SESSION_DURATION_SECONDS
    ):
        raise ValueError(
            "Study sessions cannot exceed "
            "8 hours.",
        )