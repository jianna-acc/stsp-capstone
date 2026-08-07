# File: /backend/tests/test_study_conversation_summary_state.py
# Purpose: Tests internal summary contracts and owned repository
# operations without requiring a live Supabase database.

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.repositories.study_conversation_repository import (
    StudyConversationRepository,
)
from app.schemas.study_conversation import (
    MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS,
    StudyConversationSummaryState,
    StudyConversationSummaryUpdate,
)
from app.services.study_conversation_errors import (
    StudyConversationResponseError,
    StudyConversationValidationError,
)


@dataclass
class FakeResponse:
    data: object


class FakeQuery:
    def __init__(
        self,
        *,
        data: object,
    ) -> None:
        self.response = FakeResponse(
            data=data,
        )

        self.operations: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> Self:
        self.operations.append(
            (
                "select",
                columns,
            ),
        )

        return self

    def update(
        self,
        payload: object,
    ) -> Self:
        self.operations.append(
            (
                "update",
                payload,
            ),
        )

        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self:
        self.operations.append(
            (
                "eq",
                column,
                value,
            ),
        )

        return self

    def limit(
        self,
        count: int,
    ) -> Self:
        self.operations.append(
            (
                "limit",
                count,
            ),
        )

        return self

    def execute(
        self,
    ) -> FakeResponse:
        self.operations.append(
            (
                "execute",
            ),
        )

        return self.response


class FakeClient:
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


def summary_row(
    *,
    conversation_id: UUID,
    summary_text: str | None = None,
    summarized_message_count: int = 0,
    summary_updated_at: str | None = None,
) -> dict[
    str,
    object,
]:
    return {
        "id": str(
            conversation_id,
        ),
        "summary_text": summary_text,
        "summarized_message_count": (
            summarized_message_count
        ),
        "summary_updated_at": summary_updated_at,
        "summary_version": 1,
    }


def repository_for(
    query: FakeQuery,
) -> tuple[
    StudyConversationRepository,
    FakeClient,
]:
    client = FakeClient(
        query,
    )

    return (
        StudyConversationRepository(
            client,
        ),
        client,
    )


def test_summary_update_normalizes_text() -> None:
    update = StudyConversationSummaryUpdate(
        summary_text="  Earlier discussion summary.  ",
        summarized_message_count=6,
    )

    assert update.summary_text == (
        "Earlier discussion summary."
    )

    assert update.summarized_message_count == 6
    assert update.summary_version == 1


def test_summary_update_rejects_text_over_limit() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyConversationSummaryUpdate(
            summary_text=(
                "x"
                * (
                    MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
                    + 1
                )
            ),
            summarized_message_count=1,
        )


def test_empty_summary_state_requires_zero_count() -> None:
    with pytest.raises(
        ValidationError,
        match="message count of zero",
    ):
        StudyConversationSummaryState(
            conversation_id=uuid4(),
            summary_text=None,
            summarized_message_count=2,
            summary_updated_at=None,
            summary_version=1,
        )


def test_stored_summary_requires_timestamp() -> None:
    with pytest.raises(
        ValidationError,
        match="updated timestamp",
    ):
        StudyConversationSummaryState(
            conversation_id=uuid4(),
            summary_text="Earlier discussion.",
            summarized_message_count=2,
            summary_updated_at=None,
            summary_version=1,
        )


def test_repository_loads_owned_unsummarized_state() -> None:
    user_id = uuid4()
    conversation_id = uuid4()

    query = FakeQuery(
        data=[
            summary_row(
                conversation_id=conversation_id,
            ),
        ],
    )

    repository, client = repository_for(
        query,
    )

    state = repository.get_summary_state(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    assert state is not None
    assert state.conversation_id == conversation_id
    assert state.summary_text is None
    assert state.summarized_message_count == 0

    assert client.table_names == [
        "study_conversations",
    ]

    assert (
        "eq",
        "id",
        str(
            conversation_id,
        ),
    ) in query.operations

    assert (
        "eq",
        "user_id",
        str(
            user_id,
        ),
    ) in query.operations


def test_repository_saves_owned_summary_state() -> None:
    user_id = uuid4()
    conversation_id = uuid4()

    saved_at = datetime.now(
        UTC,
    ).isoformat()

    query = FakeQuery(
        data=[
            summary_row(
                conversation_id=conversation_id,
                summary_text=(
                    "Earlier discussion summary."
                ),
                summarized_message_count=8,
                summary_updated_at=saved_at,
            ),
        ],
    )

    repository, _ = repository_for(
        query,
    )

    state = repository.save_summary_state(
        user_id=user_id,
        conversation_id=conversation_id,
        update=StudyConversationSummaryUpdate(
            summary_text=(
                "Earlier discussion summary."
            ),
            summarized_message_count=8,
        ),
    )

    assert state is not None
    assert state.summary_text == (
        "Earlier discussion summary."
    )

    assert state.summarized_message_count == 8

    update_operations = [
        operation
        for operation in query.operations
        if operation[0] == "update"
    ]

    assert len(
        update_operations,
    ) == 1

    payload = update_operations[0][1]

    assert isinstance(
        payload,
        dict,
    )

    assert payload["summary_text"] == (
        "Earlier discussion summary."
    )

    assert payload[
        "summarized_message_count"
    ] == 8

    assert payload["summary_version"] == 1
    assert isinstance(
        payload["summary_updated_at"],
        str,
    )


def test_repository_returns_none_for_unowned_summary() -> None:
    query = FakeQuery(
        data=[],
    )

    repository, _ = repository_for(
        query,
    )

    state = repository.get_summary_state(
        user_id=uuid4(),
        conversation_id=uuid4(),
    )

    assert state is None


def test_repository_rejects_invalid_update_object() -> None:
    repository, _ = repository_for(
        FakeQuery(
            data=[],
        ),
    )

    with pytest.raises(
        StudyConversationValidationError,
    ):
        repository.save_summary_state(
            user_id=uuid4(),
            conversation_id=uuid4(),
            update=object(),  # type: ignore[arg-type]
        )


def test_repository_rejects_malformed_summary_row() -> None:
    repository, _ = repository_for(
        FakeQuery(
            data=[
                {
                    "id": "invalid-id",
                    "summary_text": "Summary.",
                    "summarized_message_count": 2,
                    "summary_updated_at": (
                        datetime.now(
                            UTC,
                        ).isoformat()
                    ),
                    "summary_version": 1,
                },
            ],
        ),
    )

    with pytest.raises(
        StudyConversationResponseError,
    ):
        repository.get_summary_state(
            user_id=uuid4(),
            conversation_id=uuid4(),
        )