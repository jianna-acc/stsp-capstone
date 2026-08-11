# File: /backend/tests/test_study_scheduler_schemas.py
# Purpose: Verifies validation for Track D's generic scheduler
# contracts without depending on Academic Tasks.

from datetime import (
    date,
    datetime,
    time,
    timezone,
)
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.study_scheduler import (
    SchedulableTask,
    SchedulerAvailabilitySlot,
    SchedulerPreferences,
    StudyScheduleRequest,
)


def _task() -> SchedulableTask:
    return SchedulableTask(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="  Review Chapter 4  ",
        deadline=datetime(
            2026,
            8,
            15,
            17,
            0,
            tzinfo=timezone.utc,
        ),
        estimated_minutes=120,
        priority_weight=4,
    )


def _availability() -> (
    SchedulerAvailabilitySlot
):
    return SchedulerAvailabilitySlot(
        day_of_week=1,
        start_time=time(
            18,
            0,
        ),
        end_time=time(
            20,
            0,
        ),
    )


def test_schedulable_task_normalizes_title() -> None:
    """Generic task titles should be normalized."""

    task = _task()

    assert task.title == "Review Chapter 4"


def test_schedulable_task_requires_aware_deadline() -> None:
    """Scheduler task deadlines must be absolute."""

    aware_deadline = datetime(
        2026,
        8,
        15,
        17,
        0,
        tzinfo=timezone.utc,
    )

    naive_deadline = (
        aware_deadline.replace(
            tzinfo=None,
        )
    )

    with pytest.raises(
        ValidationError,
    ):
        SchedulableTask(
            task_id=uuid4(),
            subject_id=uuid4(),
            title="Review",
            deadline=naive_deadline,
            estimated_minutes=60,
        )


def test_availability_rejects_reversed_time() -> None:
    """Recurring availability must have positive duration."""

    with pytest.raises(
        ValidationError,
    ):
        SchedulerAvailabilitySlot(
            day_of_week=1,
            start_time=time(
                20,
                0,
            ),
            end_time=time(
                18,
                0,
            ),
        )


def test_preferences_validate_timezone() -> None:
    """Valid IANA timezones should be accepted."""

    preferences = SchedulerPreferences(
        timezone="Asia/Manila",
        preferred_session_minutes=60,
        minimum_session_minutes=15,
    )

    assert (
        preferences.timezone
        == "Asia/Manila"
    )


def test_preferences_reject_invalid_timezone() -> None:
    """Invalid timezone names must fail validation."""

    with pytest.raises(
        ValidationError,
    ):
        SchedulerPreferences(
            timezone="Not/A-Timezone",
        )


def test_preferences_reject_minimum_above_preferred() -> None:
    """Minimum session size cannot exceed preference."""

    with pytest.raises(
        ValidationError,
    ):
        SchedulerPreferences(
            preferred_session_minutes=30,
            minimum_session_minutes=45,
        )


def test_schedule_rejects_overlapping_availability() -> None:
    """The scheduler should protect against overlapping periods."""

    with pytest.raises(
        ValidationError,
    ):
        StudyScheduleRequest(
            starts_on=date(
                2026,
                8,
                10,
            ),
            ends_on=date(
                2026,
                8,
                10,
            ),
            tasks=(
                _task(),
            ),
            availability=(
                SchedulerAvailabilitySlot(
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
                SchedulerAvailabilitySlot(
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
            ),
        )


def test_schedule_accepts_independent_contract() -> None:
    """Track D can build a request with no Track C types."""

    request = StudyScheduleRequest(
        starts_on=date(
            2026,
            8,
            10,
        ),
        ends_on=date(
            2026,
            8,
            16,
        ),
        tasks=(
            _task(),
        ),
        availability=(
            _availability(),
        ),
    )

    assert len(
        request.tasks,
    ) == 1

    assert len(
        request.availability,
    ) == 1