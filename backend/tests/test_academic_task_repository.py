# File: /backend/tests/test_academic_task_repository.py
# Purpose: Verifies owned academic-task creation, retrieval,
# listing, updates, deletion, and persistence validation.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.academic_task_repository import (
    AcademicTaskRepository,
)
from app.schemas.academic_task import (
    AcademicTaskCreateRequest,
    AcademicTaskStatus,
    AcademicTaskUpdateRequest,
)
from app.services.academic_task_errors import (
    AcademicTaskPersistenceError,
    AcademicTaskResponseError,
    AcademicTaskValidationError,
)


class FakeResponse:
    """Minimal Supabase-style response."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record chained Supabase query operations."""

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

    def insert(
        self,
        payload: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "insert",
                payload,
            )
        )

        return self

    def update(
        self,
        payload: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "update",
                payload,
            )
        )

        return self

    def delete(
        self,
    ) -> FakeQuery:
        self.operations.append(
            (
                "delete",
                None,
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
    """Minimal Supabase-style client."""

    def __init__(
        self,
        query: FakeQuery,
    ) -> None:
        self.query = query

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

        return self.query


TASK_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

DEADLINE = datetime(
    2026,
    8,
    20,
    12,
    0,
    tzinfo=UTC,
)


def _task_row(
    *,
    task_id: UUID | None = None,
    subject_id: UUID | None = None,
    status: str = "pending",
    description: str | None = "Complete the first draft.",
) -> dict[
    str,
    object,
]:
    """Return one valid persisted academic-task row."""

    now = datetime.now(
        UTC,
    ).isoformat()

    return {
        "id": str(
            task_id
            if task_id is not None
            else uuid4()
        ),
        "subject_id": str(
            subject_id
            if subject_id is not None
            else SUBJECT_ID
        ),
        "title": "Research assignment",
        "description": description,
        "deadline": DEADLINE.isoformat(),
        "estimated_minutes": 120,
        "difficulty": "medium",
        "task_type": "assignment",
        "status": status,
        "created_at": now,
        "updated_at": now,
    }


def _create_request() -> AcademicTaskCreateRequest:
    """Return one valid academic-task creation request."""

    return AcademicTaskCreateRequest(
        subject_id=SUBJECT_ID,
        title="Research assignment",
        description="Complete the first draft.",
        deadline=DEADLINE,
        estimated_minutes=120,
        difficulty="medium",
        task_type="assignment",
    )


def test_create_academic_task_saves_owned_payload() -> None:
    """Creation must persist the authenticated owner."""

    user_id = uuid4()

    query = FakeQuery(
        [
            _task_row(
                task_id=TASK_ID,
            )
        ],
    )

    client = FakeClient(
        query,
    )

    repository = AcademicTaskRepository(
        client,
    )

    result = repository.create_academic_task(
        user_id=user_id,
        request=_create_request(),
    )

    assert result.id == TASK_ID
    assert result.subject_id == SUBJECT_ID
    assert result.status is AcademicTaskStatus.PENDING

    assert client.table_names == [
        "academic_tasks",
    ]

    insert_operations = [
        value
        for operation, value in query.operations
        if operation == "insert"
    ]

    assert len(
        insert_operations,
    ) == 1

    payload = insert_operations[
        0
    ]

    assert isinstance(
        payload,
        dict,
    )

    assert payload[
        "user_id"
    ] == str(
        user_id,
    )

    assert payload[
        "subject_id"
    ] == str(
        SUBJECT_ID,
    )

    assert payload[
        "difficulty"
    ] == "medium"

    assert payload[
        "task_type"
    ] == "assignment"

    assert payload[
        "status"
    ] == "pending"

    selected_columns = [
        value
        for operation, value in query.operations
        if operation == "select"
    ]

    assert len(
        selected_columns,
    ) == 1

    assert "id" in selected_columns[
        0
    ]

    assert "subject_id" in selected_columns[
        0
    ]

    assert "deadline" in selected_columns[
        0
    ]

    assert "user_id" not in selected_columns[
        0
    ]


def test_list_academic_tasks_filters_by_owner() -> None:
    """Task lists must always filter by authenticated owner."""

    user_id = uuid4()

    query = FakeQuery(
        [
            _task_row(),
        ],
    )

    repository = AcademicTaskRepository(
        FakeClient(
            query,
        ),
    )

    result = repository.list_academic_tasks(
        user_id=user_id,
        limit=20,
    )

    assert len(
        result,
    ) == 1

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations

    assert (
        "order",
        (
            "deadline",
            False,
        ),
    ) in query.operations

    assert (
        "limit",
        20,
    ) in query.operations


@pytest.mark.parametrize(
    "invalid_limit",
    [
        0,
        101,
        True,
    ],
)
def test_list_academic_task_limit_is_validated(
    invalid_limit: object,
) -> None:
    """Unbounded or invalid task lists must be rejected."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                [],
            ),
        ),
    )

    with pytest.raises(
        AcademicTaskValidationError,
    ):
        repository.list_academic_tasks(
            user_id=uuid4(),
            limit=invalid_limit,  # type: ignore[arg-type]
        )


def test_get_academic_task_filters_id_and_owner() -> None:
    """Single task lookup must check task ID and owner."""

    user_id = uuid4()

    query = FakeQuery(
        [
            _task_row(
                task_id=TASK_ID,
            )
        ],
    )

    repository = AcademicTaskRepository(
        FakeClient(
            query,
        ),
    )

    result = repository.get_academic_task(
        user_id=user_id,
        task_id=TASK_ID,
    )

    assert result is not None
    assert result.id == TASK_ID

    assert (
        "eq",
        (
            "id",
            str(
                TASK_ID,
            ),
        ),
    ) in query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations


def test_get_missing_academic_task_returns_none() -> None:
    """Missing owned task must not be fabricated."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                [],
            ),
        ),
    )

    result = repository.get_academic_task(
        user_id=uuid4(),
        task_id=uuid4(),
    )

    assert result is None


def test_update_academic_task_filters_owner() -> None:
    """Updates must target only an owned academic task."""

    user_id = uuid4()

    query = FakeQuery(
        [
            _task_row(
                task_id=TASK_ID,
                status="in_progress",
            )
        ],
    )

    repository = AcademicTaskRepository(
        FakeClient(
            query,
        ),
    )

    request = AcademicTaskUpdateRequest(
        status="in_progress",
    )

    result = repository.update_academic_task(
        user_id=user_id,
        task_id=TASK_ID,
        request=request,
    )

    assert result is not None
    assert (
        result.status
        is AcademicTaskStatus.IN_PROGRESS
    )

    update_operations = [
        value
        for operation, value in query.operations
        if operation == "update"
    ]

    assert update_operations == [
        {
            "status": "in_progress",
        }
    ]

    assert (
        "eq",
        (
            "id",
            str(
                TASK_ID,
            ),
        ),
    ) in query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations


def test_update_academic_task_can_clear_description() -> None:
    """Explicitly clearing the description must persist null."""

    query = FakeQuery(
        [
            _task_row(
                task_id=TASK_ID,
                description=None,
            )
        ],
    )

    repository = AcademicTaskRepository(
        FakeClient(
            query,
        ),
    )

    result = repository.update_academic_task(
        user_id=uuid4(),
        task_id=TASK_ID,
        request=AcademicTaskUpdateRequest(
            description="   ",
        ),
    )

    assert result is not None
    assert result.description is None

    update_operations = [
        value
        for operation, value in query.operations
        if operation == "update"
    ]

    assert update_operations == [
        {
            "description": None,
        }
    ]


def test_update_missing_academic_task_returns_none() -> None:
    """Updating a missing owned task should return none."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                [],
            ),
        ),
    )

    result = repository.update_academic_task(
        user_id=uuid4(),
        task_id=uuid4(),
        request=AcademicTaskUpdateRequest(
            status="completed",
        ),
    )

    assert result is None


def test_delete_academic_task_filters_owner() -> None:
    """Deletion must remain ownership scoped."""

    user_id = uuid4()

    query = FakeQuery(
        [
            {
                "id": str(
                    TASK_ID,
                )
            }
        ],
    )

    repository = AcademicTaskRepository(
        FakeClient(
            query,
        ),
    )

    deleted = repository.delete_academic_task(
        user_id=user_id,
        task_id=TASK_ID,
    )

    assert deleted is True

    assert (
        "eq",
        (
            "id",
            str(
                TASK_ID,
            ),
        ),
    ) in query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations

    assert (
        "select",
        "id",
    ) in query.operations


def test_delete_missing_academic_task_returns_false() -> None:
    """Deleting a missing owned task should return false."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                [],
            ),
        ),
    )

    deleted = repository.delete_academic_task(
        user_id=uuid4(),
        task_id=uuid4(),
    )

    assert deleted is False


def test_invalid_database_row_is_rejected() -> None:
    """Malformed persisted task data must fail safely."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                [
                    {
                        "id": "invalid",
                    }
                ],
            ),
        ),
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.list_academic_tasks(
            user_id=uuid4(),
        )


def test_invalid_supabase_response_is_rejected() -> None:
    """Non-list Supabase data must not be accepted."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                "invalid response",
            ),
        ),
    )

    with pytest.raises(
        AcademicTaskResponseError,
    ):
        repository.list_academic_tasks(
            user_id=uuid4(),
        )


def test_database_failure_is_controlled() -> None:
    """Raw Supabase errors must become task persistence errors."""

    repository = AcademicTaskRepository(
        FakeClient(
            FakeQuery(
                [],
                error=RuntimeError(
                    "database unavailable",
                ),
            ),
        ),
    )

    with pytest.raises(
        AcademicTaskPersistenceError,
    ):
        repository.list_academic_tasks(
            user_id=uuid4(),
        )