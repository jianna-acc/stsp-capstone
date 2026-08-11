# File: /backend/tests/test_study_scheduler_blocked_time.py
# Purpose: Verifies that generated study schedules avoid
# occupied manual time and never schedule before a boundary.

from datetime import (
    date,
    datetime,
    time,
)
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.schemas.study_scheduler import (
    SchedulableTask,
    SchedulerAvailabilitySlot,
    SchedulerBlockedWindow,
    SchedulerPreferences,
    StudyScheduleRequest,
)
from app.services.study_scheduler import (
    StudyScheduler,
)

MANILA = ZoneInfo(
    "Asia/Manila",
)


def _task(
    *,
    estimated_minutes: int = 120,
) -> SchedulableTask:
    return SchedulableTask(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="Study Biology",
        deadline=datetime(
            2026,
            8,
            11,
            23,
            0,
            tzinfo=MANILA,
        ),
        estimated_minutes=estimated_minutes,
        priority_weight=5,
    )


def _request(
    *,
    blocked_windows: tuple[
        SchedulerBlockedWindow,
        ...,
    ] = (),
    not_before: datetime | None = None,
    estimated_minutes: int = 120,
) -> StudyScheduleRequest:
    return StudyScheduleRequest(
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
            _task(
                estimated_minutes=(
                    estimated_minutes
                ),
            ),
        ),
        availability=(
            SchedulerAvailabilitySlot(
                day_of_week=1,
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    21,
                    0,
                ),
            ),
        ),
        blocked_windows=(
            blocked_windows
        ),
        not_before=not_before,
        preferences=SchedulerPreferences(
            timezone="Asia/Manila",
            preferred_session_minutes=60,
            minimum_session_minutes=15,
        ),
    )


def test_scheduler_avoids_blocked_manual_time() -> None:
    result = StudyScheduler().generate(
        _request(
            blocked_windows=(
                SchedulerBlockedWindow(
                    starts_at=datetime(
                        2026,
                        8,
                        10,
                        19,
                        0,
                        tzinfo=MANILA,
                    ),
                    ends_at=datetime(
                        2026,
                        8,
                        10,
                        20,
                        0,
                        tzinfo=MANILA,
                    ),
                ),
            ),
        )
    )

    assert len(
        result.sessions,
    ) == 2

    assert (
        result.sessions[0]
        .starts_at
        .hour
        == 18
    )

    assert (
        result.sessions[0]
        .ends_at
        .hour
        == 19
    )

    assert (
        result.sessions[1]
        .starts_at
        .hour
        == 20
    )

    assert (
        result.sessions[1]
        .ends_at
        .hour
        == 21
    )


def test_scheduler_does_not_schedule_before_boundary() -> None:
    result = StudyScheduler().generate(
        _request(
            estimated_minutes=60,
            not_before=datetime(
                2026,
                8,
                10,
                19,
                30,
                tzinfo=MANILA,
            ),
        )
    )

    assert len(
        result.sessions,
    ) == 1

    assert (
        result.sessions[0]
        .starts_at
        == datetime(
            2026,
            8,
            10,
            19,
            30,
            tzinfo=MANILA,
        )
    )


def test_blocked_time_outside_availability_does_not_change_schedule() -> None:
    result = StudyScheduler().generate(
        _request(
            estimated_minutes=60,
            blocked_windows=(
                SchedulerBlockedWindow(
                    starts_at=datetime(
                        2026,
                        8,
                        10,
                        12,
                        0,
                        tzinfo=MANILA,
                    ),
                    ends_at=datetime(
                        2026,
                        8,
                        10,
                        13,
                        0,
                        tzinfo=MANILA,
                    ),
                ),
            ),
        )
    )

    assert len(
        result.sessions,
    ) == 1

    assert (
        result.sessions[0]
        .starts_at
        .hour
        == 18
    )