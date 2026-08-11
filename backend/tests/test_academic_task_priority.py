# File: /backend/tests/test_academic_task_priority.py
# Purpose: Verifies deterministic and explainable academic-task
# priority scoring.

from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.academic_task import (
    AcademicTaskDifficulty,
    AcademicTaskStatus,
)
from app.services.academic_task_priority import (
    TOTAL_PRIORITY_WEIGHT,
    AcademicTaskPriorityInput,
    calculate_academic_task_priority,
)

NOW = datetime(
    2026,
    8,
    9,
    9,
    0,
    tzinfo=UTC,
)


def make_input(
    *,
    deadline: datetime | None = None,
    estimated_minutes: int = 120,
    difficulty: AcademicTaskDifficulty = (
        AcademicTaskDifficulty.MEDIUM
    ),
    status: AcademicTaskStatus = (
        AcademicTaskStatus.PENDING
    ),
    confidence: float | None = 3,
    performance: float | None = None,
    available_minutes: int | None = 240,
) -> AcademicTaskPriorityInput:
    """Return a reusable valid priority input."""

    return AcademicTaskPriorityInput(
        deadline=(
            deadline
            if deadline is not None
            else NOW
            + timedelta(
                days=7,
            )
        ),
        estimated_minutes=estimated_minutes,
        difficulty=difficulty,
        status=status,
        output_confidence_level=confidence,
        previous_performance_percent=performance,
        available_study_minutes_until_deadline=(
            available_minutes
        ),
    )


def test_priority_weights_total_one_hundred() -> None:
    """Priority weights must remain normalized."""

    assert TOTAL_PRIORITY_WEIGHT == 100


def test_nearer_deadline_increases_priority() -> None:
    """Tasks due sooner should receive greater urgency."""

    soon = calculate_academic_task_priority(
        make_input(
            deadline=NOW
            + timedelta(
                hours=12,
            ),
        ),
        now=NOW,
    )

    later = calculate_academic_task_priority(
        make_input(
            deadline=NOW
            + timedelta(
                days=40,
            ),
        ),
        now=NOW,
    )

    assert (
        soon.total_score
        > later.total_score
    )


def test_harder_task_increases_priority() -> None:
    """Hard tasks should outrank otherwise equal easy tasks."""

    hard = calculate_academic_task_priority(
        make_input(
            difficulty=AcademicTaskDifficulty.HARD,
        ),
        now=NOW,
    )

    easy = calculate_academic_task_priority(
        make_input(
            difficulty=AcademicTaskDifficulty.EASY,
        ),
        now=NOW,
    )

    assert (
        hard.total_score
        > easy.total_score
    )


def test_longer_task_increases_priority() -> None:
    """Longer workloads should receive more planning urgency."""

    long_task = calculate_academic_task_priority(
        make_input(
            estimated_minutes=300,
            available_minutes=900,
        ),
        now=NOW,
    )

    short_task = calculate_academic_task_priority(
        make_input(
            estimated_minutes=30,
            available_minutes=90,
        ),
        now=NOW,
    )

    assert (
        long_task.total_score
        > short_task.total_score
    )


def test_low_output_confidence_increases_priority() -> None:
    """Low confidence should increase support urgency."""

    low_confidence = (
        calculate_academic_task_priority(
            make_input(
                confidence=1,
            ),
            now=NOW,
        )
    )

    high_confidence = (
        calculate_academic_task_priority(
            make_input(
                confidence=5,
            ),
            now=NOW,
        )
    )

    assert (
        low_confidence.total_score
        > high_confidence.total_score
    )


def test_low_previous_performance_increases_priority() -> None:
    """Weak previous performance should raise priority."""

    weak_performance = (
        calculate_academic_task_priority(
            make_input(
                performance=30,
            ),
            now=NOW,
        )
    )

    strong_performance = (
        calculate_academic_task_priority(
            make_input(
                performance=90,
            ),
            now=NOW,
        )
    )

    assert (
        weak_performance.total_score
        > strong_performance.total_score
    )


def test_limited_availability_increases_priority() -> None:
    """Insufficient study time should increase scheduling pressure."""

    limited = calculate_academic_task_priority(
        make_input(
            estimated_minutes=120,
            available_minutes=60,
        ),
        now=NOW,
    )

    ample = calculate_academic_task_priority(
        make_input(
            estimated_minutes=120,
            available_minutes=500,
        ),
        now=NOW,
    )

    assert (
        limited.total_score
        > ample.total_score
    )


def test_in_progress_task_gets_status_boost() -> None:
    """In-progress work should receive a small continuation boost."""

    in_progress = (
        calculate_academic_task_priority(
            make_input(
                status=AcademicTaskStatus.IN_PROGRESS,
            ),
            now=NOW,
        )
    )

    pending = (
        calculate_academic_task_priority(
            make_input(
                status=AcademicTaskStatus.PENDING,
            ),
            now=NOW,
        )
    )

    assert (
        in_progress.total_score
        > pending.total_score
    )


@pytest.mark.parametrize(
    "status",
    [
        AcademicTaskStatus.COMPLETED,
        AcademicTaskStatus.CANCELLED,
    ],
)
def test_inactive_task_has_zero_priority(
    status: AcademicTaskStatus,
) -> None:
    """Completed or cancelled tasks leave the active queue."""

    result = calculate_academic_task_priority(
        make_input(
            status=status,
        ),
        now=NOW,
    )

    assert result.total_score == 0.0


def test_missing_optional_history_uses_neutral_scores() -> None:
    """Unavailable historical inputs should not break scoring."""

    result = calculate_academic_task_priority(
        make_input(
            confidence=None,
            performance=None,
            available_minutes=None,
        ),
        now=NOW,
    )

    assert (
        result.output_confidence_score
        == 50.0
    )

    assert (
        result.previous_performance_score
        == 50.0
    )

    assert (
        result.available_study_time_score
        == 50.0
    )


@pytest.mark.parametrize(
    "confidence",
    [
        0,
        6,
    ],
)
def test_invalid_confidence_is_rejected(
    confidence: int,
) -> None:
    """Output confidence must remain within onboarding bounds."""

    with pytest.raises(
        ValueError,
        match="output_confidence_level",
    ):
        calculate_academic_task_priority(
            make_input(
                confidence=confidence,
            ),
            now=NOW,
        )


@pytest.mark.parametrize(
    "performance",
    [
        -1.0,
        101.0,
    ],
)
def test_invalid_performance_is_rejected(
    performance: float,
) -> None:
    """Performance percentages must remain bounded."""

    with pytest.raises(
        ValueError,
        match="previous_performance_percent",
    ):
        calculate_academic_task_priority(
            make_input(
                performance=performance,
            ),
            now=NOW,
        )


def test_negative_availability_is_rejected() -> None:
    """Study availability cannot contain negative minutes."""

    with pytest.raises(
        ValueError,
        match="available_study_minutes",
    ):
        calculate_academic_task_priority(
            make_input(
                available_minutes=-1,
            ),
            now=NOW,
        )

def test_fractional_confidence_is_supported() -> None:
    """Mixed-output averages should retain their precision."""

    result = calculate_academic_task_priority(
        make_input(
            confidence=2.5,
        ),
        now=NOW,
    )

    assert (
        result.output_confidence_score
        == 62.5
    )