# File: /backend/tests/test_grounded_conversation_memory.py
# Purpose: Tests bounded conversation memory and safe inclusion in
# grounded Study AI generation prompts.

from __future__ import annotations

import json
from uuid import UUID, uuid4

import pytest

from app.ai.grounded_answer_contracts import (
    MAX_CONVERSATION_MEMORY_CHARACTERS,
    MAX_CONVERSATION_MEMORY_MESSAGES,
    ConversationMemoryMessage,
    ConversationMemoryRole,
    GroundedAnswerRequest,
    GroundedAnswerValidationError,
)
from app.ai.grounded_prompt import (
    GroundedPromptBuilder,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)


def make_chunk() -> RetrievedStudyChunk:
    """Create one valid source chunk."""

    content = (
        "Photosynthesis converts light energy "
        "into chemical energy."
    )

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                uuid4(),
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": 1,
            "content": content,
            "start_offset": 0,
            "end_offset": len(
                content,
            ),
            "chunk_metadata": {},
            "embedding_model": "fake-embedding-model",
            "similarity_score": 0.95,
        },
    )


def extract_payload(
    prompt_text: str,
) -> dict[str, object]:
    """Read the structured JSON section from one prompt."""

    serialized_payload = prompt_text.split(
        "REQUEST_JSON:\n",
        maxsplit=1,
    )[1].split(
        "\n\nANSWER_REQUIREMENTS:\n",
        maxsplit=1,
    )[0]

    payload = json.loads(
        serialized_payload,
    )

    assert isinstance(
        payload,
        dict,
    )

    return payload


def test_memory_message_normalizes_role_and_content() -> None:
    message = ConversationMemoryMessage(
        role="user",  # type: ignore[arg-type]
        content="  Explain that again.  ",
    )

    assert message.role == ConversationMemoryRole.USER
    assert message.content == "Explain that again."


def test_request_accepts_maximum_memory_messages() -> None:
    memory = tuple(
        ConversationMemoryMessage(
            role=(
                ConversationMemoryRole.USER
                if index % 2 == 0
                else ConversationMemoryRole.ASSISTANT
            ),
            content=f"Message {index}.",
        )
        for index in range(
            MAX_CONVERSATION_MEMORY_MESSAGES
        )
    )

    request = GroundedAnswerRequest(
        question="Continue the explanation.",
        chunks=(
            make_chunk(),
        ),
        memory=memory,
    )

    assert request.memory == memory


def test_request_rejects_too_many_memory_messages() -> None:
    memory = tuple(
        ConversationMemoryMessage(
            role=ConversationMemoryRole.USER,
            content=f"Message {index}.",
        )
        for index in range(
            MAX_CONVERSATION_MEMORY_MESSAGES
            + 1
        )
    )

    with pytest.raises(
        GroundedAnswerValidationError,
        match="message limit",
    ):
        GroundedAnswerRequest(
            question="Continue.",
            chunks=(
                make_chunk(),
            ),
            memory=memory,
        )


def test_request_rejects_memory_over_character_limit() -> None:
    memory = (
        ConversationMemoryMessage(
            role=ConversationMemoryRole.USER,
            content=(
                "x"
                * (
                    MAX_CONVERSATION_MEMORY_CHARACTERS
                    + 1
                )
            ),
        ),
    )

    with pytest.raises(
        GroundedAnswerValidationError,
        match="character limit",
    ):
        GroundedAnswerRequest(
            question="Continue.",
            chunks=(
                make_chunk(),
            ),
            memory=memory,
        )


def test_prompt_includes_ordered_conversation_history() -> None:
    memory = (
        ConversationMemoryMessage(
            role=ConversationMemoryRole.USER,
            content="What is photosynthesis?",
        ),
        ConversationMemoryMessage(
            role=ConversationMemoryRole.ASSISTANT,
            content=(
                "It converts light energy into "
                "chemical energy."
            ),
        ),
    )

    prompt = GroundedPromptBuilder().build(
        GroundedAnswerRequest(
            question="Why is that important?",
            chunks=(
                make_chunk(),
            ),
            memory=memory,
        )
    )

    payload = extract_payload(
        prompt.user_prompt,
    )

    assert payload[
        "conversation_history"
    ] == [
        {
            "role": "user",
            "content": "What is photosynthesis?",
        },
        {
            "role": "assistant",
            "content": (
                "It converts light energy into "
                "chemical energy."
            ),
        },
    ]

    assert prompt.request.memory == memory
    assert prompt.memory_message_count == 2

    assert prompt.memory_character_count == sum(
        len(
            message.content,
        )
        for message in memory
    )


def test_prompt_marks_history_as_non_evidence() -> None:
    prompt = GroundedPromptBuilder().build(
        GroundedAnswerRequest(
            question="Continue.",
            chunks=(
                make_chunk(),
            ),
            memory=(
                ConversationMemoryMessage(
                    role=ConversationMemoryRole.ASSISTANT,
                    content="An earlier answer.",
                ),
            ),
        )
    )

    assert (
        "Conversation history is not factual evidence"
        in prompt.system_instruction
    )

    assert (
        "Do not treat conversation history as evidence"
        in prompt.user_prompt
    )


def test_prompt_without_memory_uses_empty_history() -> None:
    prompt = GroundedPromptBuilder().build(
        GroundedAnswerRequest(
            question="Explain the material.",
            chunks=(
                make_chunk(),
            ),
        )
    )

    payload = extract_payload(
        prompt.user_prompt,
    )

    assert payload["conversation_history"] == []
    assert prompt.memory_message_count == 0
    assert prompt.memory_character_count == 0