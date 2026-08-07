# File: /backend/tests/test_study_conversation_repository.py
# Purpose: Tests Study Conversation persistence behavior using
# controlled Supabase query doubles.

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

import pytest

from app.repositories.study_conversation_repository import (
    StudyConversationRepository,
)
from app.services.study_conversation_errors import (
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
)


@dataclass
class _FakeResponse:
    data: object


class _FakeQuery:
    def __init__(
        self,
        *,
        data: object = None,
        error: Exception | None = None,
    ) -> None:
        self.response = _FakeResponse(
            data=data,
        )
        self.error = error
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

    def insert(
        self,
        payload: object,
    ) -> Self:
        self.operations.append(
            (
                "insert",
                payload,
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

    def delete(
        self,
    ) -> Self:
        self.operations.append(
            (
                "delete",
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

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> Self:
        self.operations.append(
            (
                "order",
                column,
                desc,
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

    def range(
        self,
        start: int,
        end: int,
    ) -> Self:
        self.operations.append(
            (
                "range",
                start,
                end,
            ),
        )
        return self

    def execute(
        self,
    ) -> _FakeResponse:
        self.operations.append(
            (
                "execute",
            ),
        )

        if self.error is not None:
            raise self.error

        return self.response


class _FakeClient:
    def __init__(
        self,
        query: _FakeQuery,
    ) -> None:
        self.query = query
        self.table_names: list[
            str
        ] = []

    def table(
        self,
        table_name: str,
    ) -> _FakeQuery:
        self.table_names.append(
            table_name,
        )
        return self.query


def _conversation_row(
    *,
    conversation_id: UUID | None = None,
) -> dict[
    str,
    object,
]:
    now = datetime.now(
        UTC,
    ).isoformat()

    return {
        "id": str(
            conversation_id
            or uuid4(),
        ),
        "user_id": str(
            uuid4(),
        ),
        "title": "Biology review",
        "subject_id": str(
            uuid4(),
        ),
        "study_file_id": str(
            uuid4(),
        ),
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
    }


def _message_row() -> dict[
    str,
    object,
]:
    return {
        "id": str(
            uuid4(),
        ),
        "conversation_id": str(
            uuid4(),
        ),
        "role": "assistant",
        "content": (
            "The material explains "
            "photosynthesis. [Source 1]"
        ),
        "outcome": "answered",
        "sources": [
            {
                "source_number": 1,
                "source_name": (
                    "Biology Notes.pdf"
                ),
                "chunk_index": 2,
                "similarity_score": 0.91,
            },
        ],
        "created_at": datetime.now(
            UTC,
        ).isoformat(),
    }


def _repository(
    query: _FakeQuery,
) -> tuple[
    StudyConversationRepository,
    _FakeClient,
]:
    client = _FakeClient(
        query,
    )

    repository = (
        StudyConversationRepository(
            client,
        )
    )

    return (
        repository,
        client,
    )


def test_create_conversation_sends_owner_and_filters() -> None:
    user_id = uuid4()
    subject_id = uuid4()
    study_file_id = uuid4()

    query = _FakeQuery(
        data=[
            _conversation_row(),
        ],
    )

    repository, client = _repository(
        query,
    )

    result = repository.create_conversation(
        user_id=user_id,
        title="Biology review",
        subject_id=subject_id,
        study_file_id=study_file_id,
    )

    assert result.title == "Biology review"

    assert client.table_names == [
        "study_conversations",
    ]

    assert (
        "insert",
        {
            "user_id": str(
                user_id,
            ),
            "title": "Biology review",
            "subject_id": str(
                subject_id,
            ),
            "study_file_id": str(
                study_file_id,
            ),
        },
    ) in query.operations


def test_list_conversations_filters_owner_and_orders_recently() -> None:
    user_id = uuid4()

    query = _FakeQuery(
        data=[
            _conversation_row(),
        ],
    )

    repository, _ = _repository(
        query,
    )

    conversations = (
        repository.list_conversations(
            user_id=user_id,
            limit=20,
        )
    )

    assert len(
        conversations,
    ) == 1

    assert (
        "eq",
        "user_id",
        str(
            user_id,
        ),
    ) in query.operations

    assert (
        "order",
        "last_message_at",
        True,
    ) in query.operations

    assert (
        "limit",
        20,
    ) in query.operations


@pytest.mark.parametrize(
    "limit",
    (
        0,
        51,
    ),
)
def test_list_conversations_rejects_invalid_limit(
    limit: int,
) -> None:
    repository, _ = _repository(
        _FakeQuery(),
    )

    with pytest.raises(
        StudyConversationValidationError,
    ):
        repository.list_conversations(
            user_id=uuid4(),
            limit=limit,
        )


def test_get_conversation_returns_none_when_missing() -> None:
    repository, _ = _repository(
        _FakeQuery(
            data=[],
        ),
    )

    result = repository.get_conversation(
        user_id=uuid4(),
        conversation_id=uuid4(),
    )

    assert result is None


def test_get_conversation_filters_owner_and_id() -> None:
    user_id = uuid4()
    conversation_id = uuid4()

    query = _FakeQuery(
        data=[
            _conversation_row(
                conversation_id=(
                    conversation_id
                ),
            ),
        ],
    )

    repository, _ = _repository(
        query,
    )

    result = repository.get_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    assert result is not None
    assert result.id == conversation_id

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


def test_list_messages_returns_safe_saved_messages() -> None:
    conversation_id = uuid4()

    message_row = _message_row()

    message_row[
        "conversation_id"
    ] = str(
        conversation_id,
    )

    query = _FakeQuery(
        data=[
            message_row,
        ],
    )

    repository, client = _repository(
        query,
    )

    messages = repository.list_messages(
        conversation_id=conversation_id,
    )

    assert client.table_names == [
        "study_messages",
    ]

    assert len(
        messages,
    ) == 1

    assert messages[0].role == "assistant"
    assert messages[0].outcome == "answered"

    assert (
        "order",
        "created_at",
        False,
    ) in query.operations

    assert (
        "order",
        "id",
        False,
    ) in query.operations


def test_update_conversation_converts_uuid_values() -> None:
    subject_id = uuid4()

    query = _FakeQuery(
        data=[
            _conversation_row(),
        ],
    )

    repository, _ = _repository(
        query,
    )

    result = repository.update_conversation(
        user_id=uuid4(),
        conversation_id=uuid4(),
        updates={
            "subject_id": subject_id,
            "study_file_id": None,
        },
    )

    assert result is not None

    assert (
        "update",
        {
            "subject_id": str(
                subject_id,
            ),
            "study_file_id": None,
        },
    ) in query.operations


def test_update_conversation_rejects_unsupported_fields() -> None:
    repository, _ = _repository(
        _FakeQuery(),
    )

    with pytest.raises(
        StudyConversationValidationError,
    ):
        repository.update_conversation(
            user_id=uuid4(),
            conversation_id=uuid4(),
            updates={
                "user_id": uuid4(),
            },
        )


def test_delete_conversation_reports_deleted_row() -> None:
    query = _FakeQuery(
        data=[
            {
                "id": str(
                    uuid4(),
                ),
            },
        ],
    )

    repository, _ = _repository(
        query,
    )

    deleted = repository.delete_conversation(
        user_id=uuid4(),
        conversation_id=uuid4(),
    )

    assert deleted is True

    assert (
        "delete",
    ) in query.operations


def test_database_failure_becomes_controlled_error() -> None:
    repository, _ = _repository(
        _FakeQuery(
            error=RuntimeError(
                "Private database error.",
            ),
        ),
    )

    with pytest.raises(
        StudyConversationPersistenceError,
        match=(
            "The database could not "
            "list conversations."
        ),
    ):
        repository.list_conversations(
            user_id=uuid4(),
            limit=20,
        )


def test_malformed_database_data_is_rejected() -> None:
    repository, _ = _repository(
        _FakeQuery(
            data=[
                {
                    "id": "not-a-uuid",
                },
            ],
        ),
    )

    with pytest.raises(
        StudyConversationResponseError,
    ):
        repository.list_conversations(
            user_id=uuid4(),
            limit=20,
        )


def test_non_list_response_is_rejected() -> None:
    repository, _ = _repository(
        _FakeQuery(
            data={
                "id": str(
                    uuid4(),
                ),
            },
        ),
    )

    with pytest.raises(
        StudyConversationResponseError,
    ):
        repository.list_conversations(
            user_id=uuid4(),
            limit=20,
        )

def test_save_user_message_inserts_safe_metadata() -> None:
    conversation_id = uuid4()

    message_row = _message_row()

    message_row.update(
        {
            "conversation_id": str(
                conversation_id,
            ),
            "role": "user",
            "content": "What is photosynthesis?",
            "outcome": None,
            "sources": [],
        }
    )

    query = _FakeQuery(
        data=[
            message_row,
        ],
    )

    repository, client = _repository(
        query,
    )

    result = repository.save_user_message(
        conversation_id=conversation_id,
        content="  What is photosynthesis?  ",
    )

    assert client.table_names == [
        "study_messages",
    ]

    assert result.role == "user"
    assert result.content == "What is photosynthesis?"
    assert result.outcome is None
    assert result.sources == []

    assert (
        "insert",
        {
            "conversation_id": str(
                conversation_id,
            ),
            "role": "user",
            "content": "What is photosynthesis?",
            "outcome": None,
            "sources": [],
        },
    ) in query.operations


def test_save_assistant_message_serializes_sources() -> None:
    from app.schemas.study_conversation import (
        StudyMessageSourceResponse,
    )

    conversation_id = uuid4()

    message_row = _message_row()

    message_row[
        "conversation_id"
    ] = str(
        conversation_id,
    )

    query = _FakeQuery(
        data=[
            message_row,
        ],
    )

    repository, client = _repository(
        query,
    )

    source = StudyMessageSourceResponse(
        source_number=1,
        source_name="Biology Notes.pdf",
        chunk_index=2,
        similarity_score=0.91,
    )

    result = repository.save_assistant_message(
        conversation_id=conversation_id,
        content=(
            "  Photosynthesis converts light energy "
            "into chemical energy. [Source 1]  "
        ),
        outcome="answered",
        sources=(
            source,
        ),
    )

    assert client.table_names == [
        "study_messages",
    ]

    assert result.role == "assistant"
    assert result.outcome == "answered"
    assert len(
        result.sources,
    ) == 1

    assert (
        "insert",
        {
            "conversation_id": str(
                conversation_id,
            ),
            "role": "assistant",
            "content": (
                "Photosynthesis converts light energy "
                "into chemical energy. [Source 1]"
            ),
            "outcome": "answered",
            "sources": [
                {
                    "source_number": 1,
                    "source_name": (
                        "Biology Notes.pdf"
                    ),
                    "chunk_index": 2,
                    "similarity_score": 0.91,
                },
            ],
        },
    ) in query.operations


def test_save_no_context_message_uses_empty_sources() -> None:
    conversation_id = uuid4()

    message_row = _message_row()

    message_row.update(
        {
            "conversation_id": str(
                conversation_id,
            ),
            "content": (
                "No relevant study context was found."
            ),
            "outcome": "no_context",
            "sources": [],
        }
    )

    query = _FakeQuery(
        data=[
            message_row,
        ],
    )

    repository, _ = _repository(
        query,
    )

    result = repository.save_assistant_message(
        conversation_id=conversation_id,
        content=(
            "No relevant study context was found."
        ),
        outcome="no_context",
        sources=(),
    )

    assert result.outcome == "no_context"
    assert result.sources == []


def test_answered_message_requires_sources() -> None:
    repository, _ = _repository(
        _FakeQuery(),
    )

    with pytest.raises(
        StudyConversationValidationError,
        match="requires sources",
    ):
        repository.save_assistant_message(
            conversation_id=uuid4(),
            content="An answered response.",
            outcome="answered",
            sources=(),
        )


def test_no_context_message_rejects_sources() -> None:
    from app.schemas.study_conversation import (
        StudyMessageSourceResponse,
    )

    repository, _ = _repository(
        _FakeQuery(),
    )

    source = StudyMessageSourceResponse(
        source_number=1,
        source_name="Notes.pdf",
        chunk_index=0,
        similarity_score=0.8,
    )

    with pytest.raises(
        StudyConversationValidationError,
        match="must not include sources",
    ):
        repository.save_assistant_message(
            conversation_id=uuid4(),
            content="No relevant context.",
            outcome="no_context",
            sources=(
                source,
            ),
        )


@pytest.mark.parametrize(
    "content",
    (
        "",
        "   ",
        "x" * 50001,
    ),
    ids=(
        "empty",
        "whitespace",
        "too-long",
    ),
)
def test_save_message_rejects_invalid_content(
    content: str,
) -> None:
    repository, _ = _repository(
        _FakeQuery(),
    )

    with pytest.raises(
        StudyConversationValidationError,
    ):
        repository.save_user_message(
            conversation_id=uuid4(),
            content=content,
        )


def test_save_message_rejects_empty_database_response() -> None:
    repository, _ = _repository(
        _FakeQuery(
            data=[],
        ),
    )

    with pytest.raises(
        StudyConversationResponseError,
        match="saved message response",
    ):
        repository.save_user_message(
            conversation_id=uuid4(),
            content="Explain the notes.",
        )

def test_list_recent_messages_returns_latest_in_chronological_order() -> None:
    conversation_id = uuid4()

    older_row = _message_row()
    older_row.update(
        {
            "conversation_id": str(
                conversation_id,
            ),
            "role": "user",
            "content": "Older question.",
            "outcome": None,
            "sources": [],
            "created_at": (
                "2026-08-06T10:00:00+00:00"
            ),
        }
    )

    newer_row = _message_row()
    newer_row.update(
        {
            "conversation_id": str(
                conversation_id,
            ),
            "content": "Newer answer. [Source 1]",
            "created_at": (
                "2026-08-06T10:01:00+00:00"
            ),
        }
    )

    query = _FakeQuery(
        data=[
            newer_row,
            older_row,
        ],
    )

    repository, client = _repository(
        query,
    )

    messages = repository.list_recent_messages(
        conversation_id=conversation_id,
        limit=2,
    )

    assert client.table_names == [
        "study_messages",
    ]

    assert [
        message.content
        for message in messages
    ] == [
        "Older question.",
        "Newer answer. [Source 1]",
    ]

    assert (
        "order",
        "created_at",
        True,
    ) in query.operations

    assert (
        "order",
        "id",
        True,
    ) in query.operations

    assert (
        "limit",
        2,
    ) in query.operations


@pytest.mark.parametrize(
    "limit",
    (
        0,
        11,
    ),
)
def test_list_recent_messages_rejects_invalid_limit(
    limit: int,
) -> None:
    repository, _ = _repository(
        _FakeQuery(),
    )

    with pytest.raises(
        StudyConversationValidationError,
        match="Recent message limit",
    ):
        repository.list_recent_messages(
            conversation_id=uuid4(),
            limit=limit,
        )

def test_list_messages_from_offset_uses_chronological_range() -> None:
    conversation_id = uuid4()

    message_row = _message_row()
    message_row[
        "conversation_id"
    ] = str(
        conversation_id,
    )

    query = _FakeQuery(
        data=[
            message_row,
        ],
    )

    repository, client = _repository(
        query,
    )

    messages = repository.list_messages_from_offset(
        conversation_id=conversation_id,
        offset=12,
        limit=25,
    )

    assert client.table_names == [
        "study_messages",
    ]

    assert len(
        messages,
    ) == 1

    assert (
        "order",
        "created_at",
        False,
    ) in query.operations

    assert (
        "order",
        "id",
        False,
    ) in query.operations

    assert (
        "range",
        12,
        36,
    ) in query.operations


@pytest.mark.parametrize(
    (
        "offset",
        "limit",
    ),
    (
        (
            -1,
            25,
        ),
        (
            0,
            0,
        ),
        (
            0,
            502,
        ),
    ),
)
def test_list_messages_from_offset_rejects_invalid_window(
    offset: int,
    limit: int,
) -> None:
    repository, _ = _repository(
        _FakeQuery(),
    )

    with pytest.raises(
        StudyConversationValidationError,
    ):
        repository.list_messages_from_offset(
            conversation_id=uuid4(),
            offset=offset,
            limit=limit,
        )
