# File: /backend/tests/test_rag_conversation_memory_flow.py
# Purpose: Verifies that saved conversation memory passes through
# RAG orchestration into the structured generation prompt.

from __future__ import annotations

import asyncio
import json
from uuid import UUID, uuid4

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.grounded_answer_contracts import (
    ConversationMemoryMessage,
    ConversationMemoryRole,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.services.grounded_answer_generation import (
    GroundedAnswerGenerationService,
)
from app.services.rag_orchestration import (
    RagOrchestrationRequest,
    RagOrchestrationService,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
    RetrievalOrchestrationResult,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

CONVERSATION_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

FILE_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

SUBJECT_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_chunk() -> RetrievedStudyChunk:
    """Create one controlled retrieved source."""

    content = (
        "Photosynthesis stores light energy "
        "as chemical energy."
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


class FakeRetrievalService:
    """Return one controlled source chunk."""

    def __init__(
        self,
    ) -> None:
        self.requests: list[
            RetrievalOrchestrationRequest
        ] = []

    async def retrieve(
        self,
        request: RetrievalOrchestrationRequest,
    ) -> RetrievalOrchestrationResult:
        self.requests.append(
            request,
        )

        return RetrievalOrchestrationResult(
            request=request,
            chunks=(
                make_chunk(),
            ),
            embedding_provider="fake",
            embedding_model="fake-embedding-model",
            embedding_dimensions=768,
        )

    async def aclose(
        self,
    ) -> None:
        return None


class FakeGenerationProvider:
    """Capture the final prompt sent by grounded generation."""

    def __init__(
        self,
    ) -> None:
        self.requests: list[
            GenerationRequest
        ] = []

    @property
    def provider_name(
        self,
    ) -> str:
        return "fake"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        self.requests.append(
            request,
        )

        return GenerationResult(
            text=(
                "It is important because chemical energy "
                "supports biological processes. [Source 1]"
            ),
            provider="fake",
            model="fake-model",
        )

    async def aclose(
        self,
    ) -> None:
        return None


def extract_request_json(
    prompt: str,
) -> dict[
    str,
    object,
]:
    """Extract the structured request sent to generation."""

    serialized_payload = prompt.split(
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


def test_saved_memory_reaches_structured_generation_prompt() -> None:
    retrieval_service = FakeRetrievalService()
    generation_provider = FakeGenerationProvider()

    generation_service = GroundedAnswerGenerationService(
        provider=generation_provider,
    )

    service = RagOrchestrationService(
        retrieval_service=retrieval_service,
        grounded_answer_service=generation_service,
    )

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

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Why is that important?",
        memory=memory,
        conversation_id=CONVERSATION_ID,
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
    )

    result = asyncio.run(
        service.answer(
            request,
        )
    )

    assert result.request.memory == memory
    assert result.grounded_answer.request.memory == memory

    assert len(
        generation_provider.requests,
    ) == 1

    generation_request = (
        generation_provider.requests[0]
    )

    payload = extract_request_json(
        generation_request.prompt,
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

    assert payload[
        "student_question"
    ] == "Why is that important?"

    assert len(
        retrieval_service.requests,
    ) == 1

    retrieval_request = retrieval_service.requests[0]

    assert retrieval_request.question == (
        "Why is that important?"
    )

    assert not hasattr(
        retrieval_request,
        "memory",
    )