# File: /backend/tests/test_study_scheduler_academic_task_compatibility.py
# Purpose: Verifies that Track D's generic scheduler accepts the
# maximum task sizes exposed by Track C Academic Tasks.

from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from app.schemas.study_scheduler import (
    SchedulableTask,
)


def test_schedulable_task_accepts_track_c_maximum_title() -> None:
    task = SchedulableTask(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="A" * 200,
        deadline=datetime(
            2026,
            8,
            20,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        estimated_minutes=60,
        priority_weight=3,
    )

    assert len(
        task.title,
    ) == 200


def test_schedulable_task_accepts_track_c_maximum_estimate() -> None:
    task = SchedulableTask(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="Large research project",
        deadline=datetime(
            2026,
            8,
            31,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        estimated_minutes=10_080,
        priority_weight=5,
    )

    assert (
        task.estimated_minutes
        == 10_080
    )