# File: /backend/tests/test_study_activity_repository.py
# Purpose: Verifies trusted Study Activity persistence,
# ownership filters, scheduled targets, and transition RPC calls.

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

from app.repositories.study_activity_repository import (
    StudyActivityRepository,
)
from app.schemas.study_activity import (
    StudyActivityMode,
    StudyActivityStatus,
    StudyActivityTransitionAction,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

PLAN_ID = UUID(
    "33333333-3333-4333-8333-333333333333",
)

SESSION_ID = UUID(
    "44444444-4444-4444-8444-444444444444",
)

ACTIVITY_ID = UUID(
    "55555555-5555-4555-8555-555555555555",
)


def _running_activity_row() -> dict[str, object]:
    """Return valid persisted running timer data."""

    return {
        "id": str(
            ACTIVITY_ID,
        ),
        "subject_id": str(
            SUBJECT_ID,
        ),
        "study_plan_id": str(
            PLAN_ID,
        ),
        "study_session_id": str(
            SESSION_ID,
        ),
        "title": "Biology review",
        "status": "running",
        "mode": "focus",
        "started_at": "2026-08-12T06:00:00+00:00",
        "ended_at": None,
        "segment_started_at": (
            "2026-08-12T06:00:00+00:00"
        ),
        "break_ends_at": None,
        "focus_seconds": 0,
        "break_seconds": 0,
        "created_at": "2026-08-12T06:00:00+00:00",
        "updated_at": "2026-08-12T06:00:00+00:00",
    }


def _paused_activity_row() -> dict[str, object]:
    """Return valid persisted paused timer data."""

    row = _running_activity_row()

    row.update(
        {
            "status": "paused",
            "mode": "focus",
            "segment_started_at": None,
            "focus_seconds": 1500,
            "updated_at": (
                "2026-08-12T06:25:00+00:00"
            ),
        },
    )

    return row


def _break_activity_row() -> dict[str, object]:
    row = _running_activity_row()

    row.update(
        {
            "mode": "break",
            "segment_started_at": (
                "2026-08-12T06:25:00+00:00"
            ),
            "break_ends_at": (
                "2026-08-12T06:35:00+00:00"
            ),
            "focus_seconds": 1500,
            "updated_at": (
                "2026-08-12T06:25:00+00:00"
            ),
        },
    )

    return row


class FakeQuery:
    """Small chainable PostgREST query double."""

    def __init__(
        self,
        data: list[
            dict[
                str,
                object,
            ]
        ],
    ) -> None:
        self.data = data

        self.selected_columns: str | None = None

        self.insert_payload: (
            dict[
                str,
                object,
            ]
            | None
        ) = None

        self.filters: list[
            tuple[
                str,
                str,
                object,
            ]
        ] = []

        self.limit_count: int | None = None

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.selected_columns = columns

        return self

    def insert(
        self,
        payload: dict[
            str,
            object,
        ],
    ) -> FakeQuery:
        self.insert_payload = dict(
            payload,
        )

        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.filters.append(
            (
                "eq",
                column,
                value,
            ),
        )

        return self

    def neq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.filters.append(
            (
                "neq",
                column,
                value,
            ),
        )

        return self

    def limit(
        self,
        count: int,
    ) -> FakeQuery:
        self.limit_count = count

        return self

    def execute(
        self,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            data=self.data,
        )


class FakeClient:
    """Record table and RPC operations from the repository."""

    def __init__(
        self,
        *,
        table_data: dict[
            str,
            list[
                dict[
                    str,
                    object,
                ]
            ],
        ]
        | None = None,
        rpc_data: list[
            dict[
                str,
                object,
            ]
        ]
        | None = None,
    ) -> None:
        self.table_data = (
            table_data
            or {}
        )

        self.rpc_data = (
            rpc_data
            or []
        )

        self.table_queries: list[
            tuple[
                str,
                FakeQuery,
            ]
        ] = []

        self.rpc_calls: list[
            tuple[
                str,
                dict[
                    str,
                    object,
                ],
                FakeQuery,
            ]
        ] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        query = FakeQuery(
            self.table_data.get(
                table_name,
                [],
            ),
        )

        self.table_queries.append(
            (
                table_name,
                query,
            ),
        )

        return query

    def rpc(
        self,
        function_name: str,
        params: dict[
            str,
            object,
        ],
    ) -> FakeQuery:
        query = FakeQuery(
            self.rpc_data,
        )

        self.rpc_calls.append(
            (
                function_name,
                dict(
                    params,
                ),
                query,
            ),
        )

        return query


def test_get_active_activity_filters_by_owner_and_unfinished_state() -> None:
    """Active lookup must remain student scoped."""

    client = FakeClient(
        table_data={
            "study_activity_sessions": [
                _running_activity_row(),
            ],
        },
    )

    repository = StudyActivityRepository(
        client,
    )

    activity = repository.get_active_activity(
        user_id=USER_ID,
    )

    assert activity is not None
    assert activity.id == ACTIVITY_ID

    assert (
        activity.status
        is StudyActivityStatus.RUNNING
    )

    assert (
        activity.mode
        is StudyActivityMode.FOCUS
    )

    table_name, query = (
        client.table_queries[-1]
    )

    assert (
        table_name
        == "study_activity_sessions"
    )

    assert (
        "eq",
        "user_id",
        str(
            USER_ID,
        ),
    ) in query.filters

    assert (
        "neq",
        "status",
        "completed",
    ) in query.filters

    assert query.limit_count == 1


def test_get_active_activity_returns_none_without_unfinished_timer() -> None:
    """Students without an unfinished timer receive no activity."""

    repository = StudyActivityRepository(
        FakeClient(
            table_data={
                "study_activity_sessions": [],
            },
        ),
    )

    assert (
        repository.get_active_activity(
            user_id=USER_ID,
        )
        is None
    )


def test_get_study_session_target_reads_owned_schedule_metadata() -> None:
    """Scheduled starts must resolve metadata from the trusted database."""

    client = FakeClient(
        table_data={
            "study_sessions": [
                {
                    "id": str(
                        SESSION_ID,
                    ),
                    "study_plan_id": str(
                        PLAN_ID,
                    ),
                    "subject_id": str(
                        SUBJECT_ID,
                    ),
                    "title": "Biology review",
                },
            ],
        },
    )

    repository = StudyActivityRepository(
        client,
    )

    target = (
        repository.get_study_session_target(
            user_id=USER_ID,
            study_session_id=SESSION_ID,
        )
    )

    assert target is not None
    assert target.id == SESSION_ID
    assert target.study_plan_id == PLAN_ID
    assert target.subject_id == SUBJECT_ID
    assert target.title == "Biology review"

    _, query = (
        client.table_queries[-1]
    )

    assert (
        "eq",
        "user_id",
        str(
            USER_ID,
        ),
    ) in query.filters


def test_start_activity_persists_trusted_owner_and_links() -> None:
    """Starting a scheduled timer must write trusted ownership metadata."""

    client = FakeClient(
        table_data={
            "study_activity_sessions": [
                _running_activity_row(),
            ],
        },
    )

    repository = StudyActivityRepository(
        client,
    )

    activity = repository.start_activity(
        user_id=USER_ID,
        subject_id=SUBJECT_ID,
        title="Biology review",
        study_plan_id=PLAN_ID,
        study_session_id=SESSION_ID,
    )

    assert activity.id == ACTIVITY_ID

    table_name, query = (
        client.table_queries[-1]
    )

    assert (
        table_name
        == "study_activity_sessions"
    )

    assert query.insert_payload == {
        "user_id": str(
            USER_ID,
        ),
        "subject_id": str(
            SUBJECT_ID,
        ),
        "title": "Biology review",
        "status": "running",
        "mode": "focus",
        "study_plan_id": str(
            PLAN_ID,
        ),
        "study_session_id": str(
            SESSION_ID,
        ),
    }


def test_transition_activity_calls_atomic_database_rpc() -> None:
    """Pause/resume/break/end mutations must use the trusted RPC."""

    rpc_row = (
        _paused_activity_row()
    )

    rpc_row[
        "user_id"
    ] = str(
        USER_ID,
    )

    client = FakeClient(
        rpc_data=[
            rpc_row,
        ],
    )

    repository = StudyActivityRepository(
        client,
    )

    activity = repository.transition_activity(
        user_id=USER_ID,
        activity_id=ACTIVITY_ID,
        action=(
            StudyActivityTransitionAction.PAUSE
        ),
    )

    assert (
        activity.status
        is StudyActivityStatus.PAUSED
    )

    assert not hasattr(
        activity,
        "user_id",
    )

    function_name, params, _ = (
        client.rpc_calls[-1]
    )

    assert (
        function_name
        == "transition_study_activity_session"
    )

    assert params == {
        "p_user_id": str(
            USER_ID,
        ),
        "p_activity_id": str(
            ACTIVITY_ID,
        ),
        "p_action": "pause",
    }

def test_start_break_calls_duration_aware_rpc() -> None:
    rpc_row = _break_activity_row()
    rpc_row["user_id"] = str(
        USER_ID,
    )

    client = FakeClient(
        rpc_data=[
            rpc_row,
        ],
    )

    repository = StudyActivityRepository(
        client,
    )

    activity = repository.start_break(
        user_id=USER_ID,
        activity_id=ACTIVITY_ID,
        duration_minutes=10,
    )

    assert activity.mode is StudyActivityMode.BREAK
    assert activity.break_ends_at is not None

    function_name, params, _ = (
        client.rpc_calls[-1]
    )

    assert (
        function_name
        == "start_timed_study_activity_break"
    )

    assert params == {
        "p_user_id": str(
            USER_ID,
        ),
        "p_activity_id": str(
            ACTIVITY_ID,
        ),
        "p_break_minutes": 10,
    }

