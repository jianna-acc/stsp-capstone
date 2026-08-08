# File: /backend/tests/test_reviewer_repository.py
# Purpose: Verifies owned reviewer persistence,
# retrieval, listing, deletion, and response validation.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.reviewer_repository import (
    ReviewerRepository,
)
from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerDefinition,
    ReviewerLength,
    ReviewerScopeType,
    ReviewerSource,
    ReviewerTopic,
)
from app.services.reviewer_errors import (
    ReviewerPersistenceError,
    ReviewerResponseError,
    ReviewerValidationError,
)


class FakeResponse:
    """Minimal Supabase-style response."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record chained Supabase query operations."""

    def __init__(
        self,
        response_data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error
        self.operations: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.operations.append(
            (
                "select",
                columns,
            )
        )
        return self

    def insert(
        self,
        payload: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "insert",
                payload,
            )
        )
        return self

    def delete(
        self,
    ) -> FakeQuery:
        self.operations.append(
            (
                "delete",
                None,
            )
        )
        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "eq",
                (
                    column,
                    value,
                ),
            )
        )
        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> FakeQuery:
        self.operations.append(
            (
                "order",
                (
                    column,
                    desc,
                ),
            )
        )
        return self

    def limit(
        self,
        count: int,
    ) -> FakeQuery:
        self.operations.append(
            (
                "limit",
                count,
            )
        )
        return self

    def execute(
        self,
    ) -> FakeResponse:
        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.response_data,
        )


class FakeClient:
    """Minimal Supabase-style client."""

    def __init__(
        self,
        query: FakeQuery,
    ) -> None:
        self.query = query
        self.table_names: list[
            str
        ] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        self.table_names.append(
            table_name,
        )

        return self.query


def _content() -> ReviewerContent:
    return ReviewerContent(
        overview="Overview",
        topics=(
            ReviewerTopic(
                title="Topic",
                summary="Topic summary",
                key_points=(
                    "Point one",
                ),
                definitions=(
                    ReviewerDefinition(
                        term="Term",
                        definition="Definition",
                    ),
                ),
            ),
        ),
    )


def _source(
    study_file_id: UUID,
) -> ReviewerSource:
    return ReviewerSource(
        study_file_id=study_file_id,
        source_name="Lecture.pdf",
        chunk_index=0,
        locator_type="page",
        locator_label="Page 1",
    )


def _reviewer_row(
    *,
    reviewer_id: UUID | None = None,
    subject_id: UUID | None = None,
    study_file_id: UUID | None = None,
) -> dict[
    str,
    object,
]:
    now = datetime.now(
        UTC,
    ).isoformat()

    resolved_file_id = (
        study_file_id
        if study_file_id is not None
        else uuid4()
    )

    return {
        "id": str(
            reviewer_id
            if reviewer_id is not None
            else uuid4()
        ),
        "subject_id": str(
            subject_id
            if subject_id is not None
            else uuid4()
        ),
        "study_file_id": str(
            resolved_file_id,
        ),
        "scope_type": "file",
        "title": "Generated Reviewer",
        "reviewer_length": "medium",
        "content": _content().model_dump(
            mode="json",
        ),
        "sources": [
            _source(
                resolved_file_id,
            ).model_dump(
                mode="json",
            ),
        ],
        "generation_model": "gemini-3.6-flash",
        "generation_count": 1,
        "generated_at": now,
        "created_at": now,
        "updated_at": now,
    }


def test_create_reviewer_saves_owned_payload() -> None:
    """Creation must persist owner, scope, content, and sources."""

    user_id = uuid4()
    subject_id = uuid4()
    study_file_id = uuid4()

    query = FakeQuery(
        [
            _reviewer_row(
                subject_id=subject_id,
                study_file_id=study_file_id,
            )
        ],
    )

    client = FakeClient(
        query,
    )

    repository = ReviewerRepository(
        client,
    )

    result = repository.create_reviewer(
        user_id=user_id,
        subject_id=subject_id,
        study_file_id=study_file_id,
        scope_type=ReviewerScopeType.FILE,
        title="Generated Reviewer",
        reviewer_length=ReviewerLength.MEDIUM,
        content=_content(),
        sources=(
            _source(
                study_file_id,
            ),
        ),
        generation_model="gemini-3.6-flash",
    )

    assert result.subject_id == subject_id
    assert result.study_file_id == study_file_id

    assert client.table_names == [
        "reviewers",
    ]

    insert_operations = [
        value
        for operation, value in query.operations
        if operation == "insert"
    ]

    assert len(
        insert_operations,
    ) == 1

    payload = insert_operations[0]

    assert isinstance(
        payload,
        dict,
    )

    assert payload[
        "user_id"
    ] == str(
        user_id,
    )

    assert payload[
        "scope_type"
    ] == "file"

    assert payload[
        "reviewer_length"
    ] == "medium"


def test_list_reviewers_filters_by_owner() -> None:
    """Reviewer lists must always filter by user ID."""

    user_id = uuid4()

    query = FakeQuery(
        [
            _reviewer_row(),
        ],
    )

    repository = ReviewerRepository(
        FakeClient(
            query,
        ),
    )

    result = repository.list_reviewers(
        user_id=user_id,
        limit=20,
    )

    assert len(
        result,
    ) == 1

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations


def test_list_reviewer_limit_is_validated() -> None:
    """Unbounded reviewer lists must be rejected."""

    repository = ReviewerRepository(
        FakeClient(
            FakeQuery(
                [],
            ),
        ),
    )

    with pytest.raises(
        ReviewerValidationError,
    ):
        repository.list_reviewers(
            user_id=uuid4(),
            limit=101,
        )


def test_get_reviewer_filters_id_and_owner() -> None:
    """Single reviewer lookup must check both ID and owner."""

    user_id = uuid4()
    reviewer_id = uuid4()

    query = FakeQuery(
        [
            _reviewer_row(
                reviewer_id=reviewer_id,
            )
        ],
    )

    repository = ReviewerRepository(
        FakeClient(
            query,
        ),
    )

    result = repository.get_reviewer(
        user_id=user_id,
        reviewer_id=reviewer_id,
    )

    assert result is not None
    assert result.id == reviewer_id

    assert (
        "eq",
        (
            "id",
            str(
                reviewer_id,
            ),
        ),
    ) in query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations


def test_get_missing_reviewer_returns_none() -> None:
    """Missing reviewer must not be fabricated."""

    repository = ReviewerRepository(
        FakeClient(
            FakeQuery(
                [],
            ),
        ),
    )

    result = repository.get_reviewer(
        user_id=uuid4(),
        reviewer_id=uuid4(),
    )

    assert result is None


def test_delete_reviewer_filters_owner() -> None:
    """Deletion must remain ownership scoped."""

    user_id = uuid4()
    reviewer_id = uuid4()

    query = FakeQuery(
        [
            {
                "id": str(
                    reviewer_id,
                )
            }
        ],
    )

    repository = ReviewerRepository(
        FakeClient(
            query,
        ),
    )

    deleted = repository.delete_reviewer(
        user_id=user_id,
        reviewer_id=reviewer_id,
    )

    assert deleted is True

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations


def test_invalid_database_row_is_rejected() -> None:
    """Malformed persisted reviewer data must fail safely."""

    repository = ReviewerRepository(
        FakeClient(
            FakeQuery(
                [
                    {
                        "id": "invalid"
                    }
                ],
            ),
        ),
    )

    with pytest.raises(
        ReviewerResponseError,
    ):
        repository.list_reviewers(
            user_id=uuid4(),
        )


def test_database_failure_is_controlled() -> None:
    """Supabase exceptions must become reviewer errors."""

    repository = ReviewerRepository(
        FakeClient(
            FakeQuery(
                [],
                error=RuntimeError(
                    "database unavailable",
                ),
            ),
        ),
    )

    with pytest.raises(
        ReviewerPersistenceError,
    ):
        repository.list_reviewers(
            user_id=uuid4(),
        )