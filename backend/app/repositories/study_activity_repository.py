# File: /backend/app/repositories/study_activity_repository.py
# Purpose: Reads and persists authenticated actual study-activity
# timer sessions through the trusted Supabase client.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, Self
from uuid import UUID

from postgrest.exceptions import APIError
from pydantic import ValidationError

from app.schemas.study_activity import (
    StudyActivityResponse,
    StudyActivityTransitionAction,
)
from app.services.study_activity_errors import (
    StudyActivityConflictError,
    StudyActivityNotFoundError,
    StudyActivityPersistenceError,
    StudyActivityResponseError,
    StudyActivityValidationError,
)

_STUDY_ACTIVITY_COLUMNS = (
    "id,"
    "subject_id,"
    "study_plan_id,"
    "study_session_id,"
    "title,"
    "status,"
    "mode,"
    "started_at,"
    "ended_at,"
    "segment_started_at,"
    "break_ends_at,"
    "focus_seconds,"
    "break_seconds,"
    "created_at,"
    "updated_at"
)


@dataclass(
    frozen=True,
    slots=True,
)
class StudyActivityStudySessionTarget:
    """Owned scheduled session metadata used to start a timer."""

    id: UUID
    study_plan_id: UUID
    subject_id: UUID
    title: str


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

    def insert(
        self,
        payload: Mapping[
            str,
            object,
        ],
    ) -> Self: ...

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def neq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def limit(
        self,
        count: int,
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

    def rpc(
        self,
        function_name: str,
        params: Mapping[
            str,
            object,
        ],
    ) -> _SupabaseQuery: ...


class StudyActivityRepository:
    """Persists actual study-time evidence for one authenticated student."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def get_active_activity(
        self,
        *,
        user_id: UUID,
    ) -> StudyActivityResponse | None:
        """Return the student's unfinished timer when one exists."""

        response = self._execute(
            (
                self._client
                .table(
                    "study_activity_sessions",
                )
                .select(
                    _STUDY_ACTIVITY_COLUMNS,
                )
                .eq(
                    "user_id",
                    str(
                        user_id,
                    ),
                )
                .neq(
                    "status",
                    "completed",
                )
                .limit(
                    1,
                )
            ),
            operation="load active study activity",
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(
            rows,
        ) != 1:
            raise StudyActivityResponseError(
                "The active study activity response was invalid.",
            )

        return self._parse_activity(
            rows[0],
        )

    def subject_exists(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
    ) -> bool:
        """Return whether one subject belongs to the student."""

        response = self._execute(
            (
                self._client
                .table(
                    "subjects",
                )
                .select(
                    "id",
                )
                .eq(
                    "id",
                    str(
                        subject_id,
                    ),
                )
                .eq(
                    "user_id",
                    str(
                        user_id,
                    ),
                )
                .limit(
                    1,
                )
            ),
            operation="validate study activity subject",
        )

        return bool(
            self._extract_rows(
                response,
            ),
        )

    def study_plan_exists(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> bool:
        """Return whether one study plan belongs to the student."""

        response = self._execute(
            (
                self._client
                .table(
                    "study_plans",
                )
                .select(
                    "id",
                )
                .eq(
                    "id",
                    str(
                        study_plan_id,
                    ),
                )
                .eq(
                    "user_id",
                    str(
                        user_id,
                    ),
                )
                .limit(
                    1,
                )
            ),
            operation="validate study activity plan",
        )

        return bool(
            self._extract_rows(
                response,
            ),
        )

    def get_study_session_target(
        self,
        *,
        user_id: UUID,
        study_session_id: UUID,
    ) -> StudyActivityStudySessionTarget | None:
        """Return one owned scheduled session used to start studying."""

        response = self._execute(
            (
                self._client
                .table(
                    "study_sessions",
                )
                .select(
                    "id,study_plan_id,subject_id,title",
                )
                .eq(
                    "id",
                    str(
                        study_session_id,
                    ),
                )
                .eq(
                    "user_id",
                    str(
                        user_id,
                    ),
                )
                .limit(
                    1,
                )
            ),
            operation="load scheduled study activity target",
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(
            rows,
        ) != 1:
            raise StudyActivityResponseError(
                "The scheduled study activity target response was invalid.",
            )

        return self._parse_study_session_target(
            rows[0],
        )

    def start_activity(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        title: str,
        study_plan_id: UUID | None,
        study_session_id: UUID | None,
    ) -> StudyActivityResponse:
        """Create one running focus timer."""

        payload: dict[
            str,
            object,
        ] = {
            "user_id": str(
                user_id,
            ),
            "subject_id": str(
                subject_id,
            ),
            "title": title,
            "status": "running",
            "mode": "focus",
        }

        if study_plan_id is not None:
            payload[
                "study_plan_id"
            ] = str(
                study_plan_id,
            )

        if study_session_id is not None:
            payload[
                "study_session_id"
            ] = str(
                study_session_id,
            )

        try:
            response = (
                self._client
                .table(
                    "study_activity_sessions",
                )
                .insert(
                    payload,
                )
                .select(
                    _STUDY_ACTIVITY_COLUMNS,
                )
                .execute()
            )

        except APIError as exc:
            self._raise_start_api_error(
                exc,
            )

        except Exception as exc:
            raise StudyActivityPersistenceError(
                "Unable to start study activity.",
            ) from exc

        rows = self._extract_rows(
            response,
        )

        if len(
            rows,
        ) != 1:
            raise StudyActivityResponseError(
                "The created study activity response was invalid.",
            )

        return self._parse_activity(
            rows[0],
        )


    def start_break(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        duration_minutes: int,
    ) -> StudyActivityResponse:
        """Atomically start one timed break."""

        try:
            response = (
                self._client
                .rpc(
                    "start_timed_study_activity_break",
                    {
                        "p_user_id": str(
                            user_id,
                        ),
                        "p_activity_id": str(
                            activity_id,
                        ),
                        "p_break_minutes": duration_minutes,
                    },
                )
                .execute()
            )

        except APIError as exc:
            self._raise_transition_api_error(
                exc,
            )

        except Exception as exc:
            raise StudyActivityPersistenceError(
                "Unable to start study break.",
            ) from exc

        rows = self._extract_rows(
            response,
        )

        if len(
            rows,
        ) != 1:
            raise StudyActivityResponseError(
                "The updated study activity response was invalid.",
            )

        return self._parse_activity(
            rows[0],
        )

    def transition_activity(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        action: StudyActivityTransitionAction,
    ) -> StudyActivityResponse:
        """Atomically change one owned timer state."""

        try:
            response = (
                self._client
                .rpc(
                    "transition_study_activity_session",
                    {
                        "p_user_id": str(
                            user_id,
                        ),
                        "p_activity_id": str(
                            activity_id,
                        ),
                        "p_action": action.value,
                    },
                )
                .execute()
            )

        except APIError as exc:
            self._raise_transition_api_error(
                exc,
            )

        except Exception as exc:
            raise StudyActivityPersistenceError(
                "Unable to update study activity.",
            ) from exc

        rows = self._extract_rows(
            response,
        )

        if len(
            rows,
        ) != 1:
            raise StudyActivityResponseError(
                "The updated study activity response was invalid.",
            )

        return self._parse_activity(
            rows[0],
        )

    def _execute(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one read query safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise StudyActivityPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _extract_rows(
        self,
        response: _SupabaseResponse,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Validate Supabase row data."""

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            isinstance(
                data,
                (str, bytes),
            )
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise StudyActivityResponseError(
                "Supabase returned invalid Study Activity data.",
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
                raise StudyActivityResponseError(
                    "Supabase returned an invalid Study Activity row.",
                )

            rows.append(
                item,
            )

        return rows

    @staticmethod
    def _parse_activity(
        row: Mapping[
            str,
            object,
        ],
    ) -> StudyActivityResponse:
        """Parse one persisted timer without exposing owner metadata."""

        public_row = dict(
            row,
        )

        public_row.pop(
            "user_id",
            None,
        )

        try:
            return StudyActivityResponse.model_validate(
                public_row,
            )

        except ValidationError as exc:
            raise StudyActivityResponseError(
                "Stored Study Activity data was invalid.",
            ) from exc

    @classmethod
    def _parse_study_session_target(
        cls,
        row: Mapping[
            str,
            object,
        ],
    ) -> StudyActivityStudySessionTarget:
        """Parse one owned scheduled timer target."""

        title = row.get(
            "title",
        )

        if not isinstance(
            title,
            str,
        ) or not title.strip():
            raise StudyActivityResponseError(
                "Stored study-session title was invalid.",
            )

        return StudyActivityStudySessionTarget(
            id=cls._parse_uuid(
                row.get(
                    "id",
                ),
            ),
            study_plan_id=cls._parse_uuid(
                row.get(
                    "study_plan_id",
                ),
            ),
            subject_id=cls._parse_uuid(
                row.get(
                    "subject_id",
                ),
            ),
            title=title.strip(),
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
            raise StudyActivityResponseError(
                "Stored Study Activity UUID was invalid.",
            ) from exc

    @staticmethod
    def _api_error_code(
        error: APIError,
    ) -> str | None:
        """Read a Postgres/PostgREST error code safely."""

        code = getattr(
            error,
            "code",
            None,
        )

        return (
            code
            if isinstance(
                code,
                str,
            )
            else None
        )

    @classmethod
    def _raise_start_api_error(
        cls,
        error: APIError,
    ) -> None:
        """Convert protected start failures into controlled errors."""

        code = cls._api_error_code(
            error,
        )

        if code == "23505":
            raise StudyActivityConflictError(
                "A study timer is already active.",
            ) from error

        if code in {
            "23503",
            "23514",
            "P0001",
        }:
            raise StudyActivityValidationError(
                "The study activity start target is invalid.",
            ) from error

        raise StudyActivityPersistenceError(
            "Unable to start study activity.",
        ) from error

    @classmethod
    def _raise_transition_api_error(
        cls,
        error: APIError,
    ) -> None:
        """Convert trusted transition failures into controlled errors."""

        code = cls._api_error_code(
            error,
        )

        if code == "P0002":
            raise StudyActivityNotFoundError(
                "The requested study activity was not found.",
            ) from error

        if code == "P0001":
            raise StudyActivityConflictError(
                "The study timer is not in a valid state for that action.",
            ) from error

        raise StudyActivityPersistenceError(
            "Unable to update study activity.",
        ) from error