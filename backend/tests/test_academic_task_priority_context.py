# File: /backend/tests/test_academic_task_priority_context.py
# Purpose: Verifies output-confidence resolution and recurring
# study-availability calculations used by task prioritization.

from datetime import (
    datetime,
    time,
    timedelta,
)
from zoneinfo import ZoneInfo

import pytest

from app.schemas.academic_task import (
    AcademicTaskOutputType,
)
from app.services.academic_task_priority_context import (
    StudyAvailabilitySlot,
    calculate_available_study_minutes,
    resolve_output_confidence,
)

MANILA = ZoneInfo(
    "Asia/Manila",
)

MONDAY = datetime(
    2026,
    8,
    10,
    17,
    0,
    tzinfo=MANILA,
)


def confidence_levels() -> dict[
    str,
    int,
]:
    """Return all seven saved output-confidence ratings."""

    return {
        "writing": 1,
        "computation": 2,
        "research": 3,
        "presentation": 4,
        "creative": 5,
        "reading_analysis": 2,
        "memorization": 4,
    }


def test_direct_output_uses_matching_confidence() -> None:
    """A specific task output should use its matching rating."""

    result = resolve_output_confidence(
        output_type=(
            AcademicTaskOutputType.COMPUTATION
        ),
        confidence_levels=(
            confidence_levels()
        ),
    )

    assert result == 2.0


def test_other_output_uses_neutral_fallback() -> None:
    """Unclassified work should not invent a confidence rating."""

    result = resolve_output_confidence(
        output_type=(
            AcademicTaskOutputType.OTHER
        ),
        confidence_levels=(
            confidence_levels()
        ),
    )

    assert result is None


def test_mixed_output_uses_average_confidence() -> None:
    """Mixed work should combine all supported output ratings."""

    result = resolve_output_confidence(
        output_type=(
            AcademicTaskOutputType.MIXED
        ),
        confidence_levels=(
            confidence_levels()
        ),
    )

    assert result == 3.0


def test_incomplete_mixed_confidence_uses_neutral_fallback() -> None:
    """Missing mixed-output context should remain neutral."""

    levels = confidence_levels()

    levels.pop(
        "writing",
    )

    result = resolve_output_confidence(
        output_type=(
            AcademicTaskOutputType.MIXED
        ),
        confidence_levels=levels,
    )

    assert result is None


@pytest.mark.parametrize(
    "invalid_level",
    [
        0,
        6,
    ],
)
def test_invalid_saved_confidence_is_rejected(
    invalid_level: int,
) -> None:
    """Malformed confidence data must not silently affect priority."""

    levels = confidence_levels()

    levels[
        "writing"
    ] = invalid_level

    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        resolve_output_confidence(
            output_type=(
                AcademicTaskOutputType.WRITING
            ),
            confidence_levels=levels,
        )


def test_same_day_availability_is_clipped_to_now() -> None:
    """Elapsed portions of today's slot should not be counted."""

    result = calculate_available_study_minutes(
        slots=[
            StudyAvailabilitySlot(
                day_of_week=1,
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    20,
                    0,
                ),
            ),
        ],
        now=MONDAY.replace(
            hour=19,
        ),
        deadline=MONDAY.replace(
            hour=21,
        ),
        timezone_name="Asia/Manila",
    )

    assert result == 60


def test_deadline_clips_final_availability_slot() -> None:
    """Study time after the task deadline must not be counted."""

    result = calculate_available_study_minutes(
        slots=[
            StudyAvailabilitySlot(
                day_of_week=1,
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    20,
                    0,
                ),
            ),
        ],
        now=MONDAY,
        deadline=MONDAY.replace(
            hour=19,
        ),
        timezone_name="Asia/Manila",
    )

    assert result == 60


def test_recurring_weekly_availability_is_counted() -> None:
    """Recurring slots should be counted until the deadline."""

    result = calculate_available_study_minutes(
        slots=[
            StudyAvailabilitySlot(
                day_of_week=1,
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    20,
                    0,
                ),
            ),
            StudyAvailabilitySlot(
                day_of_week=3,
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    19,
                    0,
                ),
            ),
        ],
        now=MONDAY,
        deadline=(
            MONDAY
            + timedelta(
                days=7,
                hours=4,
            )
        ),
        timezone_name="Asia/Manila",
    )

    # First Monday: 120
    # Wednesday: 60
    # Following Monday: 120
    assert result == 300


def test_unmatched_weekday_is_not_counted() -> None:
    """Slots on weekdays outside the period should contribute zero."""

    result = calculate_available_study_minutes(
        slots=[
            StudyAvailabilitySlot(
                day_of_week=3,
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    19,
                    0,
                ),
            ),
        ],
        now=MONDAY,
        deadline=MONDAY.replace(
            hour=21,
        ),
        timezone_name="Asia/Manila",
    )

    assert result == 0


def test_deadline_before_now_has_no_available_time() -> None:
    """Past deadlines have no remaining study availability."""

    result = calculate_available_study_minutes(
        slots=[],
        now=MONDAY,
        deadline=(
            MONDAY
            - timedelta(
                minutes=1,
            )
        ),
        timezone_name="Asia/Manila",
    )

    assert result == 0


def test_overlapping_slots_are_rejected() -> None:
    """Malformed overlapping availability must not be double-counted."""

    with pytest.raises(
        ValueError,
        match="overlap",
    ):
        calculate_available_study_minutes(
            slots=[
                StudyAvailabilitySlot(
                    day_of_week=1,
                    start_time=time(
                        18,
                        0,
                    ),
                    end_time=time(
                        20,
                        0,
                    ),
                ),
                StudyAvailabilitySlot(
                    day_of_week=1,
                    start_time=time(
                        19,
                        0,
                    ),
                    end_time=time(
                        21,
                        0,
                    ),
                ),
            ],
            now=MONDAY,
            deadline=MONDAY.replace(
                hour=22,
            ),
            timezone_name="Asia/Manila",
        )


def test_invalid_timezone_is_rejected() -> None:
    """Availability must use a valid IANA timezone."""

    with pytest.raises(
        ValueError,
        match="IANA timezone",
    ):
        calculate_available_study_minutes(
            slots=[],
            now=MONDAY,
            deadline=(
                MONDAY
                + timedelta(
                    days=1,
                )
            ),
            timezone_name="Mars/Manila",
        )