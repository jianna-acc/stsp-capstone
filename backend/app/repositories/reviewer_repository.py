# File: /backend/app/repositories/reviewer_repository.py
# Purpose: Persists and reads authenticated students'
# generated reviewers through Supabase.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, Self
from uuid import UUID

from pydantic import ValidationError

from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerLength,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
)
from app.services.reviewer_errors import (
    ReviewerPersistenceError,
    ReviewerResponseError,
    ReviewerValidationError,
)

_REVIEWER_COLUMNS = (
    "id,"
    "subject_id,"
    "study_file_id,"
    "scope_type,"
    "title,"
    "reviewer_length,"
    "content,"
    "sources,"
    "generation_model,"
    "generation_count,"
    "generated_at,"
    "created_at,"
    "updated_at"
)

_MAX_REVIEWER_LIST_LIMIT = 100


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


class ReviewerRepository:
    """Reads and persists reviewers belonging to one student."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def create_reviewer(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: ReviewerScopeType,
        title: str,
        reviewer_length: ReviewerLength,
        content: ReviewerContent,
        sources: Sequence[
            ReviewerSource,
        ],
        generation_model: str,
    ) -> ReviewerResponse:
        """Save and return one generated reviewer."""

        normalized_title = title.strip()
        normalized_model = generation_model.strip()

        if not normalized_title:
            raise ReviewerValidationError(
                "Reviewer title must not be empty.",
            )

        if not normalized_model:
            raise ReviewerValidationError(
                "Reviewer generation model must not be empty.",
            )

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
            "scope_type": scope_type.value,
            "title": normalized_title,
            "reviewer_length": (
                reviewer_length.value
            ),
            "content": content.model_dump(
                mode="json",
            ),
            "sources": [
                source.model_dump(
                    mode="json",
                )
                for source in sources
            ],
            "generation_model": normalized_model,
        }

        if study_file_id is not None:
            payload[
                "study_file_id"
            ] = str(
                study_file_id,
            )

        response = self._execute(
            self._client
            .table(
                "reviewers",
            )
            .insert(
                payload,
            )
            .select(
                _REVIEWER_COLUMNS,
            ),
            operation="create the reviewer",
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise ReviewerResponseError(
                "The created reviewer response was invalid.",
            )

        return self._parse_reviewer(
            rows[0],
        )

    def list_reviewers(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> list[
        ReviewerResponse
    ]:
        """List reviewers owned by one student."""

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= _MAX_REVIEWER_LIST_LIMIT
        ):
            raise ReviewerValidationError(
                "Reviewer list limit must be between "
                "1 and 100.",
            )

        response = self._execute(
            self._client
            .table(
                "reviewers",
            )
            .select(
                _REVIEWER_COLUMNS,
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
            operation="list reviewers",
        )

        return [
            self._parse_reviewer(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]

    def get_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse | None:
        """Return one owned reviewer when it exists."""

        response = self._execute(
            self._client
            .table(
                "reviewers",
            )
            .select(
                _REVIEWER_COLUMNS,
            )
            .eq(
                "id",
                str(
                    reviewer_id,
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
            operation="load the reviewer",
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise ReviewerResponseError(
                "The reviewer lookup response was invalid.",
            )

        return self._parse_reviewer(
            rows[0],
        )

    def delete_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> bool:
        """Delete one reviewer belonging to the student."""

        response = self._execute(
            self._client
            .table(
                "reviewers",
            )
            .delete()
            .select(
                "id",
            )
            .eq(
                "id",
                str(
                    reviewer_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            ),
            operation="delete the reviewer",
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
            raise ReviewerPersistenceError(
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
            isinstance(data, (str, bytes))
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise ReviewerResponseError(
                "Supabase returned invalid reviewer data.",
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
                raise ReviewerResponseError(
                    "Supabase returned an invalid reviewer row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_reviewer(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> ReviewerResponse:
        """Parse one database row into a safe response."""

        try:
            return ReviewerResponse.model_validate(
                row,
            )

        except ValidationError as exc:
            raise ReviewerResponseError(
                "The stored reviewer data was invalid.",
            ) from exc