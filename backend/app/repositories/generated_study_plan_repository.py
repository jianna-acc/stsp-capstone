# File: /backend/app/repositories/generated_study_plan_repository.py
# Purpose: Persists one generated Track D study plan and its
# generated sessions using the trusted backend Supabase client.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from typing import (
    Protocol,
    Self,
)
from uuid import UUID

from pydantic import ValidationError

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceRequest,
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_plan import (
    StudyPlanResponse,
    StudySessionResponse,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
    StudyPlanResponseError,
)

_STUDY_PLAN_COLUMNS = (
    "id,title,starts_on,ends_on,status,"
    "generation_mode,generated_at,created_at,updated_at"
)

_STUDY_SESSION_COLUMNS = (
    "id,study_plan_id,subject_id,title,starts_at,ends_at,"
    "status,origin,notes,created_at,updated_at"
)


class _SupabaseResponse(
    Protocol,
):
    data: object


class _SupabaseQuery(
    Protocol,
):
    def insert(
        self,
        values: object,
    ) -> Self: ...

    def delete(
        self,
    ) -> Self: ...

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


class GeneratedStudyPlanRepository:
    """Persists generated plan output for one authenticated user."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def persist_generated_plan(
        self,
        *,
        user_id: UUID,
        request: GeneratedStudyPlanPersistenceRequest,
    ) -> GeneratedStudyPlanPersistenceResult:
        """Persist a generated plan and all generated sessions."""

        plan = self._insert_plan(
            user_id=user_id,
            request=request,
        )

        try:
            sessions = self._insert_sessions(
                user_id=user_id,
                study_plan_id=plan.id,
                request=request,
            )

        except (
            StudyPlanPersistenceError,
            StudyPlanResponseError,
        ):
            self._rollback_plan(
                user_id=user_id,
                study_plan_id=plan.id,
            )

            raise

        return GeneratedStudyPlanPersistenceResult(
            plan=plan,
            sessions=sessions,
        )

    def _insert_plan(
        self,
        *,
        user_id: UUID,
        request: GeneratedStudyPlanPersistenceRequest,
    ) -> StudyPlanResponse:
        """Insert the generated study-plan row."""

        query = (
            self._client
            .table(
                "study_plans",
            )
            .insert(
                {
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
                    "generation_mode": "generated",
                    "generated_at": (
                        request.generated_at.isoformat()
                    ),
                }
            )
            .select(
                _STUDY_PLAN_COLUMNS,
            )
        )

        rows = self._execute_rows(
            query,
            operation=(
                "persist the generated study plan"
            ),
        )

        if len(
            rows,
        ) != 1:
            raise StudyPlanResponseError(
                "Generated study-plan insert "
                "returned an unexpected response.",
            )

        try:
            return StudyPlanResponse.model_validate(
                rows[0],
            )

        except ValidationError as exc:
            raise StudyPlanResponseError(
                "Generated study-plan response was invalid.",
            ) from exc

    def _insert_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request: GeneratedStudyPlanPersistenceRequest,
    ) -> tuple[
        StudySessionResponse,
        ...,
    ]:
        """Bulk insert all generated study sessions."""

        payload = [
            {
                "study_plan_id": str(
                    study_plan_id,
                ),
                "user_id": str(
                    user_id,
                ),
                "subject_id": str(
                    session.subject_id,
                ),
                "title": session.title,
                "starts_at": (
                    session.starts_at.isoformat()
                ),
                "ends_at": (
                    session.ends_at.isoformat()
                ),
                "status": "planned",
                "origin": "generated",
                "notes": None,
            }
            for session in request.sessions
        ]

        query = (
            self._client
            .table(
                "study_sessions",
            )
            .insert(
                payload,
            )
            .select(
                _STUDY_SESSION_COLUMNS,
            )
        )

        rows = self._execute_rows(
            query,
            operation=(
                "persist generated study sessions"
            ),
        )

        if len(
            rows,
        ) != len(
            request.sessions,
        ):
            raise StudyPlanResponseError(
                "Generated session insert returned "
                "an unexpected response.",
            )

        try:
            return tuple(
                StudySessionResponse.model_validate(
                    row,
                )
                for row in rows
            )

        except ValidationError as exc:
            raise StudyPlanResponseError(
                "Generated study-session response "
                "was invalid.",
            ) from exc

    def _rollback_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> None:
        """Best-effort cleanup if session persistence fails."""

        try:
            (
                self._client
                .table(
                    "study_plans",
                )
                .delete()
                .eq(
                    "user_id",
                    str(
                        user_id,
                    ),
                )
                .eq(
                    "id",
                    str(
                        study_plan_id,
                    ),
                )
                .execute()
            )

        except Exception:  # noqa: BLE001 - rollback is best-effort cleanup
            # Preserve the original persistence failure.
            # The database FK cascade handles session cleanup
            # when this rollback succeeds.
            return

    def _execute_rows(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Execute a Supabase write and validate returned rows."""

        try:
            response = query.execute()

        except Exception as exc:
            raise StudyPlanPersistenceError(
                f"Unable to {operation}.",
            ) from exc

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
                "Supabase returned invalid generated "
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
                    "generated study-plan row.",
                )

            rows.append(
                item,
            )

        return rows