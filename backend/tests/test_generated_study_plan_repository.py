# File: /backend/tests/test_generated_study_plan_repository.py
# Purpose: Verifies generated Track D plans and sessions use
# generated persistence metadata and owner-scoped rollback.

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

from app.repositories.generated_study_plan_repository import (
    GeneratedStudyPlanRepository,
)
from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceRequest,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
)

USER_ID = uuid4()
PLAN_ID = uuid4()
SESSION_ID = uuid4()
TASK_ID = uuid4()
SUBJECT_ID = uuid4()

GENERATED_AT = datetime(
    2026,
    8,
    10,
    7,
    0,
    tzinfo=timezone.utc,
)

STARTS_AT = datetime(
    2026,
    8,
    10,
    18,
    0,
    tzinfo=timezone(
        timedelta(
            hours=8,
        )
    ),
)

ENDS_AT = STARTS_AT + timedelta(
    minutes=60,
)


class FakeQuery:
    def __init__(
        self,
        *,
        response_data: object = None,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error
        self.calls = []

    def insert(
        self,
        values: object,
    ) -> FakeQuery:
        self.calls.append(
            (
                "insert",
                values,
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

    def execute(
        self,
    ) -> SimpleNamespace:
        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            data=self.response_data,
        )


class FakeClient:
    def __init__(
        self,
        *,
        plan_query: FakeQuery,
        session_query: FakeQuery,
    ) -> None:
        self.plan_query = plan_query
        self.session_query = session_query

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        if table_name == "study_plans":
            return self.plan_query

        if table_name == "study_sessions":
            return self.session_query

        raise AssertionError(
            f"Unexpected table: {table_name}",
        )


def _plan_row() -> dict[
    str,
    object,
]:
    return {
        "id": str(
            PLAN_ID,
        ),
        "title": "Finals Plan",
        "starts_on": "2026-08-10",
        "ends_on": "2026-08-10",
        "status": "active",
        "generation_mode": "generated",
        "generated_at": (
            GENERATED_AT.isoformat()
        ),
        "created_at": (
            GENERATED_AT.isoformat()
        ),
        "updated_at": (
            GENERATED_AT.isoformat()
        ),
    }


def _session_row() -> dict[
    str,
    object,
]:
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
        "starts_at": STARTS_AT.isoformat(),
        "ends_at": ENDS_AT.isoformat(),
        "status": "planned",
        "origin": "generated",
        "notes": None,
        "created_at": (
            GENERATED_AT.isoformat()
        ),
        "updated_at": (
            GENERATED_AT.isoformat()
        ),
    }


def _request(
) -> GeneratedStudyPlanPersistenceRequest:
    return GeneratedStudyPlanPersistenceRequest(
        title="Finals Plan",
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
        generated_at=GENERATED_AT,
        sessions=(
            GeneratedStudySession(
                task_id=TASK_ID,
                subject_id=SUBJECT_ID,
                title="Review Chapter 4",
                starts_at=STARTS_AT,
                ends_at=ENDS_AT,
                duration_minutes=60,
            ),
        ),
    )


def test_repository_persists_generated_metadata() -> None:
    """Generated rows should be marked as generated."""

    plan_query = FakeQuery(
        response_data=[
            _plan_row(),
        ],
    )

    session_query = FakeQuery(
        response_data=[
            _session_row(),
        ],
    )

    repository = GeneratedStudyPlanRepository(
        FakeClient(
            plan_query=plan_query,
            session_query=session_query,
        )
    )

    result = repository.persist_generated_plan(
        user_id=USER_ID,
        request=_request(),
    )

    assert result.plan.id == PLAN_ID
    assert result.sessions[0].id == SESSION_ID

    plan_insert = next(
        value
        for operation, value in plan_query.calls
        if operation == "insert"
    )

    assert isinstance(
        plan_insert,
        dict,
    )

    assert (
        plan_insert[
            "generation_mode"
        ]
        == "generated"
    )

    session_insert = next(
        value
        for operation, value in session_query.calls
        if operation == "insert"
    )

    assert isinstance(
        session_insert,
        list,
    )

    assert (
        session_insert[0][
            "origin"
        ]
        == "generated"
    )

    assert (
        session_insert[0][
            "user_id"
        ]
        == str(
            USER_ID,
        )
    )


def test_repository_uses_generated_timestamp() -> None:
    """The generated timestamp should be persisted."""

    plan_query = FakeQuery(
        response_data=[
            _plan_row(),
        ],
    )

    repository = GeneratedStudyPlanRepository(
        FakeClient(
            plan_query=plan_query,
            session_query=FakeQuery(
                response_data=[
                    _session_row(),
                ],
            ),
        )
    )

    repository.persist_generated_plan(
        user_id=USER_ID,
        request=_request(),
    )

    plan_insert = next(
        value
        for operation, value in plan_query.calls
        if operation == "insert"
    )

    assert (
        plan_insert[
            "generated_at"
        ]
        == GENERATED_AT.isoformat()
    )


def test_repository_rolls_back_plan_on_session_failure() -> None:
    """Session persistence failure should trigger cleanup."""

    plan_query = FakeQuery(
        response_data=[
            _plan_row(),
        ],
    )

    session_query = FakeQuery(
        error=RuntimeError(
            "session insert failed",
        ),
    )

    repository = GeneratedStudyPlanRepository(
        FakeClient(
            plan_query=plan_query,
            session_query=session_query,
        )
    )

    with pytest.raises(
        StudyPlanPersistenceError,
    ):
        repository.persist_generated_plan(
            user_id=USER_ID,
            request=_request(),
        )

    assert (
        "delete",
        None,
    ) in plan_query.calls

    assert (
        "eq",
        (
            "user_id",
            str(
                USER_ID,
            ),
        ),
    ) in plan_query.calls

    assert (
        "eq",
        (
            "id",
            str(
                PLAN_ID,
            ),
        ),
    ) in plan_query.calls


def test_repository_preserves_plan_identifier_type() -> None:
    """Persisted plan identifiers should remain UUID values."""

    repository = GeneratedStudyPlanRepository(
        FakeClient(
            plan_query=FakeQuery(
                response_data=[
                    _plan_row(),
                ],
            ),
            session_query=FakeQuery(
                response_data=[
                    _session_row(),
                ],
            ),
        )
    )

    result = repository.persist_generated_plan(
        user_id=USER_ID,
        request=_request(),
    )

    assert isinstance(
        result.plan.id,
        UUID,
    )