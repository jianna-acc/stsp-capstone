# File: /backend/app/repositories/study_plan_repository.py
# Purpose: Persists and reads authenticated students' study plans
# and study sessions through the trusted Supabase client.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, Self
from uuid import UUID

from pydantic import ValidationError

from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanResponse,
    StudySessionCreateRequest,
    StudySessionResponse,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
)

_STUDY_PLAN_COLUMNS = (
    "id,"
    "title,"
    "starts_on,"
    "ends_on,"
    "status,"
    "generation_mode,"
    "generated_at,"
    "created_at,"
    "updated_at"
)

_STUDY_SESSION_COLUMNS = (
    "id,"
    "study_plan_id,"
    "subject_id,"
    "title,"
    "starts_at,"
    "ends_at,"
    "status,"
    "origin,"
    "notes,"
    "created_at,"
    "updated_at"
)

_MAX_STUDY_PLAN_LIST_LIMIT = 100
_MAX_STUDY_SESSION_LIST_LIMIT = 200
_MAX_MANUAL_SESSION_LIST_LIMIT = 500

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

    def delete(
        self,
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


class StudyPlanRepository:
    """Reads and persists study schedules for one student."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def create_study_plan(
        self,
        *,
        user_id: UUID,
        request: StudyPlanCreateRequest,
    ) -> StudyPlanResponse:
        """Create and return one manual study plan."""

        payload: dict[
            str,
            object,
        ] = {
            "user_id": str(
                user_id,
            ),
            "title": request.title,
            "starts_on": (
                request.starts_on.isoformat()
            ),
            "ends_on": (
                request.ends_on.isoformat()
            ),
            "status": "active",
            "generation_mode": "manual",
        }

        response = self._execute(
            self._client
            .table(
                "study_plans",
            )
            .insert(
                payload,
            )
            .select(
                _STUDY_PLAN_COLUMNS,
            ),
            operation="create the study plan",
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise StudyPlanResponseError(
                "The created study-plan response "
                "was invalid.",
            )

        return self._parse_study_plan(
            rows[0],
        )

    def list_study_plans(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> list[
        StudyPlanResponse
    ]:
        """Return recent study plans belonging to one student."""

        if (
            isinstance(
                limit,
                bool,
            )
            or not isinstance(
                limit,
                int,
            )
            or not 1
            <= limit
            <= _MAX_STUDY_PLAN_LIST_LIMIT
        ):
            raise StudyPlanValidationError(
                "Study-plan list limit must be "
                "between 1 and 100.",
            )

        response = self._execute(
            self._client
            .table(
                "study_plans",
            )
            .select(
                _STUDY_PLAN_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "updated_at",
                desc=True,
            )
            .limit(
                limit,
            ),
            operation="list study plans",
        )

        return [
            self._parse_study_plan(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]

    def get_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> StudyPlanResponse | None:
        """Return one owned study plan when it exists."""

        response = self._execute(
            self._client
            .table(
                "study_plans",
            )
            .select(
                _STUDY_PLAN_COLUMNS,
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
            ),
            operation="load the study plan",
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise StudyPlanResponseError(
                "The study-plan lookup response "
                "was invalid.",
            )

        return self._parse_study_plan(
            rows[0],
        )

    def delete_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> bool:
        """Delete one study plan belonging to the student."""

        response = self._execute(
            self._client
            .table(
                "study_plans",
            )
            .delete()
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
            ),
            operation="delete the study plan",
        )

        return bool(
            self._extract_rows(
                response,
            )
        )

    def create_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request: StudySessionCreateRequest,
    ) -> StudySessionResponse:
        """Create one manually scheduled study session."""

        payload: dict[
            str,
            object,
        ] = {
            "study_plan_id": str(
                study_plan_id,
            ),
            "user_id": str(
                user_id,
            ),
            "subject_id": str(
                request.subject_id,
            ),
            "title": request.title,
            "starts_at": (
                request.starts_at.isoformat()
            ),
            "ends_at": (
                request.ends_at.isoformat()
            ),
            "status": "planned",
            "origin": "manual",
        }

        if request.notes is not None:
            payload[
                "notes"
            ] = request.notes

        response = self._execute(
            self._client
            .table(
                "study_sessions",
            )
            .insert(
                payload,
            )
            .select(
                _STUDY_SESSION_COLUMNS,
            ),
            operation="create the study session",
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise StudyPlanResponseError(
                "The created study-session response "
                "was invalid.",
            )

        return self._parse_study_session(
            rows[0],
        )

    def list_study_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        limit: int = 200,
    ) -> list[
        StudySessionResponse
    ]:
        """Return sessions belonging to one owned study plan."""

        if (
            isinstance(
                limit,
                bool,
            )
            or not isinstance(
                limit,
                int,
            )
            or not 1
            <= limit
            <= _MAX_STUDY_SESSION_LIST_LIMIT
        ):
            raise StudyPlanValidationError(
                "Study-session list limit must be "
                "between 1 and 200.",
            )

        response = self._execute(
            self._client
            .table(
                "study_sessions",
            )
            .select(
                _STUDY_SESSION_COLUMNS,
            )
            .eq(
                "study_plan_id",
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
            .order(
                "starts_at",
            )
            .limit(
                limit,
            ),
            operation="list study sessions",
        )

        return [
            self._parse_study_session(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]
    def list_manual_study_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        limit: int = 500,
    ) -> list[
        StudySessionResponse
    ]:
        """Return manual sessions belonging to one owned plan."""

        if (
            isinstance(
                limit,
                bool,
            )
            or not isinstance(
                limit,
                int,
            )
            or not 1
            <= limit
            <= _MAX_MANUAL_SESSION_LIST_LIMIT
        ):
            raise StudyPlanValidationError(
                "Manual study-session list limit must be "
                "between 1 and 500.",
            )

        response = self._execute(
            self._client
            .table(
                "study_sessions",
            )
            .select(
                _STUDY_SESSION_COLUMNS,
            )
            .eq(
                "study_plan_id",
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
            .eq(
                "origin",
                "manual",
            )
            .order(
                "starts_at",
            )
            .limit(
                limit,
            ),
            operation=(
                "list manual study sessions"
            ),
        )

        return [
            self._parse_study_session(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]
    def delete_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        study_session_id: UUID,
    ) -> bool:
        """Delete one session from an owned study plan."""

        response = self._execute(
            self._client
            .table(
                "study_sessions",
            )
            .delete()
            .select(
                "id",
            )
            .eq(
                "id",
                str(
                    study_session_id,
                ),
            )
            .eq(
                "study_plan_id",
                str(
                    study_plan_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            ),
            operation="delete the study session",
        )

        return bool(
            self._extract_rows(
                response,
            )
        )

    def _execute(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one Supabase query safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise StudyPlanPersistenceError(
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
        """Validate and normalize Supabase row data."""

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
            raise StudyPlanResponseError(
                "Supabase returned invalid "
                "study-plan data.",
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
                raise StudyPlanResponseError(
                    "Supabase returned an invalid "
                    "study-plan row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_study_plan(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> StudyPlanResponse:
        """Parse one persisted study plan."""

        try:
            return StudyPlanResponse.model_validate(
                row,
            )

        except ValidationError as exc:
            raise StudyPlanResponseError(
                "The stored study-plan data "
                "was invalid.",
            ) from exc

    def _parse_study_session(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> StudySessionResponse:
        """Parse one persisted study session."""

        try:
            return StudySessionResponse.model_validate(
                row,
            )

        except ValidationError as exc:
            raise StudyPlanResponseError(
                "The stored study-session data "
                "was invalid.",
            ) from exc