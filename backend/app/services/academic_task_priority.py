# File: /backend/app/services/academic_task_priority.py
# Purpose: Calculates deterministic academic-task priority scores
# from deadlines, workload, confidence, performance, and availability.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.schemas.academic_task import (
    AcademicTaskDifficulty,
    AcademicTaskStatus,
)

DEADLINE_WEIGHT = 30
DIFFICULTY_WEIGHT = 20
ESTIMATED_TIME_WEIGHT = 15
OUTPUT_CONFIDENCE_WEIGHT = 15
PREVIOUS_PERFORMANCE_WEIGHT = 10
AVAILABLE_STUDY_TIME_WEIGHT = 5
STATUS_WEIGHT = 5

TOTAL_PRIORITY_WEIGHT = (
    DEADLINE_WEIGHT
    + DIFFICULTY_WEIGHT
    + ESTIMATED_TIME_WEIGHT
    + OUTPUT_CONFIDENCE_WEIGHT
    + PREVIOUS_PERFORMANCE_WEIGHT
    + AVAILABLE_STUDY_TIME_WEIGHT
    + STATUS_WEIGHT
)


@dataclass(
    frozen=True,
    slots=True,
)
class AcademicTaskPriorityInput:
    """Inputs required to calculate one task's priority."""

    deadline: datetime
    estimated_minutes: int
    difficulty: AcademicTaskDifficulty
    status: AcademicTaskStatus

    output_confidence_level: float | None = None

    previous_performance_percent: float | None = None

    available_study_minutes_until_deadline: int | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class AcademicTaskPriorityResult:
    """Priority result with explainable factor scores."""

    total_score: float

    deadline_score: float
    difficulty_score: float
    estimated_time_score: float
    output_confidence_score: float
    previous_performance_score: float
    available_study_time_score: float
    status_score: float


def _validate_aware_datetime(
    value: datetime,
    *,
    field_name: str,
) -> None:
    """Require timezone-aware datetimes."""

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"{field_name} must include a timezone."
        )


def _deadline_score(
    *,
    deadline: datetime,
    now: datetime,
) -> float:
    """Score urgency based on time remaining before the deadline."""

    remaining_seconds = (
        deadline - now
    ).total_seconds()

    if remaining_seconds <= 0:
        return 100.0

    remaining_hours = (
        remaining_seconds / 3_600
    )

    if remaining_hours <= 24:
        return 100.0

    if remaining_hours <= 72:
        return 85.0

    if remaining_hours <= 168:
        return 70.0

    if remaining_hours <= 336:
        return 50.0

    if remaining_hours <= 720:
        return 25.0

    return 10.0


def _difficulty_score(
    difficulty: AcademicTaskDifficulty,
) -> float:
    """Convert task difficulty into urgency."""

    scores = {
        AcademicTaskDifficulty.EASY: 25.0,
        AcademicTaskDifficulty.MEDIUM: 60.0,
        AcademicTaskDifficulty.HARD: 100.0,
    }

    return scores[
        difficulty
    ]


def _estimated_time_score(
    estimated_minutes: int,
) -> float:
    """Score workload based on estimated completion time."""

    if estimated_minutes <= 30:
        return 20.0

    if estimated_minutes <= 60:
        return 40.0

    if estimated_minutes <= 120:
        return 60.0

    if estimated_minutes <= 240:
        return 80.0

    return 100.0


def _output_confidence_score(
    confidence_level: float | None,
) -> float:
    """Make low confidence increase task priority."""

    if confidence_level is None:
        return 50.0

    if (
        isinstance(
            confidence_level,
            bool,
        )
        or not isinstance(
            confidence_level,
            (int, float),
        )
        or not 1 <= confidence_level <= 5
    ):
        raise ValueError(
            "output_confidence_level must be between 1 and 5."
        )

    return (
        5.0
        - float(
            confidence_level,
        )
    ) * 25.0


def _previous_performance_score(
    performance_percent: float | None,
) -> float:
    """Make weaker previous performance increase priority."""

    if performance_percent is None:
        return 50.0

    if not 0 <= performance_percent <= 100:
        raise ValueError(
            "previous_performance_percent must be "
            "between 0 and 100."
        )

    return (
        100.0
        - performance_percent
    )


def _available_study_time_score(
    *,
    estimated_minutes: int,
    available_minutes: int | None,
) -> float:
    """Score scheduling pressure relative to available study time."""

    if available_minutes is None:
        return 50.0

    if available_minutes < 0:
        raise ValueError(
            "available_study_minutes_until_deadline "
            "cannot be negative."
        )

    if available_minutes == 0:
        return 100.0

    availability_ratio = (
        available_minutes
        / estimated_minutes
    )

    if availability_ratio < 1:
        return 100.0

    if availability_ratio < 1.5:
        return 80.0

    if availability_ratio < 2:
        return 60.0

    if availability_ratio < 3:
        return 40.0

    return 20.0


def _status_score(
    status: AcademicTaskStatus,
) -> float:
    """Score active workflow status."""

    scores = {
        AcademicTaskStatus.PENDING: 50.0,
        AcademicTaskStatus.IN_PROGRESS: 100.0,
        AcademicTaskStatus.COMPLETED: 0.0,
        AcademicTaskStatus.CANCELLED: 0.0,
    }

    return scores[
        status
    ]


def calculate_academic_task_priority(
    input_data: AcademicTaskPriorityInput,
    *,
    now: datetime,
) -> AcademicTaskPriorityResult:
    """Calculate an explainable deterministic priority score."""

    if TOTAL_PRIORITY_WEIGHT != 100:
        raise RuntimeError(
            "Academic-task priority weights must total 100."
        )

    _validate_aware_datetime(
        input_data.deadline,
        field_name="deadline",
    )

    _validate_aware_datetime(
        now,
        field_name="now",
    )

    if (
        isinstance(
            input_data.estimated_minutes,
            bool,
        )
        or input_data.estimated_minutes <= 0
    ):
        raise ValueError(
            "estimated_minutes must be greater than zero."
        )

    deadline_score = _deadline_score(
        deadline=input_data.deadline,
        now=now,
    )

    difficulty_score = (
        _difficulty_score(
            input_data.difficulty,
        )
    )

    estimated_time_score = (
        _estimated_time_score(
            input_data.estimated_minutes,
        )
    )

    output_confidence_score = (
        _output_confidence_score(
            input_data.output_confidence_level,
        )
    )

    previous_performance_score = (
        _previous_performance_score(
            input_data.previous_performance_percent,
        )
    )

    available_study_time_score = (
        _available_study_time_score(
            estimated_minutes=(
                input_data.estimated_minutes
            ),
            available_minutes=(
                input_data
                .available_study_minutes_until_deadline
            ),
        )
    )

    status_score = _status_score(
        input_data.status,
    )

    if input_data.status in {
        AcademicTaskStatus.COMPLETED,
        AcademicTaskStatus.CANCELLED,
    }:
        total_score = 0.0
    else:
        total_score = (
            deadline_score
            * DEADLINE_WEIGHT
            + difficulty_score
            * DIFFICULTY_WEIGHT
            + estimated_time_score
            * ESTIMATED_TIME_WEIGHT
            + output_confidence_score
            * OUTPUT_CONFIDENCE_WEIGHT
            + previous_performance_score
            * PREVIOUS_PERFORMANCE_WEIGHT
            + available_study_time_score
            * AVAILABLE_STUDY_TIME_WEIGHT
            + status_score
            * STATUS_WEIGHT
        ) / 100

    return AcademicTaskPriorityResult(
        total_score=round(
            total_score,
            1,
        ),
        deadline_score=deadline_score,
        difficulty_score=difficulty_score,
        estimated_time_score=estimated_time_score,
        output_confidence_score=output_confidence_score,
        previous_performance_score=previous_performance_score,
        available_study_time_score=available_study_time_score,
        status_score=status_score,
    )