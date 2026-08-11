# File: /backend/tests/test_study_scheduler.py
# Purpose: Verifies deterministic Track D study scheduling,
# deadlines, priorities, availability, and remaining workload.

from datetime import (
    date,
    datetime,
    time,
    timezone,
)
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.schemas.study_scheduler import (
    SchedulableTask,
    SchedulerAvailabilitySlot,
    SchedulerPreferences,
    StudyScheduleRequest,
)
from app.services.study_scheduler import (
    StudyScheduler,
)

SUBJECT_ID = uuid4()


def _request(
    *,
    tasks: tuple[
        SchedulableTask,
        ...,
    ],
    availability: tuple[
        SchedulerAvailabilitySlot,
        ...,
    ],
    starts_on: date = date(
        2026,
        8,
        10,
    ),
    ends_on: date = date(
        2026,
        8,
        16,
    ),
    preferred_session_minutes: int = 60,
) -> StudyScheduleRequest:
    return StudyScheduleRequest(
        starts_on=starts_on,
        ends_on=ends_on,
        tasks=tasks,
        availability=availability,
        preferences=SchedulerPreferences(
            timezone="Asia/Manila",
            preferred_session_minutes=(
                preferred_session_minutes
            ),
            minimum_session_minutes=15,
        ),
    )


def _task(
    *,
    title: str,
    deadline: datetime,
    minutes: int,
    priority: int = 3,
) -> SchedulableTask:
    return SchedulableTask(
        task_id=uuid4(),
        subject_id=SUBJECT_ID,
        title=title,
        deadline=deadline,
        estimated_minutes=minutes,
        priority_weight=priority,
    )


def _monday_evening() -> (
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


def test_scheduler_uses_student_timezone() -> None:
    """Generated sessions should use the configured local zone."""

    task = _task(
        title="Read",
        deadline=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=60,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                task,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    assert len(
        result.sessions,
    ) == 1

    assert (
        result.sessions[0]
        .starts_at
        .tzinfo
        == ZoneInfo(
            "Asia/Manila",
        )
    )


def test_scheduler_splits_work_into_preferred_sessions() -> None:
    """Large workloads should be divided into study sessions."""

    task = _task(
        title="Finals Review",
        deadline=datetime(
            2026,
            8,
            12,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=120,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                task,
            ),
            availability=(
                _monday_evening(),
            ),
            preferred_session_minutes=60,
        )
    )

    assert [
        session.duration_minutes
        for session in result.sessions
    ] == [
        60,
        60,
    ]

    assert (
        result.unscheduled_tasks
        == ()
    )


def test_scheduler_reports_unfinished_work() -> None:
    """Work that does not fit should remain visible."""

    task = _task(
        title="Large Project",
        deadline=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=180,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                task,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    assert sum(
        session.duration_minutes
        for session in result.sessions
    ) == 120

    assert len(
        result.unscheduled_tasks,
    ) == 1

    assert (
        result.unscheduled_tasks[0]
        .remaining_minutes
        == 60
    )


def test_scheduler_never_schedules_after_deadline() -> None:
    """Sessions must stop before the task's deadline."""

    manila = ZoneInfo(
        "Asia/Manila",
    )

    task = _task(
        title="Deadline Task",
        deadline=datetime(
            2026,
            8,
            10,
            18,
            45,
            tzinfo=manila,
        ),
        minutes=90,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                task,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    assert len(
        result.sessions,
    ) == 1

    assert (
        result.sessions[0].ends_at
        <= task.deadline
    )

    assert (
        result.sessions[0]
        .duration_minutes
        == 45
    )

    assert (
        result.unscheduled_tasks[0]
        .remaining_minutes
        == 45
    )


def test_scheduler_prioritizes_earlier_deadline() -> None:
    """Deadline order should take precedence across tasks."""

    early_task = _task(
        title="Early",
        deadline=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=60,
        priority=2,
    )

    later_task = _task(
        title="Later",
        deadline=datetime(
            2026,
            8,
            15,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=60,
        priority=5,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                later_task,
                early_task,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    assert [
        session.title
        for session in result.sessions
    ] == [
        "Early",
        "Later",
    ]


def test_scheduler_uses_priority_for_equal_deadlines() -> None:
    """Higher priority wins when deadlines are equal."""

    deadline = datetime(
        2026,
        8,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )

    low_priority = _task(
        title="Low Priority",
        deadline=deadline,
        minutes=60,
        priority=1,
    )

    high_priority = _task(
        title="High Priority",
        deadline=deadline,
        minutes=60,
        priority=5,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                low_priority,
                high_priority,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    assert [
        session.title
        for session in result.sessions
    ] == [
        "High Priority",
        "Low Priority",
    ]


def test_scheduler_uses_multiple_weekly_windows() -> None:
    """Recurring availability should expand across plan dates."""

    task = _task(
        title="Long Review",
        deadline=datetime(
            2026,
            8,
            20,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=240,
    )

    availability = (
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
            day_of_week=2,
            start_time=time(
                18,
                0,
            ),
            end_time=time(
                20,
                0,
            ),
        ),
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                task,
            ),
            availability=availability,
        )
    )

    assert sum(
        session.duration_minutes
        for session in result.sessions
    ) == 240

    assert (
        result.unscheduled_tasks
        == ()
    )


def test_scheduler_does_not_create_overlapping_sessions() -> None:
    """Generated sessions must remain sequential."""

    first_task = _task(
        title="Task One",
        deadline=datetime(
            2026,
            8,
            15,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=60,
    )

    second_task = _task(
        title="Task Two",
        deadline=datetime(
            2026,
            8,
            16,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=60,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                first_task,
                second_task,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    first_session = (
        result.sessions[0]
    )

    second_session = (
        result.sessions[1]
    )

    assert (
        first_session.ends_at
        <= second_session.starts_at
    )


def test_expired_task_remains_unscheduled() -> None:
    """Tasks already past due cannot consume future availability."""

    task = _task(
        title="Expired",
        deadline=datetime(
            2026,
            8,
            9,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        minutes=60,
    )

    result = StudyScheduler().generate(
        _request(
            tasks=(
                task,
            ),
            availability=(
                _monday_evening(),
            ),
        )
    )

    assert (
        result.sessions
        == ()
    )

    assert (
        result.unscheduled_tasks[0]
        .remaining_minutes
        == 60
    )