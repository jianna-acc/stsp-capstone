# File: /backend/tests/test_retrieval_orchestration.py

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from app.ai.contracts import EmbeddingTaskType
from app.ai.retrieval_contracts import (
    RETRIEVAL_EMBEDDING_DIMENSIONS,
    RetrievalOutcome,
    RetrievalRequest,
    RetrievalRequestError,
    RetrievalResponseError,
    RetrievalResult,
    RetrievalValidationError,
    RetrievedStudyChunk,
)
from app.services.query_embedding import (
    QueryEmbeddingProviderError,
    QueryEmbeddingResult,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
    RetrievalOrchestrationResult,
    RetrievalOrchestrationService,
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

CHUNK_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_embedding() -> tuple[float, ...]:
    values = [0.0] * RETRIEVAL_EMBEDDING_DIMENSIONS
    values[-1] = 1.0

    return tuple(
        values,
    )


def make_embedding_result(
    *,
    question: str = "What is photosynthesis?",
) -> QueryEmbeddingResult:
    return QueryEmbeddingResult(
        question=question,
        embedding=make_embedding(),
        provider="gemini",
        embedding_model="gemini-embedding-2",
        embedding_dimensions=(
            RETRIEVAL_EMBEDDING_DIMENSIONS
        ),
        task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
    )


def make_chunk() -> RetrievedStudyChunk:
    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                CHUNK_ID,
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": 2,
            "content": (
                "Photosynthesis converts light energy "
                "into chemical energy."
            ),
            "start_offset": 100,
            "end_offset": 165,
            "chunk_metadata": {
                "page_number": 3,
            },
            "embedding_model": "gemini-embedding-2",
            "similarity_score": 0.92,
        }
    )


def make_orchestration_request(
    **overrides: object,
) -> RetrievalOrchestrationRequest:
    values: dict[str, object] = {
        "user_id": USER_ID,
        "question": "What is photosynthesis?",
    }

    values.update(
        overrides,
    )

    return RetrievalOrchestrationRequest(
        **values,
    )


class FakeQueryEmbeddingService:
    """Fake query-embedding service."""

    def __init__(
        self,
        *,
        result: object | None = None,
        error: Exception | None = None,
        supports_close: bool = True,
    ) -> None:
        self.result = result or make_embedding_result()
        self.error = error
        self.supports_close = supports_close
        self.questions: list[str] = []
        self.close_calls = 0

    async def embed_query(
        self,
        question: str,
    ) -> object:
        self.questions.append(
            question,
        )

        if self.error is not None:
            raise self.error

        return self.result

    async def aclose(self) -> None:
        if not self.supports_close:
            return

        self.close_calls += 1


class FakeRetrievalPersistence:
    """Fake retrieval persistence."""

    def __init__(
        self,
        *,
        chunks: tuple[RetrievedStudyChunk, ...] = (),
        chunks_by_threshold: (
            dict[
                float,
                tuple[RetrievedStudyChunk, ...],
            ]
            | None
        ) = None,
        error: Exception | None = None,
        response: object | None = None,
    ) -> None:
        self.chunks = chunks
        self.chunks_by_threshold = chunks_by_threshold
        self.error = error
        self.response = response
        self.requests: list[RetrievalRequest] = []

    async def search(
        self,
        request: RetrievalRequest,
    ) -> object:
        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        if self.response is not None:
            return self.response

        chunks = self.chunks

        if self.chunks_by_threshold is not None:
            chunks = self.chunks_by_threshold.get(
                request.similarity_threshold,
                (),
            )

        return RetrievalResult(
            request=request,
            chunks=chunks,
        )


class QueryEmbeddingServiceWithoutClose:
    """Fake query service without an aclose method."""

    async def embed_query(
        self,
        question: str,
    ) -> QueryEmbeddingResult:
        return make_embedding_result(
            question=question,
        )


def test_request_normalizes_question_and_uses_defaults() -> None:
    request = make_orchestration_request(
        question="  What is photosynthesis?  ",
    )

    assert request.question == "What is photosynthesis?"
    assert request.match_count == 8
    assert request.similarity_threshold == 0.60
    assert request.study_file_id is None
    assert request.subject_id is None


@pytest.mark.parametrize(
    "invalid_question",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_request_rejects_invalid_question(
    invalid_question: object,
) -> None:
    with pytest.raises(
        RetrievalValidationError,
    ):
        make_orchestration_request(
            question=invalid_question,
        )


@pytest.mark.parametrize(
    "invalid_match_count",
    [
        0,
        21,
        True,
        1.5,
    ],
)
def test_request_rejects_invalid_match_count(
    invalid_match_count: object,
) -> None:
    with pytest.raises(
        RetrievalValidationError,
    ):
        make_orchestration_request(
            match_count=invalid_match_count,
        )


@pytest.mark.parametrize(
    "invalid_threshold",
    [
        -0.01,
        1.01,
        float("nan"),
        True,
    ],
)
def test_request_rejects_invalid_threshold(
    invalid_threshold: object,
) -> None:
    with pytest.raises(
        RetrievalValidationError,
    ):
        make_orchestration_request(
            similarity_threshold=invalid_threshold,
        )


def test_retrieve_embeds_question_and_forwards_filters() -> None:
    query_service = FakeQueryEmbeddingService()

    persistence = FakeRetrievalPersistence(
        chunks=(
            make_chunk(),
        )
    )

    service = RetrievalOrchestrationService(
        query_embedding_service=query_service,
        retrieval_persistence=persistence,
    )

    request = make_orchestration_request(
        match_count=5,
        similarity_threshold=0.70,
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
    )

    result = asyncio.run(
        service.retrieve(
            request,
        )
    )

    assert query_service.questions == [
        "What is photosynthesis?"
    ]

    assert len(
        persistence.requests,
    ) == 1

    retrieval_request = persistence.requests[0]

    assert retrieval_request.user_id == USER_ID
    assert retrieval_request.match_count == 5
    assert retrieval_request.similarity_threshold == 0.70
    assert retrieval_request.study_file_id == FILE_ID
    assert retrieval_request.subject_id == SUBJECT_ID
    assert len(
        retrieval_request.query_embedding,
    ) == 768

    assert isinstance(
        result,
        RetrievalOrchestrationResult,
    )
    assert result.outcome == RetrievalOutcome.MATCHES
    assert result.context_available is True
    assert result.retrieved_count == 1
    assert result.embedding_provider == "gemini"
    assert result.embedding_model == "gemini-embedding-2"
    assert result.embedding_dimensions == 768

    assert not hasattr(
        result,
        "embedding",
    )
    assert not hasattr(
        result,
        "query_embedding",
    )


def test_retrieve_returns_normal_no_context_result() -> None:
    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence()
        ),
    )

    result = asyncio.run(
        service.retrieve(
            make_orchestration_request(),
        )
    )

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.context_available is False
    assert result.retrieved_count == 0
    assert result.no_context_message is not None

def test_file_retrieval_does_not_fallback_when_default_matches() -> None:
    persistence = FakeRetrievalPersistence(
        chunks=(
            make_chunk(),
        ),
    )

    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=persistence,
    )

    result = asyncio.run(
        service.retrieve(
            make_orchestration_request(
                study_file_id=FILE_ID,
            ),
        )
    )

    assert result.outcome == RetrievalOutcome.MATCHES
    assert result.retrieved_count == 1

    assert len(
        persistence.requests,
    ) == 1

    assert (
        persistence.requests[
            0
        ].similarity_threshold
        == 0.60
    )

def test_file_retrieval_falls_back_when_default_has_no_match() -> None:
    persistence = FakeRetrievalPersistence(
        chunks_by_threshold={
            0.60: (),
            0.50: (
                make_chunk(),
            ),
        },
    )

    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=persistence,
    )

    result = asyncio.run(
        service.retrieve(
            make_orchestration_request(
                study_file_id=FILE_ID,
            ),
        )
    )

    assert result.outcome == RetrievalOutcome.MATCHES
    assert result.context_available is True
    assert result.retrieved_count == 1

    assert len(
        persistence.requests,
    ) == 2

    assert [
        retrieval_request.similarity_threshold
        for retrieval_request in persistence.requests
    ] == [
        0.60,
        0.50,
    ]

    assert all(
        retrieval_request.study_file_id == FILE_ID
        for retrieval_request in persistence.requests
    )

def test_subject_retrieval_does_not_use_file_fallback() -> None:
    persistence = FakeRetrievalPersistence(
        chunks_by_threshold={
            0.60: (),
            0.50: (
                make_chunk(),
            ),
        },
    )

    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=persistence,
    )

    result = asyncio.run(
        service.retrieve(
            make_orchestration_request(
                subject_id=SUBJECT_ID,
            ),
        )
    )

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.retrieved_count == 0

    assert len(
        persistence.requests,
    ) == 1

    assert (
        persistence.requests[
            0
        ].similarity_threshold
        == 0.60
    )

def test_file_retrieval_respects_custom_threshold() -> None:
    persistence = FakeRetrievalPersistence(
        chunks_by_threshold={
            0.70: (),
            0.50: (
                make_chunk(),
            ),
        },
    )

    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=persistence,
    )

    result = asyncio.run(
        service.retrieve(
            make_orchestration_request(
                study_file_id=FILE_ID,
                similarity_threshold=0.70,
            ),
        )
    )

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.retrieved_count == 0

    assert len(
        persistence.requests,
    ) == 1

    assert (
        persistence.requests[
            0
        ].similarity_threshold
        == 0.70
    )


def test_retrieve_rejects_invalid_request_type() -> None:
    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence()
        ),
    )

    with pytest.raises(
        RetrievalValidationError,
    ):
        asyncio.run(
            service.retrieve(
                object(),
            )
        )


def test_retrieve_propagates_embedding_failure() -> None:
    query_service = FakeQueryEmbeddingService(
        error=QueryEmbeddingProviderError(
            "Controlled embedding failure."
        )
    )

    persistence = FakeRetrievalPersistence()

    service = RetrievalOrchestrationService(
        query_embedding_service=query_service,
        retrieval_persistence=persistence,
    )

    with pytest.raises(
        QueryEmbeddingProviderError,
    ):
        asyncio.run(
            service.retrieve(
                make_orchestration_request(),
            )
        )

    assert persistence.requests == []


def test_retrieve_propagates_retrieval_failure() -> None:
    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence(
                error=RetrievalRequestError(
                    "Controlled retrieval failure."
                )
            )
        ),
    )

    with pytest.raises(
        RetrievalRequestError,
    ):
        asyncio.run(
            service.retrieve(
                make_orchestration_request(),
            )
        )


def test_retrieve_rejects_invalid_embedding_result() -> None:
    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService(
                result={
                    "unexpected": "result",
                }
            )
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence()
        ),
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            service.retrieve(
                make_orchestration_request(),
            )
        )


def test_retrieve_rejects_invalid_persistence_result() -> None:
    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence(
                response={
                    "unexpected": "result",
                }
            )
        ),
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            service.retrieve(
                make_orchestration_request(),
            )
        )


def test_retrieve_rejects_mismatched_persistence_request() -> None:
    mismatched_request = RetrievalRequest(
        user_id=uuid4(),
        query_embedding=make_embedding(),
    )

    mismatched_result = RetrievalResult(
        request=mismatched_request,
        chunks=(),
    )

    service = RetrievalOrchestrationService(
        query_embedding_service=(
            FakeQueryEmbeddingService()
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence(
                response=mismatched_result,
            )
        ),
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            service.retrieve(
                make_orchestration_request(),
            )
        )


def test_aclose_closes_query_embedding_service() -> None:
    query_service = FakeQueryEmbeddingService()

    service = RetrievalOrchestrationService(
        query_embedding_service=query_service,
        retrieval_persistence=(
            FakeRetrievalPersistence()
        ),
    )

    asyncio.run(
        service.aclose()
    )

    assert query_service.close_calls == 1


def test_aclose_supports_service_without_close() -> None:
    service = RetrievalOrchestrationService(
        query_embedding_service=(
            QueryEmbeddingServiceWithoutClose()
        ),
        retrieval_persistence=(
            FakeRetrievalPersistence()
        ),
    )

    asyncio.run(
        service.aclose()
    )