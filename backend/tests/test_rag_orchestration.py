# File: /backend/tests/test_rag_orchestration.py

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from app.ai.grounded_answer_contracts import (
    GroundedAnswerGenerationError,
    GroundedAnswerRequest,
    GroundedAnswerResult,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.services.rag_orchestration import (
    DEFAULT_RAG_MATCH_COUNT,
    DEFAULT_RAG_SIMILARITY_THRESHOLD,
    RagOrchestrationFailureCode,
    RagOrchestrationGenerationError,
    RagOrchestrationRequest,
    RagOrchestrationResponseError,
    RagOrchestrationResult,
    RagOrchestrationRetrievalError,
    RagOrchestrationService,
    RagOrchestrationValidationError,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
    RetrievalOrchestrationResult,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)


def make_chunk(
    *,
    chunk_id: UUID | None = None,
    similarity_score: float = 0.95,
    chunk_index: int = 1,
) -> RetrievedStudyChunk:
    """Create one valid retrieved study chunk."""

    content = (
        "Photosynthesis converts light energy "
        "into chemical energy."
    )

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                chunk_id
                if chunk_id is not None
                else uuid4()
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": chunk_index,
            "content": content,
            "start_offset": chunk_index * 100,
            "end_offset": (
                chunk_index * 100
                + len(content)
            ),
            "chunk_metadata": {
                "page_number": chunk_index + 1,
            },
            "embedding_model": "gemini-embedding-2",
            "similarity_score": similarity_score,
        }
    )


def make_retrieval_result(
    *,
    request: RetrievalOrchestrationRequest,
    chunks: tuple[
        RetrievedStudyChunk,
        ...,
    ],
) -> RetrievalOrchestrationResult:
    """Create one valid retrieval-orchestration result."""

    return RetrievalOrchestrationResult(
        request=request,
        chunks=chunks,
        embedding_provider="gemini",
        embedding_model="gemini-embedding-2",
        embedding_dimensions=768,
    )


class FakeRetrievalService:
    """Return a controlled retrieval result."""

    def __init__(
        self,
        *,
        chunks: tuple[
            RetrievedStudyChunk,
            ...,
        ] = (),
        error: Exception | None = None,
        invalid_result: object | None = None,
    ) -> None:
        self.chunks = chunks
        self.error = error
        self.invalid_result = invalid_result
        self.requests: list[
            RetrievalOrchestrationRequest
        ] = []
        self.closed = False

    async def retrieve(
        self,
        request: RetrievalOrchestrationRequest,
    ) -> RetrievalOrchestrationResult:
        """Record the request and return controlled context."""

        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        if self.invalid_result is not None:
            return self.invalid_result

        return make_retrieval_result(
            request=request,
            chunks=self.chunks,
        )

    async def aclose(
        self,
    ) -> None:
        """Record retrieval cleanup."""

        self.closed = True


class FakeGroundedAnswerService:
    """Return a controlled grounded-answer result."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
        invalid_result: object | None = None,
    ) -> None:
        self.error = error
        self.invalid_result = invalid_result
        self.requests: list[
            GroundedAnswerRequest
        ] = []
        self.closed = False

    async def generate(
        self,
        request: GroundedAnswerRequest,
    ) -> GroundedAnswerResult:
        """Generate an answered or no-context result."""

        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        if self.invalid_result is not None:
            return self.invalid_result

        if not request.context_available:
            return GroundedAnswerResult.no_context(
                request,
            )

        return GroundedAnswerResult.generated(
            request=request,
            answer=(
                "Photosynthesis converts light energy "
                "into chemical energy. [Source 1]"
            ),
            provider="gemini",
            model="fake-generation-model",
        )

    async def aclose(
        self,
    ) -> None:
        """Record generation cleanup."""

        self.closed = True


def test_request_normalizes_and_uses_defaults() -> None:
    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="  What is photosynthesis?  ",
    )

    assert request.user_id == USER_ID
    assert request.question == "What is photosynthesis?"
    assert request.study_file_id is None
    assert request.subject_id is None
    assert request.match_count == DEFAULT_RAG_MATCH_COUNT
    assert request.similarity_threshold == (
        DEFAULT_RAG_SIMILARITY_THRESHOLD
    )


def test_request_preserves_filters() -> None:
    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain the material.",
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
        match_count=5,
        similarity_threshold=0.75,
    )

    retrieval_request = request.to_retrieval_request()

    assert retrieval_request.user_id == USER_ID
    assert retrieval_request.study_file_id == FILE_ID
    assert retrieval_request.subject_id == SUBJECT_ID
    assert retrieval_request.match_count == 5
    assert retrieval_request.similarity_threshold == 0.75


@pytest.mark.parametrize(
    "question",
    [
        "",
        "   ",
    ],
)
def test_request_rejects_invalid_question(
    question: str,
) -> None:
    with pytest.raises(
        RagOrchestrationValidationError,
    ) as error:
        RagOrchestrationRequest(
            user_id=USER_ID,
            question=question,
        )

    assert (
        error.value.error_code
        == RagOrchestrationFailureCode.VALIDATION_FAILED
    )


def test_service_returns_answered_result() -> None:
    chunk = make_chunk()

    retrieval_service = FakeRetrievalService(
        chunks=(
            chunk,
        ),
    )

    grounded_service = FakeGroundedAnswerService()

    service = RagOrchestrationService(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="What is photosynthesis?",
        study_file_id=FILE_ID,
    )

    result = asyncio.run(
        service.answer(
            request,
        )
    )

    assert result.answer.endswith(
        "[Source 1]"
    )
    assert result.retrieved_count == 1
    assert result.source_count == 1
    assert result.context_available is True
    assert result.sources[0].chunk_id == chunk.chunk_id
    assert result.generation_provider == "gemini"
    assert result.generation_model == (
        "fake-generation-model"
    )
    assert result.embedding_provider == "gemini"
    assert result.embedding_dimensions == 768

    assert len(
        retrieval_service.requests,
    ) == 1

    assert len(
        grounded_service.requests,
    ) == 1

    assert (
        retrieval_service.requests[0].study_file_id
        == FILE_ID
    )

    assert grounded_service.requests[0].chunks == (
        chunk,
    )


def test_service_returns_no_context_result() -> None:
    retrieval_service = FakeRetrievalService(
        chunks=(),
    )

    grounded_service = FakeGroundedAnswerService()

    service = RagOrchestrationService(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_service,
    )

    result = asyncio.run(
        service.answer(
            RagOrchestrationRequest(
                user_id=USER_ID,
                question="What is the topic?",
            )
        )
    )

    assert result.outcome.value == "no_context"
    assert result.retrieved_count == 0
    assert result.source_count == 0
    assert result.context_available is False
    assert result.sources == ()


def test_service_wraps_retrieval_failure() -> None:
    retrieval_service = FakeRetrievalService(
        error=RuntimeError(
            "Controlled retrieval failure."
        ),
    )

    service = RagOrchestrationService(
        retrieval_service=retrieval_service,
        grounded_answer_service=(
            FakeGroundedAnswerService()
        ),
    )

    with pytest.raises(
        RagOrchestrationRetrievalError,
    ) as error:
        asyncio.run(
            service.answer(
                RagOrchestrationRequest(
                    user_id=USER_ID,
                    question="Explain the material.",
                )
            )
        )

    assert (
        error.value.error_code
        == RagOrchestrationFailureCode.RETRIEVAL_FAILED
    )


def test_service_wraps_generation_failure() -> None:
    chunk = make_chunk()

    grounded_service = FakeGroundedAnswerService(
        error=GroundedAnswerGenerationError(
            "Controlled generation failure."
        ),
    )

    service = RagOrchestrationService(
        retrieval_service=FakeRetrievalService(
            chunks=(
                chunk,
            ),
        ),
        grounded_answer_service=grounded_service,
    )

    with pytest.raises(
        RagOrchestrationGenerationError,
    ) as error:
        asyncio.run(
            service.answer(
                RagOrchestrationRequest(
                    user_id=USER_ID,
                    question="Explain the material.",
                )
            )
        )

    assert (
        error.value.error_code
        == RagOrchestrationFailureCode.GENERATION_FAILED
    )


def test_service_rejects_invalid_retrieval_result() -> None:
    service = RagOrchestrationService(
        retrieval_service=FakeRetrievalService(
            invalid_result=object(),
        ),
        grounded_answer_service=(
            FakeGroundedAnswerService()
        ),
    )

    with pytest.raises(
        RagOrchestrationResponseError,
    ):
        asyncio.run(
            service.answer(
                RagOrchestrationRequest(
                    user_id=USER_ID,
                    question="Explain the material.",
                )
            )
        )


def test_service_rejects_invalid_grounded_result() -> None:
    service = RagOrchestrationService(
        retrieval_service=FakeRetrievalService(
            chunks=(
                make_chunk(),
            ),
        ),
        grounded_answer_service=(
            FakeGroundedAnswerService(
                invalid_result=object(),
            )
        ),
    )

    with pytest.raises(
        RagOrchestrationResponseError,
    ):
        asyncio.run(
            service.answer(
                RagOrchestrationRequest(
                    user_id=USER_ID,
                    question="Explain the material.",
                )
            )
        )


def test_result_rejects_unretrieved_answer_context() -> None:
    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain the material.",
    )

    retrieval_request = request.to_retrieval_request()

    retrieved_chunk = make_chunk(
        chunk_id=uuid4(),
        similarity_score=0.95,
        chunk_index=1,
    )

    different_chunk = make_chunk(
        chunk_id=uuid4(),
        similarity_score=0.90,
        chunk_index=2,
    )

    retrieval_result = make_retrieval_result(
        request=retrieval_request,
        chunks=(
            retrieved_chunk,
        ),
    )

    grounded_result = GroundedAnswerResult.generated(
        request=GroundedAnswerRequest(
            question=request.question,
            chunks=(
                different_chunk,
            ),
        ),
        answer="Grounded answer. [Source 1]",
        provider="gemini",
        model="fake-generation-model",
    )

    with pytest.raises(
        RagOrchestrationResponseError,
    ):
        RagOrchestrationResult(
            request=request,
            retrieval=retrieval_result,
            grounded_answer=grounded_result,
        )


def test_service_closes_both_services() -> None:
    retrieval_service = FakeRetrievalService()
    grounded_service = FakeGroundedAnswerService()

    service = RagOrchestrationService(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_service,
    )

    asyncio.run(
        service.aclose()
    )

    assert grounded_service.closed is True
    assert retrieval_service.closed is True


def test_service_rejects_invalid_dependencies() -> None:
    with pytest.raises(
        RagOrchestrationValidationError,
    ):
        RagOrchestrationService(
            retrieval_service=object(),
            grounded_answer_service=(
                FakeGroundedAnswerService()
            ),
        )

    with pytest.raises(
        RagOrchestrationValidationError,
    ):
        RagOrchestrationService(
            retrieval_service=FakeRetrievalService(),
            grounded_answer_service=object(),
        )
