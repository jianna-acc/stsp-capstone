# File: /backend/app/schemas/study_scheduler.py
# Purpose: Defines Track D's generic scheduling contracts so the
# scheduler remains independent of unfinished Academic Tasks work.

from __future__ import annotations

from datetime import (
    date,
    datetime,
    time,
)
from itertools import pairwise
from typing import Self
from uuid import UUID
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

MAX_SCHEDULER_TASK_TITLE_CHARACTERS = 200
MAX_SCHEDULER_TIMEZONE_CHARACTERS = 100

MAX_SCHEDULER_TASKS = 500
MAX_SCHEDULER_AVAILABILITY_SLOTS = 30
MAX_SCHEDULER_PLAN_SPAN_DAYS = 366

MIN_TASK_ESTIMATE_MINUTES = 5
MAX_TASK_ESTIMATE_MINUTES = 10_080

MIN_SESSION_MINUTES = 5
MAX_SESSION_MINUTES = 240


class SchedulableTask(BaseModel):
    """One generic academic workload item accepted by Track D."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    task_id: UUID

    subject_id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_SCHEDULER_TASK_TITLE_CHARACTERS,
    )

    deadline: datetime

    estimated_minutes: int = Field(
        ge=MIN_TASK_ESTIMATE_MINUTES,
        le=MAX_TASK_ESTIMATE_MINUTES,
    )

    priority_weight: int = Field(
        default=3,
        ge=1,
        le=5,
    )

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        """Trim task titles before scheduling."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Schedulable task title must not be empty.",
            )

        return normalized

    @field_validator(
        "deadline",
    )
    @classmethod
    def validate_deadline(
        cls,
        value: datetime,
    ) -> datetime:
        """Require an absolute timezone-aware task deadline."""

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "Task deadline must include "
                "timezone information.",
            )

        return value


class SchedulerAvailabilitySlot(BaseModel):
    """One recurring weekly period available to the scheduler."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    day_of_week: int = Field(
        ge=1,
        le=7,
    )

    start_time: time

    end_time: time

    @model_validator(
        mode="after",
    )
    def validate_time_order(
        self,
    ) -> Self:
        """Require a positive local-time availability period."""

        if self.start_time >= self.end_time:
            raise ValueError(
                "Availability end time must be "
                "after its start time.",
            )

        return self


class SchedulerPreferences(BaseModel):
    """Student preferences used when dividing available time."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    timezone: str = Field(
        default="Asia/Manila",
        min_length=1,
        max_length=MAX_SCHEDULER_TIMEZONE_CHARACTERS,
    )

    preferred_session_minutes: int = Field(
        default=60,
        ge=10,
        le=MAX_SESSION_MINUTES,
    )

    minimum_session_minutes: int = Field(
        default=15,
        ge=MIN_SESSION_MINUTES,
        le=120,
    )

    @field_validator(
        "timezone",
    )
    @classmethod
    def validate_timezone(
        cls,
        value: str,
    ) -> str:
        """Normalize and validate one IANA timezone."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Scheduler timezone must not be empty.",
            )

        try:
            ZoneInfo(
                normalized,
            )
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                "Scheduler timezone must be a valid "
                "IANA timezone.",
            ) from exc

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_session_lengths(
        self,
    ) -> Self:
        """Keep minimum sessions within the preferred duration."""

        if (
            self.minimum_session_minutes
            > self.preferred_session_minutes
        ):
            raise ValueError(
                "Minimum session duration cannot exceed "
                "the preferred session duration.",
            )

        return self


class StudyScheduleRequest(BaseModel):
    """Complete independent input to the Track D scheduler."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    starts_on: date

    ends_on: date

    tasks: tuple[
        SchedulableTask,
        ...,
    ] = Field(
        min_length=1,
        max_length=MAX_SCHEDULER_TASKS,
    )

    availability: tuple[
        SchedulerAvailabilitySlot,
        ...,
    ] = Field(
        min_length=1,
        max_length=MAX_SCHEDULER_AVAILABILITY_SLOTS,
    )

    preferences: SchedulerPreferences = Field(
        default_factory=SchedulerPreferences,
    )

    @model_validator(
        mode="after",
    )
    def validate_request(
        self,
    ) -> Self:
        """Validate date span and recurring availability overlaps."""

        span_days = (
            self.ends_on
            - self.starts_on
        ).days

        if span_days < 0:
            raise ValueError(
                "Schedule end date cannot be before "
                "its start date.",
            )

        if (
            span_days
            > MAX_SCHEDULER_PLAN_SPAN_DAYS
        ):
            raise ValueError(
                "Schedule date range cannot exceed "
                "366 days.",
            )

        slots_by_day: dict[
            int,
            list[
                SchedulerAvailabilitySlot
            ],
        ] = {}

        for slot in self.availability:
            slots_by_day.setdefault(
                slot.day_of_week,
                [],
            ).append(
                slot,
            )

        for slots in slots_by_day.values():
            ordered_slots = sorted(
                slots,
                key=lambda slot: (
                    slot.start_time,
                    slot.end_time,
                ),
            )

            for previous, current in pairwise(
                ordered_slots,
            ):
                if (
                    current.start_time
                    < previous.end_time
                ):
                    raise ValueError(
                        "Scheduler availability periods "
                        "cannot overlap.",
                    )

        return self


class GeneratedStudySession(BaseModel):
    """One session proposed by the deterministic scheduler."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    task_id: UUID

    subject_id: UUID

    title: str = Field(
        min_length=1,
        max_length=MAX_SCHEDULER_TASK_TITLE_CHARACTERS,
    )

    starts_at: datetime

    ends_at: datetime

    duration_minutes: int = Field(
        ge=1,
        le=MAX_SESSION_MINUTES,
    )


class UnscheduledTask(BaseModel):
    """Remaining workload that could not fit before its deadline."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    task_id: UUID

    remaining_minutes: int = Field(
        ge=1,
        le=MAX_TASK_ESTIMATE_MINUTES,
    )


class StudyScheduleResult(BaseModel):
    """Complete deterministic scheduling result."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    sessions: tuple[
        GeneratedStudySession,
        ...,
    ] = ()

    unscheduled_tasks: tuple[
        UnscheduledTask,
        ...,
    ] = ()