# File: /backend/tests/test_rag_orchestration_dependency.py

from __future__ import annotations

import asyncio
from typing import get_type_hints
from uuid import UUID

from fastapi.params import Depends

from app.ai.grounded_answer_contracts import (
    GroundedAnswerRequest,
    GroundedAnswerResult,
)
from app.api.grounded_answer_generation_dependency import (
    get_grounded_answer_generation_service,
)
from app.api.rag_orchestration_dependency import (
    get_rag_orchestration_service,
)
from app.api.retrieval_orchestration_dependency import (
    get_retrieval_orchestration_service,
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


class FakeRetrievalService:
    """Fake retrieval dependency for combined wiring tests."""

    def __init__(
        self,
    ) -> None:
        self.requests: list[
            RetrievalOrchestrationRequest
        ] = []
        self.closed = False

    async def retrieve(
        self,
        request: RetrievalOrchestrationRequest,
    ) -> RetrievalOrchestrationResult:
        """Return a controlled no-context result."""

        self.requests.append(
            request,
        )

        return RetrievalOrchestrationResult(
            request=request,
            chunks=(),
            embedding_provider="gemini",
            embedding_model="fake-embedding-model",
            embedding_dimensions=768,
        )

    async def aclose(
        self,
    ) -> None:
        """Record explicit closure."""

        self.closed = True


class FakeGroundedAnswerService:
    """Fake generation dependency for combined wiring tests."""

    def __init__(
        self,
    ) -> None:
        self.requests: list[
            GroundedAnswerRequest
        ] = []
        self.closed = False

    async def generate(
        self,
        request: GroundedAnswerRequest,
    ) -> GroundedAnswerResult:
        """Return a controlled no-context answer."""

        self.requests.append(
            request,
        )

        return GroundedAnswerResult.no_context(
            request,
        )

    async def aclose(
        self,
    ) -> None:
        """Record explicit closure."""

        self.closed = True


def test_dependency_constructs_rag_service() -> None:
    retrieval_service = FakeRetrievalService()
    grounded_service = FakeGroundedAnswerService()

    service = get_rag_orchestration_service(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_service,
    )

    assert isinstance(
        service,
        RagOrchestrationService,
    )


def test_dependency_uses_supplied_child_services() -> None:
    retrieval_service = FakeRetrievalService()
    grounded_service = FakeGroundedAnswerService()

    service = get_rag_orchestration_service(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_service,
    )

    result = asyncio.run(
        service.answer(
            RagOrchestrationRequest(
                user_id=USER_ID,
                question="Explain the uploaded material.",
            )
        )
    )

    assert result.outcome.value == "no_context"
    assert result.retrieved_count == 0
    assert result.source_count == 0
    assert result.context_available is False

    assert len(
        retrieval_service.requests,
    ) == 1

    assert len(
        grounded_service.requests,
    ) == 1

    assert (
        retrieval_service.requests[0].user_id
        == USER_ID
    )

    assert grounded_service.requests[0].chunks == ()


def test_dependency_does_not_close_child_services() -> None:
    retrieval_service = FakeRetrievalService()
    grounded_service = FakeGroundedAnswerService()

    get_rag_orchestration_service(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_service,
    )

    assert retrieval_service.closed is False
    assert grounded_service.closed is False


def test_dependency_declares_expected_fastapi_dependencies() -> None:
    type_hints = get_type_hints(
        get_rag_orchestration_service,
        include_extras=True,
    )

    retrieval_annotation = type_hints[
        "retrieval_service"
    ]

    grounded_annotation = type_hints[
        "grounded_answer_service"
    ]

    retrieval_metadata = getattr(
        retrieval_annotation,
        "__metadata__",
        (),
    )

    grounded_metadata = getattr(
        grounded_annotation,
        "__metadata__",
        (),
    )

    assert len(
        retrieval_metadata,
    ) == 1

    assert len(
        grounded_metadata,
    ) == 1

    retrieval_dependency = retrieval_metadata[0]
    grounded_dependency = grounded_metadata[0]

    assert isinstance(
        retrieval_dependency,
        Depends,
    )

    assert isinstance(
        grounded_dependency,
        Depends,
    )

    assert retrieval_dependency.dependency is (
        get_retrieval_orchestration_service
    )

    assert grounded_dependency.dependency is (
        get_grounded_answer_generation_service
    )
