# File: /backend/app/schemas/academic_task.py
# Purpose: Defines validated request and response contracts for
# student-owned academic tasks.

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

MAX_ACADEMIC_TASK_TITLE_CHARACTERS = 200
MAX_ACADEMIC_TASK_DESCRIPTION_CHARACTERS = 5_000

MIN_ACADEMIC_TASK_ESTIMATED_MINUTES = 1
MAX_ACADEMIC_TASK_ESTIMATED_MINUTES = 10_080


class AcademicTaskDifficulty(StrEnum):
    """Supported academic-task difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AcademicTaskType(StrEnum):
    """Supported academic-task categories."""

    ASSIGNMENT = "assignment"
    PROJECT = "project"
    EXAM = "exam"
    QUIZ = "quiz"
    READING = "reading"
    PRESENTATION = "presentation"
    RESEARCH = "research"
    OTHER = "other"


class AcademicTaskStatus(StrEnum):
    """Supported academic-task workflow states."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


_NON_NULL_UPDATE_FIELDS = frozenset(
    {
        "subject_id",
        "title",
        "deadline",
        "estimated_minutes",
        "difficulty",
        "task_type",
        "status",
    }
)


def _normalize_required_text(
    value: str,
    *,
    field_name: str,
) -> str:
    """Trim required text and reject blank values."""

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty."
        )

    return normalized


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    """Trim optional text and convert blank text to null."""

    if value is None:
        return None

    normalized = value.strip()

    return normalized or None


def _validate_timezone_aware_datetime(
    value: datetime,
    *,
    field_name: str,
) -> datetime:
    """Require an explicit timezone for persisted timestamps."""

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"{field_name} must include a timezone."
        )

    return value


class AcademicTaskCreateRequest(BaseModel):
    """Request to create one academic task."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    subject_id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_ACADEMIC_TASK_TITLE_CHARACTERS,
    )

    description: str | None = Field(
        default=None,
        max_length=MAX_ACADEMIC_TASK_DESCRIPTION_CHARACTERS,
    )

    deadline: datetime

    estimated_minutes: int = Field(
        ge=MIN_ACADEMIC_TASK_ESTIMATED_MINUTES,
        le=MAX_ACADEMIC_TASK_ESTIMATED_MINUTES,
    )

    difficulty: AcademicTaskDifficulty

    task_type: AcademicTaskType

    status: AcademicTaskStatus = (
        AcademicTaskStatus.PENDING
    )

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Trim and validate the task title."""

        return _normalize_required_text(
            value,
            field_name="title",
        )

    @field_validator(
        "description",
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize optional task description."""

        return _normalize_optional_text(
            value,
        )

    @field_validator(
        "deadline",
    )
    @classmethod
    def validate_deadline(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware deadline."""

        return _validate_timezone_aware_datetime(
            value,
            field_name="deadline",
        )


class AcademicTaskUpdateRequest(BaseModel):
    """Partial update for one academic task."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    subject_id: UUID | None = None

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_ACADEMIC_TASK_TITLE_CHARACTERS,
    )

    description: str | None = Field(
        default=None,
        max_length=MAX_ACADEMIC_TASK_DESCRIPTION_CHARACTERS,
    )

    deadline: datetime | None = None

    estimated_minutes: int | None = Field(
        default=None,
        ge=MIN_ACADEMIC_TASK_ESTIMATED_MINUTES,
        le=MAX_ACADEMIC_TASK_ESTIMATED_MINUTES,
    )

    difficulty: AcademicTaskDifficulty | None = None

    task_type: AcademicTaskType | None = None

    status: AcademicTaskStatus | None = None

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str | None,
    ) -> str | None:
        """Trim a provided task title."""

        if value is None:
            return None

        return _normalize_required_text(
            value,
            field_name="title",
        )

    @field_validator(
        "description",
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize a provided task description."""

        return _normalize_optional_text(
            value,
        )

    @field_validator(
        "deadline",
    )
    @classmethod
    def validate_deadline(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require timezone awareness when deadline is provided."""

        if value is None:
            return None

        return _validate_timezone_aware_datetime(
            value,
            field_name="deadline",
        )

    @model_validator(
        mode="after",
    )
    def validate_update_fields(
        self,
    ) -> Self:
        """Require at least one valid field to update."""

        if not self.model_fields_set:
            raise ValueError(
                "At least one academic-task field must be provided."
            )

        for field_name in _NON_NULL_UPDATE_FIELDS:
            if (
                field_name in self.model_fields_set
                and getattr(
                    self,
                    field_name,
                )
                is None
            ):
                raise ValueError(
                    f"{field_name} cannot be null."
                )

        return self

class AcademicTaskStatusUpdateRequest(BaseModel):
    """Request to change only an academic task's status."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    status: AcademicTaskStatus

class AcademicTaskResponse(BaseModel):
    """Academic task returned to its authenticated owner."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    subject_id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_ACADEMIC_TASK_TITLE_CHARACTERS,
    )

    description: str | None = Field(
        default=None,
        max_length=MAX_ACADEMIC_TASK_DESCRIPTION_CHARACTERS,
    )

    deadline: datetime

    estimated_minutes: int = Field(
        ge=MIN_ACADEMIC_TASK_ESTIMATED_MINUTES,
        le=MAX_ACADEMIC_TASK_ESTIMATED_MINUTES,
    )

    difficulty: AcademicTaskDifficulty

    task_type: AcademicTaskType

    status: AcademicTaskStatus

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
        """Trim persisted task title."""

        return _normalize_required_text(
            value,
            field_name="title",
        )

    @field_validator(
        "description",
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize persisted description."""

        return _normalize_optional_text(
            value,
        )

    @field_validator(
        "deadline",
        "created_at",
        "updated_at",
    )
    @classmethod
    def validate_timestamps(
        cls,
        value: datetime,
    ) -> datetime:
        """Require timezone-aware persisted timestamps."""

        return _validate_timezone_aware_datetime(
            value,
            field_name="timestamp",
        )


class AcademicTaskListResponse(BaseModel):
    """List of academic tasks owned by one student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    items: tuple[
        AcademicTaskResponse,
        ...,
    ] = ()


class AcademicTaskApiErrorResponse(BaseModel):
    """Safe public error returned by academic-task endpoints."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    error_code: str = Field(
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        min_length=1,
        max_length=300,
    )

    @field_validator(
        "error_code",
        "message",
    )
    @classmethod
    def normalize_error_text(
        cls,
        value: str,
    ) -> str:
        """Trim public error fields."""

        return _normalize_required_text(
            value,
            field_name="error field",
        )