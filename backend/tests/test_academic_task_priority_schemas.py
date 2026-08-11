# File: /backend/tests/test_academic_task_priority_schemas.py
# Purpose: Verifies public API contracts for academic-task
# priority scores and prioritized task collections.

from datetime import (
    UTC,
    datetime,
)
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.academic_task import (
    AcademicTaskResponse,
)
from app.schemas.academic_task_priority import (
    AcademicTaskPriorityBreakdownResponse,
    AcademicTaskPriorityListResponse,
    AcademicTaskPriorityResponse,
)

TASK_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

NOW = datetime(
    2026,
    8,
    9,
    10,
    0,
    tzinfo=UTC,
)


def make_task() -> AcademicTaskResponse:
    """Return one valid task response."""

    return AcademicTaskResponse(
        id=TASK_ID,
        subject_id=SUBJECT_ID,
        title="Research assignment",
        description="Complete the first draft.",
        deadline=datetime(
            2026,
            8,
            20,
            12,
            0,
            tzinfo=UTC,
        ),
        estimated_minutes=120,
        difficulty="medium",
        task_type="assignment",
        output_type="writing",
        status="pending",
        created_at=NOW,
        updated_at=NOW,
    )


def make_priority(
) -> AcademicTaskPriorityBreakdownResponse:
    """Return one valid priority breakdown."""

    return AcademicTaskPriorityBreakdownResponse(
        total_score=72.5,
        deadline_score=85.0,
        difficulty_score=60.0,
        estimated_time_score=60.0,
        output_confidence_score=75.0,
        previous_performance_score=50.0,
        available_study_time_score=80.0,
        status_score=50.0,
    )


def test_priority_breakdown_accepts_valid_scores() -> None:
    """Every priority factor should remain bounded."""

    priority = make_priority()

    assert priority.total_score == 72.5
    assert priority.deadline_score == 85.0
    assert (
        priority.output_confidence_score
        == 75.0
    )


@pytest.mark.parametrize(
    "invalid_score",
    [
        -0.1,
        100.1,
    ],
)
def test_priority_breakdown_rejects_invalid_total(
    invalid_score: float,
) -> None:
    """Priority totals must remain between zero and 100."""

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskPriorityBreakdownResponse(
            total_score=invalid_score,
            deadline_score=50,
            difficulty_score=50,
            estimated_time_score=50,
            output_confidence_score=50,
            previous_performance_score=50,
            available_study_time_score=50,
            status_score=50,
        )


def test_priority_response_contains_task_and_breakdown() -> None:
    """One API item should pair task data with priority data."""

    response = AcademicTaskPriorityResponse(
        task=make_task(),
        priority=make_priority(),
    )

    assert response.task.id == TASK_ID

    assert (
        response.priority.total_score
        == 72.5
    )


def test_priority_list_contains_validated_items() -> None:
    """Priority lists should contain validated task items."""

    item = AcademicTaskPriorityResponse(
        task=make_task(),
        priority=make_priority(),
    )

    response = AcademicTaskPriorityListResponse(
        items=(
            item,
        ),
    )

    assert response.items == (
        item,
    )


def test_priority_response_forbids_unknown_fields() -> None:
    """Priority API responses should reject accidental fields."""

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskPriorityResponse(
            task=make_task(),
            priority=make_priority(),
            user_id=str(
                UUID(
                    "33333333-3333-4333-8333-333333333333"
                )
            ),
        )