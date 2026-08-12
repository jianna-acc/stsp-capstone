# File: /backend/app/schemas/study_activity.py
# Purpose: Defines validated contracts for actual timer-recorded
# student study activity.

from __future__ import annotations

from datetime import datetime
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

MAX_STUDY_ACTIVITY_TITLE_CHARACTERS = 160
DEFAULT_STUDY_BREAK_MINUTES = 5
MIN_STUDY_BREAK_MINUTES = 1
MAX_STUDY_BREAK_MINUTES = 180


class StudyActivityStatus(StrEnum):
    """Supported lifecycle states for one study timer."""

    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class StudyActivityMode(StrEnum):
    """Supported running timer modes."""

    FOCUS = "focus"
    BREAK = "break"


class StudyActivityTransitionAction(StrEnum):
    """Trusted timer transitions executed by the backend."""

    PAUSE = "pause"
    RESUME = "resume"
    START_BREAK = "start_break"
    END_BREAK = "end_break"
    COMPLETE = "complete"


class StudyActivityStartRequest(BaseModel):
    """Request to begin one actual study timer."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    subject_id: UUID | None = None

    title: str | None = Field(
        default=None,
        max_length=MAX_STUDY_ACTIVITY_TITLE_CHARACTERS,
    )

    study_plan_id: UUID | None = None

    study_session_id: UUID | None = None

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize an optional free-study title."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @model_validator(
        mode="after",
    )
    def validate_start_target(
        self,
    ) -> Self:
        """Require explicit subject/title when not using a scheduled session."""

        if self.study_session_id is None:
            if self.subject_id is None:
                raise ValueError(
                    "Free study activity requires a subject.",
                )

            if self.title is None:
                raise ValueError(
                    "Free study activity requires a title.",
                )

        return self


class StudyActivityBreakStartRequest(BaseModel):
    """Request to start a timed break."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    duration_minutes: int = Field(
        default=DEFAULT_STUDY_BREAK_MINUTES,
        ge=MIN_STUDY_BREAK_MINUTES,
        le=MAX_STUDY_BREAK_MINUTES,
    )


class StudyActivityResponse(BaseModel):
    """Persisted actual study timer returned to its owner."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    subject_id: UUID | None = None

    study_plan_id: UUID | None = None

    study_session_id: UUID | None = None

    title: str = Field(
        min_length=1,
        max_length=MAX_STUDY_ACTIVITY_TITLE_CHARACTERS,
    )

    status: StudyActivityStatus

    mode: StudyActivityMode

    started_at: datetime

    ended_at: datetime | None = None

    segment_started_at: datetime | None = None

    break_ends_at: datetime | None = None

    focus_seconds: int = Field(
        ge=0,
    )

    break_seconds: int = Field(
        ge=0,
    )

    created_at: datetime

    updated_at: datetime

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_persisted_title(
        cls,
        value: str,
    ) -> str:
        """Trim persisted timer titles."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Study activity title must not be empty.",
            )

        return normalized

    @field_validator(
        "started_at",
        "ended_at",
        "segment_started_at",
        "break_ends_at",
        "created_at",
        "updated_at",
    )
    @classmethod
    def require_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require persisted timestamps to be timezone-aware."""

        if value is None:
            return None

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "Study activity timestamps must include timezone information.",
            )

        return value

    @model_validator(
        mode="after",
    )
    def validate_state(
        self,
    ) -> Self:
        """Protect timer lifecycle consistency in API responses."""

        if self.status is StudyActivityStatus.RUNNING:
            if (
                self.ended_at is not None
                or self.segment_started_at is None
            ):
                raise ValueError(
                    "Running study activity state is invalid.",
                )

            if self.mode is StudyActivityMode.BREAK:
                if self.break_ends_at is None:
                    raise ValueError(
                        "Running break state requires a break deadline.",
                    )
            elif self.break_ends_at is not None:
                raise ValueError(
                    "Running focus state cannot have a break deadline.",
                )

        elif self.status is StudyActivityStatus.PAUSED:
            if (
                self.mode is not StudyActivityMode.FOCUS
                or self.ended_at is not None
                or self.segment_started_at is not None
                or self.break_ends_at is not None
            ):
                raise ValueError(
                    "Paused study activity state is invalid.",
                )

        else:
            if (
                self.mode is not StudyActivityMode.FOCUS
                or self.ended_at is None
                or self.segment_started_at is not None
                or self.break_ends_at is not None
            ):
                raise ValueError(
                    "Completed study activity state is invalid.",
                )

        return self


class StudyActivityApiErrorResponse(BaseModel):
    """Controlled Study Activity API error."""

    error_code: str
    message: str