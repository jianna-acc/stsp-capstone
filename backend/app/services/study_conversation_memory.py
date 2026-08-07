# File: /backend/app/services/study_conversation_memory.py
# Purpose: Converts stored summaries and recent saved messages
# into bounded grounded-generation conversation memory.

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from app.ai.grounded_answer_contracts import (
    MAX_CONVERSATION_MEMORY_CHARACTERS,
    MAX_CONVERSATION_MEMORY_MESSAGES,
    ConversationMemoryMessage,
    ConversationMemoryRole,
)
from app.schemas.study_conversation import (
    MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS,
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationValidationError,
)

MEMORY_TRUNCATION_MARKER: Final = (
    "\n[Message truncated to fit the conversation memory limit.]"
)


def build_conversation_memory(
    messages: Sequence[
        StudyMessageResponse
    ],
    *,
    summary_text: str | None = None,
) -> tuple[
    ConversationMemoryMessage,
    ...,
]:
    """Combine one stored summary with the newest saved messages."""

    if (
        isinstance(
            messages,
            (
                str,
                bytes,
            ),
        )
        or not isinstance(
            messages,
            Sequence,
        )
    ):
        raise StudyConversationValidationError(
            "Conversation messages must be a sequence.",
        )

    normalized_messages = tuple(
        messages,
    )

    if not all(
        isinstance(
            message,
            StudyMessageResponse,
        )
        for message in normalized_messages
    ):
        raise StudyConversationValidationError(
            "Every conversation-memory item must be "
            "a StudyMessageResponse.",
        )

    summary_memory = _build_summary_memory(
        summary_text,
    )

    reserved_message_count = (
        1
        if summary_memory is not None
        else 0
    )

    recent_message_limit = (
        MAX_CONVERSATION_MEMORY_MESSAGES
        - reserved_message_count
    )

    remaining_characters = (
        MAX_CONVERSATION_MEMORY_CHARACTERS
    )

    if summary_memory is not None:
        remaining_characters -= len(
            summary_memory.content,
        )

    recent_messages = normalized_messages[
        -recent_message_limit:
    ]

    newest_first_memory: list[
        ConversationMemoryMessage
    ] = []

    for message in reversed(
        recent_messages,
    ):
        content = message.content.strip()

        if not content:
            continue

        if remaining_characters <= 0:
            break

        content_for_memory = content

        if len(content_for_memory) > remaining_characters:
            available_content_characters = (
                remaining_characters
                - len(
                    MEMORY_TRUNCATION_MARKER,
                )
            )

            if available_content_characters <= 0:
                break

            content_for_memory = (
                content_for_memory[
                    :available_content_characters
                ].rstrip()
                + MEMORY_TRUNCATION_MARKER
            )

        newest_first_memory.append(
            ConversationMemoryMessage(
                role=ConversationMemoryRole(
                    message.role,
                ),
                content=content_for_memory,
            )
        )

        remaining_characters -= len(
            content_for_memory,
        )

        if content_for_memory != content:
            break

    recent_memory = tuple(
        reversed(
            newest_first_memory,
        )
    )

    if summary_memory is None:
        return recent_memory

    return (
        summary_memory,
        *recent_memory,
    )


def _build_summary_memory(
    summary_text: str | None,
) -> ConversationMemoryMessage | None:
    """Validate one internal non-evidence summary memory item."""

    if summary_text is None:
        return None

    if not isinstance(
        summary_text,
        str,
    ):
        raise StudyConversationValidationError(
            "Conversation summary memory must be a string.",
        )

    normalized_summary = summary_text.strip()

    if not normalized_summary:
        raise StudyConversationValidationError(
            "Conversation summary memory must not be blank.",
        )

    if (
        len(
            normalized_summary,
        )
        > MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
    ):
        raise StudyConversationValidationError(
            "Conversation summary memory exceeds the "
            "configured summary limit.",
        )

    return ConversationMemoryMessage(
        role=ConversationMemoryRole.ASSISTANT,
        content=normalized_summary,
    )
