# File: /backend/app/services/study_conversation_service.py
# Purpose: Coordinates ownership-aware CRUD operations for saved
# Study Assistant conversations and messages.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.study_conversation import (
    StudyConversationCreateRequest,
    StudyConversationDetailResponse,
    StudyConversationListResponse,
    StudyConversationResponse,
    StudyConversationUpdateRequest,
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationNotFoundError,
)


class _StudyConversationRepository(
    Protocol,
):
    def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str,
        subject_id: UUID | None,
        study_file_id: UUID | None,
    ) -> StudyConversationResponse: ...

    def list_conversations(
        self,
        *,
        user_id: UUID,
        limit: int,
    ) -> list[
        StudyConversationResponse
    ]: ...

    def get_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationResponse | None: ...

    def list_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = 200,
    ) -> list[
        StudyMessageResponse
    ]: ...

    def update_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        updates: dict[
            str,
            object,
        ],
    ) -> StudyConversationResponse | None: ...

    def delete_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> bool: ...


class StudyConversationService:
    """Coordinates safe conversation operations for one user."""

    def __init__(
        self,
        repository: _StudyConversationRepository,
    ) -> None:
        self._repository = repository

    def create_conversation(
        self,
        *,
        user_id: UUID,
        request: StudyConversationCreateRequest,
    ) -> StudyConversationResponse:
        """Create one owned conversation."""

        return self._repository.create_conversation(
            user_id=user_id,
            title=request.title,
            subject_id=request.subject_id,
            study_file_id=request.study_file_id,
        )

    def list_conversations(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
    ) -> StudyConversationListResponse:
        """List the user's most recently active conversations."""

        conversations = (
            self._repository.list_conversations(
                user_id=user_id,
                limit=limit,
            )
        )

        return StudyConversationListResponse(
            items=conversations,
        )

    def get_conversation_detail(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        message_limit: int = 200,
    ) -> StudyConversationDetailResponse:
        """Load one owned conversation and its messages."""

        conversation = (
            self._repository.get_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
            )
        )

        if conversation is None:
            raise StudyConversationNotFoundError(
                "The requested conversation was not found.",
            )

        messages = self._repository.list_messages(
            conversation_id=conversation_id,
            limit=message_limit,
        )

        return StudyConversationDetailResponse(
            conversation=conversation,
            messages=messages,
        )

    def update_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        request: StudyConversationUpdateRequest,
    ) -> StudyConversationResponse:
        """Update one owned conversation."""

        updates = request.model_dump(
            exclude_unset=True,
        )

        conversation = (
            self._repository.update_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                updates=updates,
            )
        )

        if conversation is None:
            raise StudyConversationNotFoundError(
                "The requested conversation was not found.",
            )

        return conversation

    def delete_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> None:
        """Delete one owned conversation."""

        deleted = (
            self._repository.delete_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
            )
        )

        if not deleted:
            raise StudyConversationNotFoundError(
                "The requested conversation was not found.",
            )