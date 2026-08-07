# File: /backend/tests/test_study_conversation_memory.py
# Purpose: Tests deterministic conversion of saved messages into
# bounded grounded-generation conversation memory.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.ai.grounded_answer_contracts import (
    MAX_CONVERSATION_MEMORY_CHARACTERS,
    MAX_CONVERSATION_MEMORY_MESSAGES,
    ConversationMemoryRole,
)
from app.schemas.study_conversation import (
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationValidationError,
)
from app.services.study_conversation_memory import (
    MEMORY_TRUNCATION_MARKER,
    build_conversation_memory,
)


def make_message(
    *,
    role: str,
    content: str,
) -> StudyMessageResponse:
    """Create one valid saved message."""

    conversation_id = uuid4()

    if role == "user":
        return StudyMessageResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content=content,
            created_at=datetime.now(
                UTC,
            ),
        )

    return StudyMessageResponse(
        id=uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content=content,
        outcome="answered",
        sources=[],
        created_at=datetime.now(
            UTC,
        ),
    )


def test_memory_preserves_chronological_order() -> None:
    messages = (
        make_message(
            role="user",
            content="First question.",
        ),
        make_message(
            role="assistant",
            content="First answer.",
        ),
        make_message(
            role="user",
            content="Follow-up question.",
        ),
    )

    memory = build_conversation_memory(
        messages,
    )

    assert [
        message.content
        for message in memory
    ] == [
        "First question.",
        "First answer.",
        "Follow-up question.",
    ]

    assert [
        message.role
        for message in memory
    ] == [
        ConversationMemoryRole.USER,
        ConversationMemoryRole.ASSISTANT,
        ConversationMemoryRole.USER,
    ]


def test_memory_keeps_only_latest_ten_messages() -> None:
    messages = tuple(
        make_message(
            role=(
                "user"
                if index % 2 == 0
                else "assistant"
            ),
            content=f"Message {index}.",
        )
        for index in range(
            MAX_CONVERSATION_MEMORY_MESSAGES
            + 3
        )
    )

    memory = build_conversation_memory(
        messages,
    )

    assert len(
        memory,
    ) == MAX_CONVERSATION_MEMORY_MESSAGES

    assert memory[0].content == "Message 3."
    assert memory[-1].content == "Message 12."


def test_memory_prioritizes_newest_messages_under_budget() -> None:
    older_message = make_message(
        role="user",
        content="O" * 6_000,
    )

    newer_message = make_message(
        role="assistant",
        content="N" * 4_000,
    )

    memory = build_conversation_memory(
        (
            older_message,
            newer_message,
        ),
    )

    assert len(
        memory,
    ) == 2

    assert memory[-1].content == "N" * 4_000

    assert memory[0].content.endswith(
        MEMORY_TRUNCATION_MARKER,
    )

    total_characters = sum(
        len(
            message.content,
        )
        for message in memory
    )

    assert (
        total_characters
        == MAX_CONVERSATION_MEMORY_CHARACTERS
    )


def test_single_large_message_is_safely_truncated() -> None:
    memory = build_conversation_memory(
        (
            make_message(
                role="user",
                content="x" * 20_000,
            ),
        )
    )

    assert len(
        memory,
    ) == 1

    assert len(
        memory[0].content,
    ) == MAX_CONVERSATION_MEMORY_CHARACTERS

    assert memory[0].content.endswith(
        MEMORY_TRUNCATION_MARKER,
    )


def test_empty_message_collection_returns_empty_memory() -> None:
    assert build_conversation_memory(
        (),
    ) == ()


def test_memory_rejects_invalid_collection() -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="must be a sequence",
    ):
        build_conversation_memory(
            "invalid",  # type: ignore[arg-type]
        )


def test_memory_rejects_invalid_items() -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="StudyMessageResponse",
    ):
        build_conversation_memory(
            (
                object(),
            ),  # type: ignore[arg-type]
        )

def test_memory_places_summary_before_recent_messages() -> None:
    messages = (
        make_message(
            role="user",
            content="Recent question.",
        ),
        make_message(
            role="assistant",
            content="Recent answer.",
        ),
    )

    memory = build_conversation_memory(
        messages,
        summary_text=(
            "Earlier conversation summary "
            "(not factual study evidence):\n"
            "User: An older question."
        ),
    )

    assert len(
        memory,
    ) == 3

    assert memory[0].role == (
        ConversationMemoryRole.ASSISTANT
    )

    assert memory[0].content.startswith(
        "Earlier conversation summary"
    )

    assert memory[1].content == "Recent question."
    assert memory[2].content == "Recent answer."


def test_summary_reserves_one_of_ten_memory_slots() -> None:
    messages = tuple(
        make_message(
            role=(
                "user"
                if index % 2 == 0
                else "assistant"
            ),
            content=f"Recent message {index}.",
        )
        for index in range(
            12
        )
    )

    memory = build_conversation_memory(
        messages,
        summary_text=(
            "Earlier conversation summary "
            "(not factual study evidence)."
        ),
    )

    assert len(
        memory,
    ) == MAX_CONVERSATION_MEMORY_MESSAGES

    assert memory[0].content.startswith(
        "Earlier conversation summary"
    )

    assert memory[1].content == "Recent message 3."
    assert memory[-1].content == "Recent message 11."


def test_summary_and_recent_messages_share_character_budget() -> None:
    summary_text = "S" * 4_000

    memory = build_conversation_memory(
        (
            make_message(
                role="user",
                content="R" * 6_000,
            ),
        ),
        summary_text=summary_text,
    )

    assert memory[0].content == summary_text

    total_characters = sum(
        len(
            item.content,
        )
        for item in memory
    )

    assert (
        total_characters
        == MAX_CONVERSATION_MEMORY_CHARACTERS
    )

    assert memory[-1].content.endswith(
        MEMORY_TRUNCATION_MARKER,
    )


@pytest.mark.parametrize(
    "summary_text",
    (
        "",
        "   ",
    ),
)
def test_memory_rejects_blank_summary(
    summary_text: str,
) -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="must not be blank",
    ):
        build_conversation_memory(
            (),
            summary_text=summary_text,
        )
