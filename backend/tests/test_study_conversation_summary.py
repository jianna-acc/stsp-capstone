# File: /backend/tests/test_study_conversation_summary.py
# Purpose: Tests deterministic bounded summaries of older saved
# Study Assistant conversation messages.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.schemas.study_conversation import (
    MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS,
    StudyConversationSummaryState,
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationValidationError,
)
from app.services.study_conversation_summary import (
    CONVERSATION_SUMMARY_VERSION,
    MESSAGE_TRUNCATION_MARKER,
    SUMMARY_HEADER,
    SUMMARY_TRUNCATION_MARKER,
    build_conversation_summary_update,
)

CONVERSATION_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)


def make_state(
    *,
    summary_text: str | None = None,
    summarized_message_count: int = 0,
    summary_version: int = (
        CONVERSATION_SUMMARY_VERSION
    ),
) -> StudyConversationSummaryState:
    return StudyConversationSummaryState(
        conversation_id=CONVERSATION_ID,
        summary_text=summary_text,
        summarized_message_count=(
            summarized_message_count
        ),
        summary_updated_at=(
            datetime.now(
                UTC,
            )
            if summary_text is not None
            else None
        ),
        summary_version=summary_version,
    )


def make_message(
    *,
    role: str,
    content: str,
    conversation_id: UUID = CONVERSATION_ID,
) -> StudyMessageResponse:
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
        outcome="no_context",
        sources=[],
        created_at=datetime.now(
            UTC,
        ),
    )


def test_summary_builder_labels_roles_and_counts_messages() -> None:
    update = build_conversation_summary_update(
        state=make_state(),
        messages=(
            make_message(
                role="user",
                content="What is photosynthesis?",
            ),
            make_message(
                role="assistant",
                content=(
                    "It converts light energy into "
                    "chemical energy. [Source 1]"
                ),
            ),
        ),
    )

    assert update is not None

    assert update.summary_text.startswith(
        SUMMARY_HEADER,
    )

    assert (
        "User: What is photosynthesis?"
        in update.summary_text
    )

    assert (
        "Assistant: It converts light energy "
        "into chemical energy."
        in update.summary_text
    )

    assert "[Source 1]" not in update.summary_text
    assert update.summarized_message_count == 2


def test_summary_builder_appends_to_existing_summary() -> None:
    state = make_state(
        summary_text=(
            f"{SUMMARY_HEADER}\n"
            "User: Earlier question."
        ),
        summarized_message_count=1,
    )

    update = build_conversation_summary_update(
        state=state,
        messages=(
            make_message(
                role="assistant",
                content="Earlier answer.",
            ),
        ),
    )

    assert update is not None

    assert "User: Earlier question." in (
        update.summary_text
    )

    assert "Assistant: Earlier answer." in (
        update.summary_text
    )

    assert update.summarized_message_count == 2


def test_summary_builder_returns_none_without_messages() -> None:
    update = build_conversation_summary_update(
        state=make_state(),
        messages=(),
    )

    assert update is None


def test_summary_builder_rejects_invalid_collection() -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="must be a sequence",
    ):
        build_conversation_summary_update(
            state=make_state(),
            messages="invalid",  # type: ignore[arg-type]
        )


def test_summary_builder_rejects_invalid_items() -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="StudyMessageResponse",
    ):
        build_conversation_summary_update(
            state=make_state(),
            messages=(
                object(),
            ),  # type: ignore[arg-type]
        )


def test_summary_builder_rejects_wrong_conversation() -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="does not belong",
    ):
        build_conversation_summary_update(
            state=make_state(),
            messages=(
                make_message(
                    role="user",
                    content="Wrong conversation.",
                    conversation_id=uuid4(),
                ),
            ),
        )


def test_summary_builder_rejects_unknown_version() -> None:
    with pytest.raises(
        StudyConversationValidationError,
        match="version",
    ):
        build_conversation_summary_update(
            state=make_state(
                summary_version=2,
            ),
            messages=(
                make_message(
                    role="user",
                    content="A message.",
                ),
            ),
        )


def test_summary_builder_shortens_large_message() -> None:
    update = build_conversation_summary_update(
        state=make_state(),
        messages=(
            make_message(
                role="user",
                content="x" * 2_000,
            ),
        ),
    )

    assert update is not None

    assert MESSAGE_TRUNCATION_MARKER in (
        update.summary_text
    )

    assert (
        len(
            update.summary_text,
        )
        <= MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
    )


def test_summary_builder_prioritizes_newest_rows() -> None:
    messages = tuple(
        make_message(
            role=(
                "user"
                if index % 2 == 0
                else "assistant"
            ),
            content=(
                f"Message-{index}-"
                + str(
                    index,
                )
                * 550
            ),
        )
        for index in range(
            12
        )
    )

    update = build_conversation_summary_update(
        state=make_state(),
        messages=messages,
    )

    assert update is not None

    assert SUMMARY_TRUNCATION_MARKER in (
        update.summary_text
    )

    assert "Message-11-" in update.summary_text
    assert "Message-0-" not in update.summary_text

    assert (
        len(
            update.summary_text,
        )
        <= MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
    )

    assert update.summarized_message_count == 12


def test_summary_builder_is_deterministic() -> None:
    state = make_state()

    messages = (
        make_message(
            role="user",
            content="First message.",
        ),
        make_message(
            role="assistant",
            content="Second message.",
        ),
    )

    first_update = build_conversation_summary_update(
        state=state,
        messages=messages,
    )

    second_update = build_conversation_summary_update(
        state=state,
        messages=messages,
    )

    assert first_update == second_update