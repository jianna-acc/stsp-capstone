# File: /backend/tests/test_analytics_repository.py
# Purpose: Verifies owner-scoped canonical Analytics repository queries.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID

import pytest

from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.services.analytics_errors import (
    AnalyticsRepositoryError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

ATTEMPT_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)


class FakeResponse:
    """Minimal Supabase response used by repository tests."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record one Supabase query chain."""

    def __init__(
        self,
        rows: object,
    ) -> None:
        self.rows = rows
        self.selected_columns: str | None = None
        self.filters: list[
            tuple[
                str,
                object,
            ]
        ] = []
        self.orderings: list[
            tuple[
                str,
                bool,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> Self:
        self.selected_columns = columns
        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self:
        self.filters.append(
            (
                column,
                value,
            ),
        )
        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> Self:
        self.orderings.append(
            (
                column,
                desc,
            ),
        )
        return self

    def execute(
        self,
    ) -> FakeResponse:
        return FakeResponse(
            self.rows,
        )


class FakeClient:
    """Return deterministic query objects for Analytics reads."""

    def __init__(self) -> None:
        self.tables: list[str] = []
        self.queries: list[FakeQuery] = []

        self.rows_by_table: dict[
            str,
            object,
        ] = {
            "subjects": [
                {
                    "id": "subject-1",
                },
                {
                    "id": "subject-2",
                },
            ],
            "study_files": [
                {
                    "id": "file-1",
                },
                {
                    "id": "file-2",
                },
                {
                    "id": "file-3",
                },
            ],
            "quiz_attempts": [
                {
                    "id": str(
                        ATTEMPT_ID,
                    ),
                    "correct_count": 8,
                    "question_count": 10,
                    "completed_at": (
                        "2026-08-10T04:00:00+00:00"
                    ),
                },
            ],
            "quiz_attempt_answers": [
                {
                    "topic": "Algebra",
                    "is_correct": True,
                },
                {
                    "topic": "Algebra",
                    "is_correct": False,
                },
            ],
        }

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        self.tables.append(
            table_name,
        )

        query = FakeQuery(
            self.rows_by_table[
                table_name
            ],
        )

        self.queries.append(
            query,
        )

        return query


def test_subject_count_is_scoped_to_authenticated_user() -> None:
    """Subject Analytics must include the authenticated owner filter."""

    client = FakeClient()
    repository = AnalyticsRepository(
        client,
    )

    result = repository.count_subjects(
        user_id=USER_ID,
    )

    assert result == 2

    query = client.queries[0]

    assert query.selected_columns == "id"
    assert query.filters == [
        (
            "user_id",
            str(USER_ID),
        ),
    ]


def test_study_file_count_is_scoped_to_authenticated_user() -> None:
    """Study-material Analytics must include the owner filter."""

    client = FakeClient()
    repository = AnalyticsRepository(
        client,
    )

    result = repository.count_study_files(
        user_id=USER_ID,
    )

    assert result == 3

    query = client.queries[0]

    assert query.filters == [
        (
            "user_id",
            str(USER_ID),
        ),
    ]


def test_ready_study_file_count_adds_ready_filter() -> None:
    """Ready-material Analytics filters by owner and readiness."""

    client = FakeClient()
    repository = AnalyticsRepository(
        client,
    )

    result = repository.count_ready_study_files(
        user_id=USER_ID,
    )

    assert result == 3

    query = client.queries[0]

    assert query.filters == [
        (
            "user_id",
            str(USER_ID),
        ),
        (
            "processing_status",
            "ready",
        ),
    ]


def test_completed_quiz_attempts_are_owner_scoped() -> None:
    """Quiz performance reads only completed attempts for the user."""

    client = FakeClient()
    repository = AnalyticsRepository(
        client,
    )

    attempts = repository.list_completed_quiz_attempts(
        user_id=USER_ID,
    )

    assert len(
        attempts,
    ) == 1

    attempt = attempts[0]

    assert attempt.id == ATTEMPT_ID
    assert attempt.correct_count == 8
    assert attempt.question_count == 10
    assert attempt.completed_at == datetime(
        2026,
        8,
        10,
        4,
        0,
        tzinfo=timezone.utc,
    )

    query = client.queries[0]

    assert query.selected_columns == (
        "id,"
        "correct_count,"
        "question_count,"
        "completed_at"
    )

    assert query.filters == [
        (
            "user_id",
            str(USER_ID),
        ),
        (
            "status",
            "completed",
        ),
    ]

    assert query.orderings == [
        (
            "completed_at",
            True,
        ),
    ]


def test_quiz_answers_are_scoped_to_selected_attempt() -> None:
    """Topic evidence must come only from the selected Quiz attempt."""

    client = FakeClient()
    repository = AnalyticsRepository(
        client,
    )

    answers = repository.list_quiz_attempt_answers(
        attempt_id=ATTEMPT_ID,
    )

    assert [
        (
            answer.topic,
            answer.is_correct,
        )
        for answer in answers
    ] == [
        (
            "Algebra",
            True,
        ),
        (
            "Algebra",
            False,
        ),
    ]

    query = client.queries[0]

    assert query.selected_columns == "topic,is_correct"

    assert query.filters == [
        (
            "attempt_id",
            str(ATTEMPT_ID),
        ),
    ]

    assert query.orderings == [
        (
            "answered_at",
            False,
        ),
    ]


def test_invalid_supabase_response_becomes_controlled_error() -> None:
    """Malformed canonical responses must become Analytics errors."""

    client = FakeClient()

    client.rows_by_table[
        "subjects"
    ] = {
        "unexpected": "mapping",
    }

    repository = AnalyticsRepository(
        client,
    )

    with pytest.raises(
        AnalyticsRepositoryError,
        match="invalid response",
    ):
        repository.count_subjects(
            user_id=USER_ID,
        )


def test_invalid_completed_quiz_attempt_is_rejected() -> None:
    """Invalid persisted Quiz counts must not reach Analytics."""

    client = FakeClient()

    client.rows_by_table[
        "quiz_attempts"
    ] = [
        {
            "id": str(
                ATTEMPT_ID,
            ),
            "correct_count": 11,
            "question_count": 10,
            "completed_at": (
                "2026-08-10T04:00:00+00:00"
            ),
        },
    ]

    repository = AnalyticsRepository(
        client,
    )

    with pytest.raises(
        AnalyticsRepositoryError,
        match="counts are invalid",
    ):
        repository.list_completed_quiz_attempts(
            user_id=USER_ID,
        )