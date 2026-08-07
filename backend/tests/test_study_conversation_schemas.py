# File: /backend/tests/test_study_conversation_schemas.py
# Purpose: Tests safe Study Conversation request and response
# validation without requiring a live database.

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.study_conversation import (
    StudyConversationCreateRequest,
    StudyConversationDetailResponse,
    StudyConversationListResponse,
    StudyConversationResponse,
    StudyConversationUpdateRequest,
    StudyMessageResponse,
    StudyMessageSourceResponse,
)


def _conversation_response() -> StudyConversationResponse:
    now = datetime.now(
        UTC,
    )

    return StudyConversationResponse(
        id=uuid4(),
        title="Biology review",
        subject_id=uuid4(),
        study_file_id=uuid4(),
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )


def test_create_request_uses_default_title() -> None:
    request = StudyConversationCreateRequest()

    assert request.title == "New conversation"
    assert request.subject_id is None
    assert request.study_file_id is None


def test_create_request_normalizes_title() -> None:
    request = StudyConversationCreateRequest(
        title="  Rizal review  ",
    )

    assert request.title == "Rizal review"


@pytest.mark.parametrize(
    "title",
    (
        "",
        "   ",
        "a" * 121,
    ),
)
def test_create_request_rejects_invalid_title(
    title: str,
) -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyConversationCreateRequest(
            title=title,
        )


def test_create_request_rejects_unknown_fields() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyConversationCreateRequest.model_validate(
            {
                "title": "Test",
                "user_id": str(
                    uuid4(),
                ),
            },
        )


def test_update_request_requires_at_least_one_field() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyConversationUpdateRequest()


def test_update_request_allows_filter_clearing() -> None:
    request = StudyConversationUpdateRequest(
        subject_id=None,
        study_file_id=None,
    )

    assert request.model_fields_set == {
        "subject_id",
        "study_file_id",
    }


def test_update_request_rejects_null_title() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyConversationUpdateRequest(
            title=None,
        )


def test_conversation_response_rejects_user_id() -> None:
    now = datetime.now(
        UTC,
    )

    with pytest.raises(
        ValidationError,
    ):
        StudyConversationResponse.model_validate(
            {
                "id": str(
                    uuid4(),
                ),
                "user_id": str(
                    uuid4(),
                ),
                "title": "Unsafe response",
                "subject_id": None,
                "study_file_id": None,
                "created_at": now,
                "updated_at": now,
                "last_message_at": now,
            },
        )


def test_source_response_normalizes_name() -> None:
    source = StudyMessageSourceResponse(
        source_number=1,
        source_name="  Biology Notes.pdf  ",
        chunk_index=2,
        similarity_score=0.91,
    )

    assert source.source_name == "Biology Notes.pdf"


def test_user_message_rejects_outcome() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyMessageResponse(
            id=uuid4(),
            conversation_id=uuid4(),
            role="user",
            content="Summarize this material.",
            outcome="answered",
            created_at=datetime.now(
                UTC,
            ),
        )


def test_user_message_rejects_sources() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyMessageResponse(
            id=uuid4(),
            conversation_id=uuid4(),
            role="user",
            content="Summarize this material.",
            sources=[
                StudyMessageSourceResponse(
                    source_number=1,
                    source_name="Notes.pdf",
                    chunk_index=0,
                    similarity_score=0.8,
                ),
            ],
            created_at=datetime.now(
                UTC,
            ),
        )


def test_assistant_message_requires_outcome() -> None:
    with pytest.raises(
        ValidationError,
    ):
        StudyMessageResponse(
            id=uuid4(),
            conversation_id=uuid4(),
            role="assistant",
            content="This is the answer.",
            created_at=datetime.now(
                UTC,
            ),
        )


def test_assistant_message_accepts_safe_sources() -> None:
    message = StudyMessageResponse(
        id=uuid4(),
        conversation_id=uuid4(),
        role="assistant",
        content="The material explains photosynthesis. [Source 1]",
        outcome="answered",
        sources=[
            StudyMessageSourceResponse(
                source_number=1,
                source_name="Biology Notes.pdf",
                chunk_index=2,
                similarity_score=0.91,
            ),
        ],
        created_at=datetime.now(
            UTC,
        ),
    )

    assert message.outcome == "answered"
    assert len(message.sources) == 1


def test_list_response_accepts_conversations() -> None:
    response = StudyConversationListResponse(
        items=[
            _conversation_response(),
        ],
    )

    assert len(response.items) == 1


def test_detail_response_accepts_messages() -> None:
    conversation = _conversation_response()

    response = StudyConversationDetailResponse(
        conversation=conversation,
        messages=[
            StudyMessageResponse(
                id=uuid4(),
                conversation_id=conversation.id,
                role="user",
                content="What are the key ideas?",
                created_at=datetime.now(
                    UTC,
                ),
            ),
        ],
    )

    assert response.conversation.id == conversation.id
    assert len(response.messages) == 1