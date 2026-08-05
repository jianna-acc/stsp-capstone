# File: /backend/tests/test_retrieval_orchestration_dependency.py

from __future__ import annotations

import asyncio
from uuid import UUID

import pytest

import app.services as service_exports
from app.ai.contracts import EmbeddingTaskType
from app.ai.retrieval_contracts import (
    RETRIEVAL_EMBEDDING_DIMENSIONS,
    RetrievalOutcome,
    RetrievalRequest,
    RetrievalResult,
)
from app.ai.retrieval_persistence import (
    SupabaseRetrievalPersistence,
)
from app.api.retrieval_orchestration_dependency import (
    get_retrieval_orchestration_service,
)
from app.core.config import Settings
from app.services.query_embedding import (
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


def make_embedding() -> tuple[float, ...]:
    """Return one valid test embedding."""

    values = [
        0.0
    ] * RETRIEVAL_EMBEDDING_DIMENSIONS

    values[-1] = 1.0

    return tuple(
        values,
    )


class FakeQueryEmbeddingService:
    """Generate a controlled query embedding."""

    def __init__(self) -> None:
        self.questions: list[str] = []

    async def embed_query(
        self,
        question: str,
    ) -> QueryEmbeddingResult:
        self.questions.append(
            question,
        )

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


def test_services_package_exports_retrieval_contracts() -> None:
    """The shared service package should expose Phase 5C."""

    assert (
        service_exports.RetrievalOrchestrationRequest
        is RetrievalOrchestrationRequest
    )

    assert (
        service_exports.RetrievalOrchestrationResult
        is RetrievalOrchestrationResult
    )

    assert (
        service_exports.RetrievalOrchestrationService
        is RetrievalOrchestrationService
    )


def test_dependency_constructs_orchestration_service() -> None:
    """The dependency should construct the expected service."""

    service = get_retrieval_orchestration_service(
        settings=Settings.model_construct(),
        query_embedding_service=FakeQueryEmbeddingService(),
    )

    assert isinstance(
        service,
        RetrievalOrchestrationService,
    )


def test_dependency_wires_embedding_to_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The constructed service should perform the full workflow."""

    retrieval_requests: list[
        RetrievalRequest
    ] = []

    async def fake_search(
        _persistence: SupabaseRetrievalPersistence,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        retrieval_requests.append(
            request,
        )

        return RetrievalResult(
            request=request,
            chunks=(),
        )

    monkeypatch.setattr(
        SupabaseRetrievalPersistence,
        "search",
        fake_search,
    )

    query_service = FakeQueryEmbeddingService()

    service = get_retrieval_orchestration_service(
        settings=Settings.model_construct(),
        query_embedding_service=query_service,
    )

    result = asyncio.run(
        service.retrieve(
            RetrievalOrchestrationRequest(
                user_id=USER_ID,
                question="  What is photosynthesis?  ",
                match_count=5,
                similarity_threshold=0.70,
            )
        )
    )

    assert query_service.questions == [
        "What is photosynthesis?"
    ]

    assert len(
        retrieval_requests,
    ) == 1

    retrieval_request = retrieval_requests[0]

    assert retrieval_request.user_id == USER_ID
    assert retrieval_request.match_count == 5
    assert retrieval_request.similarity_threshold == 0.70
    assert len(
        retrieval_request.query_embedding,
    ) == RETRIEVAL_EMBEDDING_DIMENSIONS

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.context_available is False
    assert result.retrieved_count == 0

    assert not hasattr(
        result,
        "embedding",
    )