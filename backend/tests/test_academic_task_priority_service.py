# File: /backend/tests/test_academic_task_priority_service.py
# Purpose: Verifies orchestration of task data, student context,
# recurring availability, and deterministic priority scoring.

from __future__ import annotations

from datetime import (
    UTC,
    datetime,
    time,
    timedelta,
)
from uuid import UUID

import pytest

from app.repositories.academic_task_priority_context_repository import (
    AcademicTaskPriorityContextData,
)
from app.schemas.academic_task import (
    AcademicTaskResponse,
    AcademicTaskStatus,
)
from app.services.academic_task_errors import (
    AcademicTaskResponseError,
)
from app.services.academic_task_priority_context import (
    StudyAvailabilitySlot,
)
from app.services.academic_task_priority_service import (
    AcademicTaskPriorityService,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

TASK_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

NOW = datetime(
    2026,
    8,
    10,
    9,
    0,
    tzinfo=UTC,
)


def make_task(
    *,
    task_id: UUID = TASK_ID,
    output_type: str = "writing",
    status: AcademicTaskStatus = AcademicTaskStatus.PENDING,
    deadline: datetime | None = None,
) -> AcademicTaskResponse:
    """Return one valid task for priority-service tests."""

    return AcademicTaskResponse(
        id=task_id,
        subject_id=SUBJECT_ID,
        title="Research assignment",
        description="Complete the first draft.",
        deadline=(
            deadline
            if deadline is not None
            else NOW
            + timedelta(
                hours=12,
            )
        ),
        estimated_minutes=120,
        difficulty="medium",
        task_type="assignment",
        output_type=output_type,
        status=status,
        created_at=NOW,
        updated_at=NOW,
    )


class FakePriorityContextRepository:
    """Record context loads for priority-service tests."""

    def __init__(
        self,
        context: AcademicTaskPriorityContextData,
    ) -> None:
        self.context = context

        self.calls: list[
            UUID
        ] = []

    def load_priority_context(
        self,
        *,
        user_id: UUID,
    ) -> AcademicTaskPriorityContextData:
        """Record and return student priority context."""

        self.calls.append(
            user_id,
        )

        return self.context


def make_context() -> AcademicTaskPriorityContextData:
    """Return one valid reusable student context."""

    return AcademicTaskPriorityContextData(
        timezone_name="Asia/Manila",
        confidence_levels={
            "writing": 1,
            "computation": 4,
            "research": 3,
            "presentation": 3,
            "creative": 3,
            "reading_analysis": 3,
            "memorization": 3,
        },
        availability_slots=(
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
        ),
    )


def test_score_task_loads_authenticated_context() -> None:
    """Single-task scoring must use the authenticated owner."""

    repository = FakePriorityContextRepository(
        make_context(),
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    result = service.score_task(
        user_id=USER_ID,
        task=make_task(),
        now=NOW,
    )

    assert result.task.id == TASK_ID

    assert (
        result.priority.total_score
        > 0
    )

    assert (
        result.priority.output_confidence_score
        == 100.0
    )

    assert repository.calls == [
        USER_ID,
    ]


def test_score_task_resolves_available_study_time() -> None:
    """Recurring availability should affect scheduling pressure."""

    repository = FakePriorityContextRepository(
        AcademicTaskPriorityContextData(
            timezone_name="UTC",
            confidence_levels={
                "writing": 3,
            },
            availability_slots=(
                StudyAvailabilitySlot(
                    day_of_week=1,
                    start_time=time(
                        10,
                        0,
                    ),
                    end_time=time(
                        12,
                        0,
                    ),
                ),
            ),
        )
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    result = service.score_task(
        user_id=USER_ID,
        task=make_task(
            deadline=NOW.replace(
                hour=13,
            ),
        ),
        now=NOW,
    )

    assert (
        result.priority.available_study_time_score
        == 80.0
    )


def test_missing_availability_uses_neutral_fallback() -> None:
    """Absent availability should not mean zero available time."""

    repository = FakePriorityContextRepository(
        AcademicTaskPriorityContextData(
            timezone_name="Asia/Manila",
            confidence_levels={
                "writing": 3,
            },
            availability_slots=(),
        )
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    result = service.score_task(
        user_id=USER_ID,
        task=make_task(),
        now=NOW,
    )

    assert (
        result.priority.available_study_time_score
        == 50.0
    )


def test_missing_confidence_uses_neutral_fallback() -> None:
    """Absent output confidence should remain neutral."""

    repository = FakePriorityContextRepository(
        AcademicTaskPriorityContextData(
            timezone_name="Asia/Manila",
            confidence_levels={},
            availability_slots=(),
        )
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    result = service.score_task(
        user_id=USER_ID,
        task=make_task(),
        now=NOW,
    )

    assert (
        result.priority.output_confidence_score
        == 50.0
    )


def test_other_output_type_uses_neutral_confidence() -> None:
    """Unclassified output types should use neutral confidence."""

    repository = FakePriorityContextRepository(
        make_context(),
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    result = service.score_task(
        user_id=USER_ID,
        task=make_task(
            output_type="other",
        ),
        now=NOW,
    )

    assert (
        result.priority.output_confidence_score
        == 50.0
    )


def test_completed_task_has_zero_priority() -> None:
    """Completed tasks must leave the active priority queue."""

    repository = FakePriorityContextRepository(
        make_context(),
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    result = service.score_task(
        user_id=USER_ID,
        task=make_task(
            status=AcademicTaskStatus.COMPLETED,
        ),
        now=NOW,
    )

    assert (
        result.priority.total_score
        == 0.0
    )


def test_score_tasks_loads_context_only_once() -> None:
    """Batch scoring should not query context once per task."""

    repository = FakePriorityContextRepository(
        make_context(),
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    second_task_id = UUID(
        "44444444-4444-4444-8444-444444444444"
    )

    results = service.score_tasks(
        user_id=USER_ID,
        tasks=[
            make_task(),
            make_task(
                task_id=second_task_id,
                output_type="computation",
            ),
        ],
        now=NOW,
    )

    assert len(
        results,
    ) == 2

    assert results[
        0
    ].task.id == TASK_ID

    assert results[
        1
    ].task.id == second_task_id

    assert repository.calls == [
        USER_ID,
    ]


def test_score_empty_task_list_does_not_load_context() -> None:
    """Empty task lists should require no context query."""

    repository = FakePriorityContextRepository(
        make_context(),
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    results = service.score_tasks(
        user_id=USER_ID,
        tasks=[],
        now=NOW,
    )

    assert results == []
    assert repository.calls == []


def test_invalid_timezone_becomes_controlled_response_error() -> None:
    """Malformed persisted timezone data must fail safely."""

    repository = FakePriorityContextRepository(
        AcademicTaskPriorityContextData(
            timezone_name="Mars/Manila",
            confidence_levels={
                "writing": 3,
            },
            availability_slots=(
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
            ),
        )
    )

    service = AcademicTaskPriorityService(
        repository,
    )

    with pytest.raises(
        AcademicTaskResponseError,
        match="priority context",
    ):
        service.score_task(
            user_id=USER_ID,
            task=make_task(),
            now=NOW,
        )