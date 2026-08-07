# File: /backend/app/schemas/study_conversation.py
# Purpose: Defines safe request and response contracts for saved
# Study Assistant conversations and messages.

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

StudyMessageRole = Literal[
    "user",
    "assistant",
]

StudyMessageOutcome = Literal[
    "answered",
    "no_context",
]

MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS = 4_000
MAX_STUDY_CONVERSATION_SUMMARY_VERSION = 100


def _normalize_summary_text(
    value: str,
) -> str:
    """Normalize and validate internal conversation-summary text."""

    normalized_summary = value.strip()

    if not normalized_summary:
        raise ValueError(
            "Conversation summary must not be blank.",
        )

    if (
        len(
            normalized_summary,
        )
        > MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
    ):
        raise ValueError(
            "Conversation summary must not exceed "
            f"{MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS} "
            "characters.",
        )

    return normalized_summary


def _normalize_title(
    value: str,
) -> str:
    """Normalize and validate a conversation title."""

    normalized_title = value.strip()

    if not normalized_title:
        raise ValueError(
            "Conversation title must not be blank.",
        )

    if len(normalized_title) > 120:
        raise ValueError(
            "Conversation title must not exceed 120 characters.",
        )

    return normalized_title


class StudyConversationCreateRequest(
    BaseModel,
):
    """Request for creating one saved conversation."""

    model_config = ConfigDict(
        extra="forbid",
    )

    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=120,
    )

    subject_id: UUID | None = None
    study_file_id: UUID | None = None

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        return _normalize_title(
            value,
        )


class StudyConversationUpdateRequest(
    BaseModel,
):
    """Request for updating conversation metadata or filters."""

    model_config = ConfigDict(
        extra="forbid",
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    subject_id: UUID | None = None
    study_file_id: UUID | None = None

    @field_validator(
        "title",
        mode="before",
    )
    @classmethod
    def normalize_optional_title(
        cls,
        value: object,
    ) -> object:
        if value is None:
            raise ValueError(
                "Conversation title must not be null.",
            )

        if not isinstance(
            value,
            str,
        ):
            return value

        return _normalize_title(
            value,
        )

    @model_validator(
        mode="after",
    )
    def require_update_field(
        self,
    ) -> StudyConversationUpdateRequest:
        if not self.model_fields_set:
            raise ValueError(
                "At least one conversation field must be provided.",
            )

        return self


class StudyConversationResponse(
    BaseModel,
):
    """Safe conversation metadata returned to the frontend."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: UUID
    title: str

    subject_id: UUID | None
    study_file_id: UUID | None

    created_at: datetime
    updated_at: datetime
    last_message_at: datetime

    @field_validator(
        "title",
    )
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        return _normalize_title(
            value,
        )


class StudyMessageSourceResponse(
    BaseModel,
):
    """Safe citation metadata stored with an assistant message."""

    model_config = ConfigDict(
        extra="forbid",
    )

    source_number: int = Field(
        ge=1,
    )

    source_name: str = Field(
        min_length=1,
        max_length=500,
    )

    chunk_index: int = Field(
        ge=0,
    )

    similarity_score: float = Field(
        ge=0,
        le=1,
    )

    @field_validator(
        "source_name",
    )
    @classmethod
    def normalize_source_name(
        cls,
        value: str,
    ) -> str:
        normalized_name = value.strip()

        if not normalized_name:
            raise ValueError(
                "Source name must not be blank.",
            )

        return normalized_name


class StudyMessageResponse(
    BaseModel,
):
    """Safe saved-message response returned to the frontend."""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: UUID
    conversation_id: UUID

    role: StudyMessageRole

    content: str = Field(
        min_length=1,
        max_length=50000,
    )

    outcome: StudyMessageOutcome | None = None

    sources: list[
        StudyMessageSourceResponse
    ] = Field(
        default_factory=list,
    )

    created_at: datetime

    @field_validator(
        "content",
    )
    @classmethod
    def normalize_content(
        cls,
        value: str,
    ) -> str:
        normalized_content = value.strip()

        if not normalized_content:
            raise ValueError(
                "Message content must not be blank.",
            )

        return normalized_content

    @model_validator(
        mode="after",
    )
    def validate_role_metadata(
        self,
    ) -> StudyMessageResponse:
        if self.role == "user":
            if self.outcome is not None:
                raise ValueError(
                    "User messages must not include an outcome.",
                )

            if self.sources:
                raise ValueError(
                    "User messages must not include sources.",
                )

            return self

        if self.outcome is None:
            raise ValueError(
                "Assistant messages require an outcome.",
            )

        return self


class StudyConversationSummaryUpdate(
    BaseModel,
):
    """Validated internal update for one conversation summary."""

    model_config = ConfigDict(
        extra="forbid",
    )

    summary_text: str = Field(
        min_length=1,
        max_length=(
            MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
        ),
    )

    summarized_message_count: int = Field(
        ge=1,
    )

    summary_version: int = Field(
        default=1,
        ge=1,
        le=MAX_STUDY_CONVERSATION_SUMMARY_VERSION,
    )

    @field_validator(
        "summary_text",
    )
    @classmethod
    def normalize_summary_text(
        cls,
        value: str,
    ) -> str:
        return _normalize_summary_text(
            value,
        )


class StudyConversationSummaryState(
    BaseModel,
):
    """Internal persisted summary state for one conversation."""

    model_config = ConfigDict(
        extra="forbid",
    )

    conversation_id: UUID

    summary_text: str | None = Field(
        default=None,
        max_length=(
            MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
        ),
    )

    summarized_message_count: int = Field(
        ge=0,
    )

    summary_updated_at: datetime | None

    summary_version: int = Field(
        ge=1,
        le=MAX_STUDY_CONVERSATION_SUMMARY_VERSION,
    )

    @field_validator(
        "summary_text",
    )
    @classmethod
    def normalize_optional_summary_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return _normalize_summary_text(
            value,
        )

    @model_validator(
        mode="after",
    )
    def validate_summary_state(
        self,
    ) -> StudyConversationSummaryState:
        if self.summary_text is None:
            if self.summarized_message_count != 0:
                raise ValueError(
                    "An empty summary must have a message "
                    "count of zero.",
                )

            if self.summary_updated_at is not None:
                raise ValueError(
                    "An empty summary must not have an "
                    "updated timestamp.",
                )

            return self

        if self.summarized_message_count <= 0:
            raise ValueError(
                "A stored summary requires at least one "
                "summarized message.",
            )

        if self.summary_updated_at is None:
            raise ValueError(
                "A stored summary requires an updated timestamp.",
            )

        return self


class StudyConversationListResponse(
    BaseModel,
):
    """List of the authenticated user's saved conversations."""

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[
        StudyConversationResponse
    ] = Field(
        default_factory=list,
    )


class StudyConversationDetailResponse(
    BaseModel,
):
    """One saved conversation and all loaded messages."""

    model_config = ConfigDict(
        extra="forbid",
    )

    conversation: StudyConversationResponse

    messages: list[
        StudyMessageResponse
    ] = Field(
        default_factory=list,
    )

class StudyConversationApiErrorResponse(
    BaseModel,
):
    """Safe controlled error returned by conversation endpoints."""

    model_config = ConfigDict(
        extra="forbid",
    )

    error_code: str = Field(
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        min_length=1,
        max_length=500,
    )