# File: /backend/app/services/study_scheduler.py
# Purpose: Generates deterministic study sessions from generic
# tasks, recurring availability, deadlines, and study preferences.

from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from zoneinfo import ZoneInfo

from app.schemas.study_scheduler import (
    GeneratedStudySession,
    SchedulableTask,
    SchedulerAvailabilitySlot,
    StudyScheduleRequest,
    StudyScheduleResult,
    UnscheduledTask,
)


@dataclass(
    slots=True,
)
class _TaskState:
    """Mutable remaining workload for one validated task."""

    task: SchedulableTask

    remaining_minutes: int


class StudyScheduler:
    """Generate study sessions without depending on Track C."""

    def generate(
        self,
        request: StudyScheduleRequest,
    ) -> StudyScheduleResult:
        """Allocate available study time before task deadlines."""

        timezone_info = ZoneInfo(
            request.preferences.timezone,
        )

        task_states = [
            _TaskState(
                task=task,
                remaining_minutes=(
                    task.estimated_minutes
                ),
            )
            for task in request.tasks
        ]

        task_states.sort(
            key=self._task_sort_key,
        )

        windows = self._build_availability_windows(
            starts_on=request.starts_on,
            ends_on=request.ends_on,
            availability=request.availability,
            timezone_info=timezone_info,
        )

        sessions: list[
            GeneratedStudySession
        ] = []

        for (
            window_start,
            window_end,
        ) in windows:
            cursor = window_start

            while cursor < window_end:
                selected = self._select_task(
                    task_states=task_states,
                    cursor=cursor,
                    window_end=window_end,
                    minimum_session_minutes=(
                        request
                        .preferences
                        .minimum_session_minutes
                    ),
                )

                if selected is None:
                    break

                (
                    task_state,
                    effective_end,
                ) = selected

                available_minutes = int(
                    (
                        effective_end
                        - cursor
                    ).total_seconds()
                    // 60
                )

                session_minutes = min(
                    request
                    .preferences
                    .preferred_session_minutes,
                    task_state.remaining_minutes,
                    available_minutes,
                )

                if session_minutes <= 0:
                    break

                session_end = (
                    cursor
                    + timedelta(
                        minutes=session_minutes,
                    )
                )

                sessions.append(
                    GeneratedStudySession(
                        task_id=(
                            task_state.task.task_id
                        ),
                        subject_id=(
                            task_state.task.subject_id
                        ),
                        title=(
                            task_state.task.title
                        ),
                        starts_at=cursor,
                        ends_at=session_end,
                        duration_minutes=(
                            session_minutes
                        ),
                    )
                )

                task_state.remaining_minutes -= (
                    session_minutes
                )

                cursor = session_end

        unscheduled_tasks = tuple(
            UnscheduledTask(
                task_id=state.task.task_id,
                remaining_minutes=(
                    state.remaining_minutes
                ),
            )
            for state in task_states
            if state.remaining_minutes > 0
        )

        return StudyScheduleResult(
            sessions=tuple(
                sessions,
            ),
            unscheduled_tasks=(
                unscheduled_tasks
            ),
        )

    @staticmethod
    def _task_sort_key(
        state: _TaskState,
    ) -> tuple[
        datetime,
        int,
        str,
    ]:
        """Schedule nearer deadlines first, then higher priority."""

        return (
            state.task.deadline.astimezone(
                timezone.utc,
            ),
            -state.task.priority_weight,
            str(
                state.task.task_id,
            ),
        )

    @staticmethod
    def _select_task(
        *,
        task_states: list[
            _TaskState
        ],
        cursor: datetime,
        window_end: datetime,
        minimum_session_minutes: int,
    ) -> tuple[
        _TaskState,
        datetime,
    ] | None:
        """Choose the next task that can use the current window."""

        for state in task_states:
            if state.remaining_minutes <= 0:
                continue

            task_deadline = (
                state.task.deadline.astimezone(
                    cursor.tzinfo,
                )
            )

            if cursor >= task_deadline:
                continue

            effective_end = min(
                window_end,
                task_deadline,
            )

            available_minutes = int(
                (
                    effective_end
                    - cursor
                ).total_seconds()
                // 60
            )

            if available_minutes <= 0:
                continue

            if (
                available_minutes
                < minimum_session_minutes
                and state.remaining_minutes
                > available_minutes
            ):
                continue

            return (
                state,
                effective_end,
            )

        return None

    @staticmethod
    def _build_availability_windows(
        *,
        starts_on: date,
        ends_on: date,
        availability: tuple[
            SchedulerAvailabilitySlot,
            ...,
        ],
        timezone_info: ZoneInfo,
    ) -> list[
        tuple[
            datetime,
            datetime,
        ]
    ]:
        """Expand recurring availability across plan dates."""

        windows: list[
            tuple[
                datetime,
                datetime,
            ]
        ] = []

        current_date = starts_on

        while current_date <= ends_on:
            weekday = (
                current_date.isoweekday()
            )

            matching_slots = (
                slot
                for slot in availability
                if slot.day_of_week
                == weekday
            )

            for slot in matching_slots:
                window_start = datetime.combine(
                    current_date,
                    slot.start_time,
                    tzinfo=timezone_info,
                )

                window_end = datetime.combine(
                    current_date,
                    slot.end_time,
                    tzinfo=timezone_info,
                )

                windows.append(
                    (
                        window_start,
                        window_end,
                    )
                )

            current_date += timedelta(
                days=1,
            )

        windows.sort(
            key=lambda window: window[0],
        )

        return windows