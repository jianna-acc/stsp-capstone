# File: /backend/app/repositories/analytics_repository.py
# Purpose: Reads authenticated student-owned canonical data for analytics.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, Self
from uuid import UUID

from postgrest.exceptions import APIError

from app.services.analytics_errors import AnalyticsRepositoryError


@dataclass(
    frozen=True,
    slots=True,
)
class QuizAttemptAnalyticsRecord:
    """Minimal completed Quiz-attempt evidence used by Analytics."""

    id: UUID
    correct_count: int
    question_count: int
    completed_at: datetime


@dataclass(
    frozen=True,
    slots=True,
)
class QuizAnswerAnalyticsRecord:
    """Minimal persisted Quiz-answer evidence used by Analytics."""

    topic: str
    is_correct: bool


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

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
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

    def list_completed_quiz_attempts(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        QuizAttemptAnalyticsRecord,
        ...,
    ]:
        """Return completed Quiz attempts owned by one student."""

        query = (
            self._client.table(
                "quiz_attempts",
            )
            .select(
                (
                    "id,"
                    "correct_count,"
                    "question_count,"
                    "completed_at"
                ),
            )
            .eq(
                "user_id",
                str(user_id),
            )
            .eq(
                "status",
                "completed",
            )
            .order(
                "completed_at",
                desc=True,
            )
        )

        rows = self._execute_rows(
            query,
            resource="Quiz attempts",
        )

        return tuple(
            self._parse_quiz_attempt(
                row,
            )
            for row in rows
        )

    def list_quiz_attempt_answers(
        self,
        *,
        attempt_id: UUID,
    ) -> tuple[
        QuizAnswerAnalyticsRecord,
        ...,
    ]:
        """Return canonical answers belonging to one selected attempt."""

        query = (
            self._client.table(
                "quiz_attempt_answers",
            )
            .select(
                "topic,is_correct",
            )
            .eq(
                "attempt_id",
                str(attempt_id),
            )
            .order(
                "answered_at",
                desc=False,
            )
        )

        rows = self._execute_rows(
            query,
            resource="Quiz attempt answers",
        )

        return tuple(
            self._parse_quiz_answer(
                row,
            )
            for row in rows
        )

    def _execute_count(
        self,
        query: _SupabaseQuery,
    ) -> int:
        """Execute one canonical count query and validate its rows."""

        rows = self._execute_rows(
            query,
            resource="Analytics count",
        )

        return len(
            rows,
        )

    def _execute_rows(
        self,
        query: _SupabaseQuery,
        *,
        resource: str,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Execute and validate one canonical Analytics table query."""

        try:
            response = query.execute()
        except APIError as exc:
            raise AnalyticsRepositoryError(
                f"Unable to read {resource}.",
            ) from exc

        data = response.data

        if not isinstance(
            data,
            Sequence,
        ) or isinstance(
            data,
            str | bytes,
        ):
            raise AnalyticsRepositoryError(
                "Analytics data source returned an invalid response.",
            )

        rows: list[
            Mapping[
                str,
                object,
            ]
        ] = []

        for item in data:
            if not isinstance(
                item,
                Mapping,
            ):
                raise AnalyticsRepositoryError(
                    "Analytics data source returned an invalid row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_quiz_attempt(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> QuizAttemptAnalyticsRecord:
        """Validate minimal completed Quiz-attempt Analytics evidence."""

        attempt_id = self._parse_uuid(
            row.get(
                "id",
            ),
        )

        correct_count = self._parse_integer(
            row.get(
                "correct_count",
            ),
            minimum=0,
        )

        question_count = self._parse_integer(
            row.get(
                "question_count",
            ),
            minimum=1,
        )

        if correct_count > question_count:
            raise AnalyticsRepositoryError(
                "Stored Quiz attempt counts are invalid.",
            )

        completed_at = self._parse_datetime(
            row.get(
                "completed_at",
            ),
        )

        return QuizAttemptAnalyticsRecord(
            id=attempt_id,
            correct_count=correct_count,
            question_count=question_count,
            completed_at=completed_at,
        )

    def _parse_quiz_answer(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> QuizAnswerAnalyticsRecord:
        """Validate minimal Quiz-answer Analytics evidence."""

        topic = row.get(
            "topic",
        )

        if not isinstance(
            topic,
            str,
        ) or not topic.strip():
            raise AnalyticsRepositoryError(
                "Stored Quiz answer topic is invalid.",
            )

        is_correct = row.get(
            "is_correct",
        )

        if not isinstance(
            is_correct,
            bool,
        ):
            raise AnalyticsRepositoryError(
                "Stored Quiz answer correctness is invalid.",
            )

        return QuizAnswerAnalyticsRecord(
            topic=topic.strip(),
            is_correct=is_correct,
        )

    @staticmethod
    def _parse_uuid(
        value: object,
    ) -> UUID:
        """Parse one persisted UUID."""

        try:
            return UUID(
                str(
                    value,
                ),
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise AnalyticsRepositoryError(
                "Stored Analytics UUID is invalid.",
            ) from exc

    @staticmethod
    def _parse_integer(
        value: object,
        *,
        minimum: int,
    ) -> int:
        """Parse one persisted integer with a minimum value."""

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                int,
            )
            or value < minimum
        ):
            raise AnalyticsRepositoryError(
                "Stored Analytics count is invalid.",
            )

        return value

    @staticmethod
    def _parse_datetime(
        value: object,
    ) -> datetime:
        """Parse one timezone-aware persisted timestamp."""

        if isinstance(
            value,
            datetime,
        ):
            parsed = value
        elif isinstance(
            value,
            str,
        ):
            try:
                parsed = datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    ),
                )
            except ValueError as exc:
                raise AnalyticsRepositoryError(
                    "Stored Analytics timestamp is invalid.",
                ) from exc
        else:
            raise AnalyticsRepositoryError(
                "Stored Analytics timestamp is invalid.",
            )

        if parsed.tzinfo is None:
            raise AnalyticsRepositoryError(
                "Stored Analytics timestamp must include a timezone.",
            )

        return parsed.astimezone(
            timezone.utc,
        )