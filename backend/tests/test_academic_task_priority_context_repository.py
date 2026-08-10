# File: /backend/tests/test_academic_task_priority_context_repository.py
# Purpose: Verifies loading and validation of student-owned
# context used by deterministic academic-task prioritization.

from __future__ import annotations

from uuid import UUID

import pytest

from app.repositories.academic_task_priority_context_repository import (
    AcademicTaskPriorityContextRepository,
)
from app.services.academic_task_errors import (
    AcademicTaskPersistenceError,
    AcademicTaskResponseError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)


class FakeResponse:
    """Minimal Supabase-style response."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record chained Supabase read operations."""

    def __init__(
        self,
        response_data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error

        self.operations: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.operations.append(
            (
                "select",
                columns,
            )
        )

        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "eq",
                (
                    column,
                    value,
                ),
            )
        )

        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> FakeQuery:
        self.operations.append(
            (
                "order",
                (
                    column,
                    desc,
                ),
            )
        )

        return self

    def limit(
        self,
        count: int,
    ) -> FakeQuery:
        self.operations.append(
            (
                "limit",
                count,
            )
        )

        return self

    def execute(
        self,
    ) -> FakeResponse:
        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.response_data,
        )


class FakeClient:
    """Route table names to independent fake queries."""

    def __init__(
        self,
        queries: dict[
            str,
            FakeQuery,
        ],
    ) -> None:
        self.queries = queries

        self.table_names: list[
            str
        ] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        self.table_names.append(
            table_name,
        )

        return self.queries[
            table_name
        ]


def make_client() -> tuple[
    FakeClient,
    dict[
        str,
        FakeQuery,
    ],
]:
    """Return one valid priority-context fake client."""

    queries = {
        "profiles": FakeQuery(
            [
                {
                    "timezone": "Asia/Manila",
                }
            ],
        ),
        "learning_output_confidences": FakeQuery(
            [
                {
                    "output_type": "writing",
                    "confidence_level": 2,
                },
                {
                    "output_type": "computation",
                    "confidence_level": 4,
                },
            ],
        ),
        "study_availability": FakeQuery(
            [
                {
                    "day_of_week": 1,
                    "start_time": "18:00:00",
                    "end_time": "20:00:00",
                },
                {
                    "day_of_week": 3,
                    "start_time": "17:30:00",
                    "end_time": "19:00:00",
                },
            ],
        ),
    }

    return (
        FakeClient(
            queries,
        ),
        queries,
    )


def test_load_priority_context_returns_student_data() -> None:
    """Repository should load all priority context."""

    client, queries = make_client()

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    result = repository.load_priority_context(
        user_id=USER_ID,
    )

    assert (
        result.timezone_name
        == "Asia/Manila"
    )

    assert result.confidence_levels == {
        "writing": 2,
        "computation": 4,
    }

    assert len(
        result.availability_slots,
    ) == 2

    assert (
        result.availability_slots[
            0
        ].day_of_week
        == 1
    )

    assert (
        result.availability_slots[
            0
        ].start_time.isoformat()
        == "18:00:00"
    )

    assert client.table_names == [
        "profiles",
        "learning_output_confidences",
        "study_availability",
    ]

    assert (
        "eq",
        (
            "id",
            str(
                USER_ID,
            ),
        ),
    ) in queries[
        "profiles"
    ].operations

    assert (
        "eq",
        (
            "user_id",
            str(
                USER_ID,
            ),
        ),
    ) in queries[
        "learning_output_confidences"
    ].operations

    assert (
        "eq",
        (
            "user_id",
            str(
                USER_ID,
            ),
        ),
    ) in queries[
        "study_availability"
    ].operations


def test_timezone_is_normalized() -> None:
    """Stored timezone whitespace should be normalized."""

    client, queries = make_client()

    queries[
        "profiles"
    ].response_data = [
        {
            "timezone": "  Asia/Manila  ",
        }
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    result = repository.load_priority_context(
        user_id=USER_ID,
    )

    assert (
        result.timezone_name
        == "Asia/Manila"
    )


@pytest.mark.parametrize(
    "profile_rows",
    [
        [],
        [
            {
                "timezone": "Asia/Manila",
            },
            {
                "timezone": "UTC",
            },
        ],
        [
            {
                "timezone": "",
            }
        ],
    ],
)
def test_invalid_profile_timezone_response_is_rejected(
    profile_rows: list[
        dict[
            str,
            object,
        ]
    ],
) -> None:
    """Exactly one non-empty timezone must be returned."""

    client, queries = make_client()

    queries[
        "profiles"
    ].response_data = profile_rows

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_missing_confidence_rows_are_allowed() -> None:
    """Incomplete confidence context should support neutral fallback."""

    client, queries = make_client()

    queries[
        "learning_output_confidences"
    ].response_data = []

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    result = repository.load_priority_context(
        user_id=USER_ID,
    )

    assert result.confidence_levels == {}


def test_invalid_confidence_type_is_rejected() -> None:
    """Unsupported persisted output categories must fail safely."""

    client, queries = make_client()

    queries[
        "learning_output_confidences"
    ].response_data = [
        {
            "output_type": "coding",
            "confidence_level": 3,
        }
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


@pytest.mark.parametrize(
    "confidence_level",
    [
        0,
        6,
        True,
    ],
)
def test_invalid_confidence_level_is_rejected(
    confidence_level: object,
) -> None:
    """Malformed persisted confidence values must fail safely."""

    client, queries = make_client()

    queries[
        "learning_output_confidences"
    ].response_data = [
        {
            "output_type": "writing",
            "confidence_level": confidence_level,
        }
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_duplicate_confidence_type_is_rejected() -> None:
    """Duplicate confidence rows must not be silently overwritten."""

    client, queries = make_client()

    queries[
        "learning_output_confidences"
    ].response_data = [
        {
            "output_type": "writing",
            "confidence_level": 2,
        },
        {
            "output_type": "writing",
            "confidence_level": 4,
        },
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
        match="Duplicate",
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_empty_availability_is_allowed() -> None:
    """No availability rows should remain representable."""

    client, queries = make_client()

    queries[
        "study_availability"
    ].response_data = []

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    result = repository.load_priority_context(
        user_id=USER_ID,
    )

    assert (
        result.availability_slots
        == ()
    )


@pytest.mark.parametrize(
    "day_of_week",
    [
        0,
        8,
        True,
    ],
)
def test_invalid_availability_weekday_is_rejected(
    day_of_week: object,
) -> None:
    """Weekdays must match the ISO 1-through-7 contract."""

    client, queries = make_client()

    queries[
        "study_availability"
    ].response_data = [
        {
            "day_of_week": day_of_week,
            "start_time": "18:00:00",
            "end_time": "20:00:00",
        }
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_invalid_availability_time_is_rejected() -> None:
    """Malformed stored time strings must fail safely."""

    client, queries = make_client()

    queries[
        "study_availability"
    ].response_data = [
        {
            "day_of_week": 1,
            "start_time": "not-a-time",
            "end_time": "20:00:00",
        }
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_reversed_availability_period_is_rejected() -> None:
    """Availability start time must precede end time."""

    client, queries = make_client()

    queries[
        "study_availability"
    ].response_data = [
        {
            "day_of_week": 1,
            "start_time": "20:00:00",
            "end_time": "18:00:00",
        }
    ]

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_invalid_supabase_response_is_rejected() -> None:
    """Priority-context queries must return list-shaped data."""

    client, queries = make_client()

    queries[
        "profiles"
    ].response_data = "invalid"

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )


def test_database_failure_is_controlled() -> None:
    """Raw Supabase failures must become domain persistence errors."""

    client, queries = make_client()

    queries[
        "profiles"
    ].error = RuntimeError(
        "database unavailable",
    )

    repository = (
        AcademicTaskPriorityContextRepository(
            client,
        )
    )

    with pytest.raises(
        AcademicTaskPersistenceError,
    ):
        repository.load_priority_context(
            user_id=USER_ID,
        )