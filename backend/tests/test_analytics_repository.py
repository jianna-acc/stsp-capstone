# File: /backend/tests/test_analytics_repository.py
# Purpose: Verifies owner-scoped canonical Analytics repository queries.

from __future__ import annotations

from typing import Self
from uuid import UUID

import pytest

from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_errors import AnalyticsRepositoryError

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
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

    def execute(
        self,
    ) -> FakeResponse:
        return FakeResponse(
            self.rows,
        )


class FakeClient:
    """Return deterministic query objects for table reads."""

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
    """Subject analytics must include the authenticated user filter."""

    client = FakeClient()
    repository = AnalyticsRepository(
        client,
    )

    result = repository.count_subjects(
        user_id=USER_ID,
    )

    assert result == 2
    assert client.tables == [
        "subjects",
    ]

    query = client.queries[0]

    assert query.selected_columns == "id"
    assert query.filters == [
        (
            "user_id",
            str(USER_ID),
        ),
    ]


def test_study_file_count_is_scoped_to_authenticated_user() -> None:
    """Study material counts must include the owner filter."""

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
    """Ready-material analytics must filter by owner and readiness."""

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


def test_invalid_supabase_data_becomes_controlled_error() -> None:
    """Malformed canonical data must become a feature-level error."""

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