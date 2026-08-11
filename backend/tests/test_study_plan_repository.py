# File: /backend/tests/test_study_plan_repository.py
# Purpose: Verifies ownership filtering, persistence payloads,
# response parsing, and failures in the Track D repository.

from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from types import SimpleNamespace
from uuid import (
    UUID,
    uuid4,
)

import pytest

from app.repositories.study_plan_repository import (
    StudyPlanRepository,
)
from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudySessionCreateRequest,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
)

USER_ID = uuid4()
PLAN_ID = uuid4()
SESSION_ID = uuid4()
SUBJECT_ID = uuid4()

NOW = datetime(
    2026,
    8,
    10,
    8,
    0,
    tzinfo=timezone.utc,
)


def _plan_row() -> dict[str, object]:
    return {
        "id": str(
            PLAN_ID,
        ),
        "title": "Finals Review",
        "starts_on": "2026-08-10",
        "ends_on": "2026-08-17",
        "status": "active",
        "generation_mode": "manual",
        "generated_at": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }


def _session_row() -> dict[str, object]:
    return {
        "id": str(
            SESSION_ID,
        ),
        "study_plan_id": str(
            PLAN_ID,
        ),
        "subject_id": str(
            SUBJECT_ID,
        ),
        "title": "Review Chapter 4",
        "starts_at": NOW.isoformat(),
        "ends_at": (
            NOW
            + timedelta(
                hours=1,
            )
        ).isoformat(),
        "status": "planned",
        "origin": "manual",
        "notes": "Focus on definitions.",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }


class FakeQuery:
    def __init__(
        self,
        data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.data = data
        self.error = error
        self.calls: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.calls.append(
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
        self.calls.append(
            (
                "insert",
                payload,
            )
        )
        return self

    def delete(
        self,
    ) -> FakeQuery:
        self.calls.append(
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
        self.calls.append(
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
        self.calls.append(
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
        self.calls.append(
            (
                "limit",
                count,
            )
        )
        return self

    def execute(
        self,
    ) -> SimpleNamespace:
        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            data=self.data,
        )


class FakeClient:
    def __init__(
        self,
        query: FakeQuery,
    ) -> None:
        self.query = query
        self.tables: list[str] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        self.tables.append(
            table_name,
        )

        return self.query


def test_create_study_plan_uses_owned_payload() -> None:
    query = FakeQuery(
        [
            _plan_row(),
        ]
    )

    repository = StudyPlanRepository(
        FakeClient(
            query,
        )
    )

    result = repository.create_study_plan(
        user_id=USER_ID,
        request=StudyPlanCreateRequest(
            title="Finals Review",
            starts_on=date(
                2026,
                8,
                10,
            ),
            ends_on=date(
                2026,
                8,
                17,
            ),
        ),
    )

    assert result.id == PLAN_ID

    insert_call = next(
        value
        for operation, value in query.calls
        if operation == "insert"
    )

    assert isinstance(
        insert_call,
        dict,
    )

    assert insert_call[
        "user_id"
    ] == str(
        USER_ID,
    )

    assert (
        insert_call[
            "generation_mode"
        ]
        == "manual"
    )


def test_get_study_plan_filters_owner() -> None:
    query = FakeQuery(
        [
            _plan_row(),
        ]
    )

    repository = StudyPlanRepository(
        FakeClient(
            query,
        )
    )

    result = repository.get_study_plan(
        user_id=USER_ID,
        study_plan_id=PLAN_ID,
    )

    assert result is not None
    assert result.id == PLAN_ID

    assert (
        "eq",
        (
            "user_id",
            str(
                USER_ID,
            ),
        ),
    ) in query.calls


def test_list_study_plans_rejects_invalid_limit() -> None:
    repository = StudyPlanRepository(
        FakeClient(
            FakeQuery(
                [],
            )
        )
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        repository.list_study_plans(
            user_id=USER_ID,
            limit=0,
        )


def test_create_study_session_uses_manual_origin() -> None:
    query = FakeQuery(
        [
            _session_row(),
        ]
    )

    repository = StudyPlanRepository(
        FakeClient(
            query,
        )
    )

    result = repository.create_study_session(
        user_id=USER_ID,
        study_plan_id=PLAN_ID,
        request=StudySessionCreateRequest(
            subject_id=SUBJECT_ID,
            title="Review Chapter 4",
            starts_at=NOW,
            ends_at=(
                NOW
                + timedelta(
                    hours=1,
                )
            ),
            notes="Focus on definitions.",
        ),
    )

    assert result.id == SESSION_ID

    insert_call = next(
        value
        for operation, value in query.calls
        if operation == "insert"
    )

    assert isinstance(
        insert_call,
        dict,
    )

    assert (
        insert_call[
            "study_plan_id"
        ]
        == str(
            PLAN_ID,
        )
    )

    assert insert_call[
        "origin"
    ] == "manual"


def test_delete_missing_study_session_returns_false() -> None:
    repository = StudyPlanRepository(
        FakeClient(
            FakeQuery(
                [],
            )
        )
    )

    deleted = (
        repository.delete_study_session(
            user_id=USER_ID,
            study_plan_id=PLAN_ID,
            study_session_id=SESSION_ID,
        )
    )

    assert deleted is False


def test_repository_rejects_invalid_response_data() -> None:
    repository = StudyPlanRepository(
        FakeClient(
            FakeQuery(
                "invalid",
            )
        )
    )

    with pytest.raises(
        StudyPlanResponseError,
    ):
        repository.list_study_plans(
            user_id=USER_ID,
        )


def test_repository_wraps_storage_failure() -> None:
    repository = StudyPlanRepository(
        FakeClient(
            FakeQuery(
                [],
                error=RuntimeError(
                    "storage failed",
                ),
            )
        )
    )

    with pytest.raises(
        StudyPlanPersistenceError,
    ):
        repository.list_study_plans(
            user_id=USER_ID,
        )


def test_uuid_constants_are_valid() -> None:
    """Keep static test identifiers UUID-compatible."""

    assert isinstance(
        USER_ID,
        UUID,
    )