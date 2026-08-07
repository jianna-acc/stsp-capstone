# File: /backend/tests/test_study_conversation_service.py
# Purpose: Tests ownership-aware Study Conversation service
# orchestration without requiring a live database.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.schemas.study_conversation import (
    StudyConversationCreateRequest,
    StudyConversationResponse,
    StudyConversationUpdateRequest,
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationNotFoundError,
)
from app.services.study_conversation_service import (
    StudyConversationService,
)


def _conversation(
    *,
    conversation_id: UUID | None = None,
    title: str = "Biology review",
    subject_id: UUID | None = None,
    study_file_id: UUID | None = None,
) -> StudyConversationResponse:
    now = datetime.now(
        UTC,
    )

    return StudyConversationResponse(
        id=conversation_id or uuid4(),
        title=title,
        subject_id=subject_id,
        study_file_id=study_file_id,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )


def _user_message(
    conversation_id: UUID,
) -> StudyMessageResponse:
    return StudyMessageResponse(
        id=uuid4(),
        conversation_id=conversation_id,
        role="user",
        content="What are the main ideas?",
        created_at=datetime.now(
            UTC,
        ),
    )


class _FakeRepository:
    def __init__(
        self,
    ) -> None:
        self.created_conversation = _conversation()

        self.conversations: list[
            StudyConversationResponse
        ] = []

        self.conversation: (
            StudyConversationResponse
            | None
        ) = None

        self.messages: list[
            StudyMessageResponse
        ] = []

        self.updated_conversation: (
            StudyConversationResponse
            | None
        ) = None

        self.deleted = False

        self.calls: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str,
        subject_id: UUID | None,
        study_file_id: UUID | None,
    ) -> StudyConversationResponse:
        self.calls.append(
            (
                "create_conversation",
                user_id,
                title,
                subject_id,
                study_file_id,
            ),
        )

        return self.created_conversation

    def list_conversations(
        self,
        *,
        user_id: UUID,
        limit: int,
    ) -> list[
        StudyConversationResponse
    ]:
        self.calls.append(
            (
                "list_conversations",
                user_id,
                limit,
            ),
        )

        return self.conversations

    def get_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationResponse | None:
        self.calls.append(
            (
                "get_conversation",
                user_id,
                conversation_id,
            ),
        )

        return self.conversation

    def list_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = 200,
    ) -> list[
        StudyMessageResponse
    ]:
        self.calls.append(
            (
                "list_messages",
                conversation_id,
                limit,
            ),
        )

        return self.messages

    def update_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        updates: dict[
            str,
            object,
        ],
    ) -> StudyConversationResponse | None:
        self.calls.append(
            (
                "update_conversation",
                user_id,
                conversation_id,
                updates,
            ),
        )

        return self.updated_conversation

    def delete_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        self.calls.append(
            (
                "delete_conversation",
                user_id,
                conversation_id,
            ),
        )

        return self.deleted


def test_create_conversation_forwards_owner_and_filters() -> None:
    repository = _FakeRepository()

    service = StudyConversationService(
        repository,
    )

    user_id = uuid4()
    subject_id = uuid4()
    study_file_id = uuid4()

    request = StudyConversationCreateRequest(
        title="  Biology review  ",
        subject_id=subject_id,
        study_file_id=study_file_id,
    )

    result = service.create_conversation(
        user_id=user_id,
        request=request,
    )

    assert result == repository.created_conversation

    assert repository.calls == [
        (
            "create_conversation",
            user_id,
            "Biology review",
            subject_id,
            study_file_id,
        ),
    ]


def test_list_conversations_wraps_repository_items() -> None:
    repository = _FakeRepository()

    conversation = _conversation()

    repository.conversations = [
        conversation,
    ]

    service = StudyConversationService(
        repository,
    )

    user_id = uuid4()

    response = service.list_conversations(
        user_id=user_id,
        limit=15,
    )

    assert response.items == [
        conversation,
    ]

    assert repository.calls == [
        (
            "list_conversations",
            user_id,
            15,
        ),
    ]


def test_list_conversations_uses_default_limit() -> None:
    repository = _FakeRepository()

    service = StudyConversationService(
        repository,
    )

    user_id = uuid4()

    service.list_conversations(
        user_id=user_id,
    )

    assert repository.calls == [
        (
            "list_conversations",
            user_id,
            20,
        ),
    ]


def test_get_detail_checks_ownership_before_messages() -> None:
    repository = _FakeRepository()

    conversation_id = uuid4()
    user_id = uuid4()

    conversation = _conversation(
        conversation_id=conversation_id,
    )

    message = _user_message(
        conversation_id,
    )

    repository.conversation = conversation
    repository.messages = [
        message,
    ]

    service = StudyConversationService(
        repository,
    )

    response = service.get_conversation_detail(
        user_id=user_id,
        conversation_id=conversation_id,
        message_limit=100,
    )

    assert response.conversation == conversation
    assert response.messages == [
        message,
    ]

    assert repository.calls == [
        (
            "get_conversation",
            user_id,
            conversation_id,
        ),
        (
            "list_messages",
            conversation_id,
            100,
        ),
    ]


def test_get_detail_rejects_missing_conversation() -> None:
    repository = _FakeRepository()

    service = StudyConversationService(
        repository,
    )

    user_id = uuid4()
    conversation_id = uuid4()

    with pytest.raises(
        StudyConversationNotFoundError,
        match=(
            "The requested conversation "
            "was not found."
        ),
    ):
        service.get_conversation_detail(
            user_id=user_id,
            conversation_id=conversation_id,
        )

    assert repository.calls == [
        (
            "get_conversation",
            user_id,
            conversation_id,
        ),
    ]


def test_missing_conversation_does_not_load_messages() -> None:
    repository = _FakeRepository()

    service = StudyConversationService(
        repository,
    )

    with pytest.raises(
        StudyConversationNotFoundError,
    ):
        service.get_conversation_detail(
            user_id=uuid4(),
            conversation_id=uuid4(),
        )

    assert all(
        call[0] != "list_messages"
        for call in repository.calls
    )


def test_update_conversation_forwards_only_set_fields() -> None:
    repository = _FakeRepository()

    conversation_id = uuid4()
    user_id = uuid4()
    subject_id = uuid4()

    repository.updated_conversation = (
        _conversation(
            conversation_id=conversation_id,
            title="Updated review",
            subject_id=subject_id,
            study_file_id=None,
        )
    )

    service = StudyConversationService(
        repository,
    )

    request = StudyConversationUpdateRequest(
        title="  Updated review  ",
        subject_id=subject_id,
        study_file_id=None,
    )

    result = service.update_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
        request=request,
    )

    assert result == repository.updated_conversation

    assert repository.calls == [
        (
            "update_conversation",
            user_id,
            conversation_id,
            {
                "title": "Updated review",
                "subject_id": subject_id,
                "study_file_id": None,
            },
        ),
    ]


def test_update_preserves_unset_fields() -> None:
    repository = _FakeRepository()

    conversation_id = uuid4()
    user_id = uuid4()

    repository.updated_conversation = (
        _conversation(
            conversation_id=conversation_id,
            title="Renamed conversation",
        )
    )

    service = StudyConversationService(
        repository,
    )

    request = StudyConversationUpdateRequest(
        title="Renamed conversation",
    )

    service.update_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
        request=request,
    )

    assert repository.calls == [
        (
            "update_conversation",
            user_id,
            conversation_id,
            {
                "title": "Renamed conversation",
            },
        ),
    ]


def test_update_rejects_missing_conversation() -> None:
    repository = _FakeRepository()

    service = StudyConversationService(
        repository,
    )

    with pytest.raises(
        StudyConversationNotFoundError,
        match=(
            "The requested conversation "
            "was not found."
        ),
    ):
        service.update_conversation(
            user_id=uuid4(),
            conversation_id=uuid4(),
            request=(
                StudyConversationUpdateRequest(
                    title="Renamed",
                )
            ),
        )


def test_delete_conversation_succeeds() -> None:
    repository = _FakeRepository()
    repository.deleted = True

    service = StudyConversationService(
        repository,
    )

    user_id = uuid4()
    conversation_id = uuid4()

    result = service.delete_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    assert result is None

    assert repository.calls == [
        (
            "delete_conversation",
            user_id,
            conversation_id,
        ),
    ]


def test_delete_rejects_missing_conversation() -> None:
    repository = _FakeRepository()

    service = StudyConversationService(
        repository,
    )

    with pytest.raises(
        StudyConversationNotFoundError,
        match=(
            "The requested conversation "
            "was not found."
        ),
    ):
        service.delete_conversation(
            user_id=uuid4(),
            conversation_id=uuid4(),
        )