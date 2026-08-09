# File: /backend/app/repositories/academic_task_repository.py
# Purpose: Persists and reads authenticated students'
# academic tasks through Supabase.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, Self
from uuid import UUID

from pydantic import ValidationError

from app.schemas.academic_task import (
    AcademicTaskCreateRequest,
    AcademicTaskResponse,
    AcademicTaskUpdateRequest,
)
from app.services.academic_task_errors import (
    AcademicTaskPersistenceError,
    AcademicTaskResponseError,
    AcademicTaskValidationError,
)

_ACADEMIC_TASK_COLUMNS = (
    "id,"
    "subject_id,"
    "title,"
    "description,"
    "deadline,"
    "estimated_minutes,"
    "difficulty,"
    "task_type,"
    "status,"
    "created_at,"
    "updated_at"
)

_MAX_ACADEMIC_TASK_LIST_LIMIT = 100


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

    def update(
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


class AcademicTaskRepository:
    """Reads and persists academic tasks owned by one student."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def create_academic_task(
        self,
        *,
        user_id: UUID,
        request: AcademicTaskCreateRequest,
    ) -> AcademicTaskResponse:
        """Create and return one student-owned academic task."""

        payload = request.model_dump(
            mode="json",
        )

        payload[
            "user_id"
        ] = str(
            user_id,
        )

        response = self._execute(
            self._client
            .table(
                "academic_tasks",
            )
            .insert(
                payload,
            )
            .select(
                _ACADEMIC_TASK_COLUMNS,
            ),
            operation="create the academic task",
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise AcademicTaskResponseError(
                "The created academic-task response was invalid.",
            )

        return self._parse_academic_task(
            rows[0],
        )

    def list_academic_tasks(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
    ) -> list[
        AcademicTaskResponse
    ]:
        """List academic tasks belonging to one student."""

        if (
            isinstance(
                limit,
                bool,
            )
            or not isinstance(
                limit,
                int,
            )
            or not 1 <= limit <= _MAX_ACADEMIC_TASK_LIST_LIMIT
        ):
            raise AcademicTaskValidationError(
                "Academic-task list limit must be between "
                "1 and 100.",
            )

        response = self._execute(
            self._client
            .table(
                "academic_tasks",
            )
            .select(
                _ACADEMIC_TASK_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "deadline",
                desc=False,
            )
            .limit(
                limit,
            ),
            operation="list academic tasks",
        )

        return [
            self._parse_academic_task(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]

    def get_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> AcademicTaskResponse | None:
        """Return one owned academic task when it exists."""

        response = self._execute(
            self._client
            .table(
                "academic_tasks",
            )
            .select(
                _ACADEMIC_TASK_COLUMNS,
            )
            .eq(
                "id",
                str(
                    task_id,
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
            operation="load the academic task",
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise AcademicTaskResponseError(
                "The academic-task lookup response was invalid.",
            )

        return self._parse_academic_task(
            rows[0],
        )

    def update_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        request: AcademicTaskUpdateRequest,
    ) -> AcademicTaskResponse | None:
        """Update one academic task belonging to the student."""

        payload = request.model_dump(
            mode="json",
            exclude_unset=True,
        )

        response = self._execute(
            self._client
            .table(
                "academic_tasks",
            )
            .update(
                payload,
            )
            .eq(
                "id",
                str(
                    task_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .select(
                _ACADEMIC_TASK_COLUMNS,
            ),
            operation="update the academic task",
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise AcademicTaskResponseError(
                "The updated academic-task response was invalid.",
            )

        return self._parse_academic_task(
            rows[0],
        )

    def delete_academic_task(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
    ) -> bool:
        """Delete one academic task belonging to the student."""

        response = self._execute(
            self._client
            .table(
                "academic_tasks",
            )
            .delete()
            .eq(
                "id",
                str(
                    task_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .select(
                "id",
            ),
            operation="delete the academic task",
        )

        rows = self._extract_rows(
            response,
        )

        return bool(
            rows,
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
            raise AcademicTaskPersistenceError(
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
        """Validate and normalize Supabase response rows."""

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
            raise AcademicTaskResponseError(
                "Supabase returned invalid academic-task data.",
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
                raise AcademicTaskResponseError(
                    "Supabase returned an invalid "
                    "academic-task row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_academic_task(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> AcademicTaskResponse:
        """Parse one database row into a safe task response."""

        try:
            return AcademicTaskResponse.model_validate(
                row,
            )

        except ValidationError as exc:
            raise AcademicTaskResponseError(
                "The stored academic-task data was invalid.",
            ) from exc