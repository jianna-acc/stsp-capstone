# File: /backend/app/repositories/analytics_repository.py
# Purpose: Reads authenticated student-owned canonical data for analytics.

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, Self
from uuid import UUID

from app.services.analytics_errors import AnalyticsRepositoryError


class _SupabaseResponse(
    Protocol,
):
    data: object


class _SupabaseQuery(
    Protocol,
):
    def select(
        self,
        columns: str,
    ) -> Self: ...

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseClient(
    Protocol,
):
    def table(
        self,
        table_name: str,
    ) -> _SupabaseQuery: ...


class AnalyticsRepository:
    """Reads canonical student-owned records used by Analytics."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def count_subjects(
        self,
        *,
        user_id: UUID,
    ) -> int:
        """Count subjects belonging to one authenticated student."""

        query = (
            self._client.table(
                "subjects",
            )
            .select(
                "id",
            )
            .eq(
                "user_id",
                str(user_id),
            )
        )

        return self._execute_count(
            query,
        )

    def count_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int:
        """Count study files belonging to one authenticated student."""

        query = (
            self._client.table(
                "study_files",
            )
            .select(
                "id",
            )
            .eq(
                "user_id",
                str(user_id),
            )
        )

        return self._execute_count(
            query,
        )

    def count_ready_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int:
        """Count ready study files belonging to one student."""

        query = (
            self._client.table(
                "study_files",
            )
            .select(
                "id",
            )
            .eq(
                "user_id",
                str(user_id),
            )
            .eq(
                "processing_status",
                "ready",
            )
        )

        return self._execute_count(
            query,
        )

    def _execute_count(
        self,
        query: _SupabaseQuery,
    ) -> int:
        """Execute one canonical count query and validate its rows."""

        response = query.execute()

        try:
            return self._count_rows(
                response.data,
            )
        except TypeError as exc:
            raise AnalyticsRepositoryError(
                "Analytics data source returned an invalid response.",
            ) from exc

    @staticmethod
    def _count_rows(
        data: object,
    ) -> int:
        """Count rows from a validated Supabase list response."""

        if not isinstance(
            data,
            Sequence,
        ) or isinstance(
            data,
            str | bytes,
        ):
            raise TypeError(
                "Supabase returned an invalid analytics response.",
            )

        return len(data)