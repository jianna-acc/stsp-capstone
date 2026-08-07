# File: /backend/tests/test_rag_conversation_contract.py
# Purpose: Tests optional conversation IDs across the protected
# RAG request and orchestration flow.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai.grounded_answer_contracts import (
    GroundedAnswerRequest,
    GroundedAnswerResult,
)
from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.routes.rag import (
    router as rag_router,
)
from app.api.study_conversation_rag_dependency import (
    get_study_conversation_rag_service,
)
from app.schemas.rag import (
    RagAnswerRequest,
)
from app.schemas.study_conversation import (
    StudyConversationResponse,
    StudyMessageResponse,
    StudyMessageSourceResponse,
)
from app.services.rag_orchestration import (
    RagOrchestrationRequest,
    RagOrchestrationResult,
    RagOrchestrationValidationError,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationResult,
)
from app.services.study_conversation_rag import (
    StudyConversationRagResult,
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


class FakeRagService:
    """Record requests and return controlled no-context results."""

    def __init__(
        self,
    ) -> None:
        self.requests: list[
            RagOrchestrationRequest
        ] = []

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> RagOrchestrationResult:
        """Return one safe no-context answer."""

        self.requests.append(
            request,
        )

        retrieval_result = RetrievalOrchestrationResult(
            request=request.to_retrieval_request(),
            chunks=(),
            embedding_provider="gemini",
            embedding_model="fake-embedding-model",
            embedding_dimensions=768,
        )

        grounded_request = GroundedAnswerRequest(
            question=request.question,
            chunks=(),
        )

        grounded_result = GroundedAnswerResult.no_context(
            grounded_request,
        )

        return RagOrchestrationResult(
            request=request,
            retrieval=retrieval_result,
            grounded_answer=grounded_result,
        )



class FakeConversationRagServiceAdapter:
    """Wrap an older fake RAG service with persisted chat data."""

    def __init__(
        self,
        service: object,
    ) -> None:
        self._service = service

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> StudyConversationRagResult:
        """Resolve a test conversation and wrap the RAG result."""

        conversation_id = (
            request.conversation_id
            or CONVERSATION_ID
        )

        resolved_request = RagOrchestrationRequest(
            user_id=request.user_id,
            question=request.question,
            conversation_id=conversation_id,
            study_file_id=request.study_file_id,
            subject_id=request.subject_id,
            match_count=request.match_count,
            similarity_threshold=(
                request.similarity_threshold
            ),
        )

        answer_method = self._service.answer

        rag_result = await answer_method(
            resolved_request,
        )

        now = datetime.now(
            UTC,
        )

        conversation = StudyConversationResponse(
            id=conversation_id,
            title=resolved_request.question[:120],
            subject_id=resolved_request.subject_id,
            study_file_id=resolved_request.study_file_id,
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )

        user_message = StudyMessageResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content=resolved_request.question,
            created_at=now,
        )

        message_sources = [
            StudyMessageSourceResponse(
                source_number=source.source_number,
                source_name=source.source_name,
                chunk_index=source.chunk_index,
                similarity_score=source.similarity_score,
            )
            for source in rag_result.sources
        ]

        assistant_message = StudyMessageResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=rag_result.answer,
            outcome=rag_result.outcome.value,
            sources=message_sources,
            created_at=now,
        )

        return StudyConversationRagResult(
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
            rag_result=rag_result,
        )


def create_test_client(
    service: FakeRagService,
) -> TestClient:
    """Create an isolated authenticated RAG API."""

    app = FastAPI()

    app.include_router(
        rag_router,
        prefix="/api",
    )

    app.dependency_overrides[
        require_authenticated_user
    ] = lambda: AuthenticatedUser(
        user_id=USER_ID,
    )

    app.dependency_overrides[
        get_study_conversation_rag_service
    ] = lambda: FakeConversationRagServiceAdapter(
        service,
    )

    return TestClient(
        app,
    )


def test_public_request_accepts_conversation_id() -> None:
    request = RagAnswerRequest(
        question="Explain this material.",
        conversation_id=CONVERSATION_ID,
    )

    assert request.conversation_id == CONVERSATION_ID


def test_public_request_defaults_conversation_id_to_none() -> None:
    request = RagAnswerRequest(
        question="Explain this material.",
    )

    assert request.conversation_id is None


def test_public_request_rejects_invalid_conversation_id() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerRequest(
            question="Explain this material.",
            conversation_id="not-a-uuid",
        )


def test_orchestration_request_preserves_conversation_id() -> None:
    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain this material.",
        conversation_id=CONVERSATION_ID,
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
    )

    assert request.conversation_id == CONVERSATION_ID

    retrieval_request = request.to_retrieval_request()

    assert retrieval_request.user_id == USER_ID
    assert retrieval_request.study_file_id == FILE_ID
    assert retrieval_request.subject_id == SUBJECT_ID

    assert not hasattr(
        retrieval_request,
        "conversation_id",
    )


def test_orchestration_rejects_non_uuid_conversation_id() -> None:
    with pytest.raises(
        RagOrchestrationValidationError,
        match="conversation_id must be a UUID or None",
    ):
        RagOrchestrationRequest(
            user_id=USER_ID,
            question="Explain this material.",
            conversation_id="not-a-uuid",  # type: ignore[arg-type]
        )


def test_endpoint_forwards_conversation_id() -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain this material.",
                "conversation_id": str(
                    CONVERSATION_ID,
                ),
            },
        )

    assert response.status_code == 200

    assert len(
        service.requests,
    ) == 1

    captured_request = service.requests[0]

    assert captured_request.user_id == USER_ID
    assert (
        captured_request.conversation_id
        == CONVERSATION_ID
    )


def test_openapi_exposes_conversation_id() -> None:
    app = FastAPI()

    app.include_router(
        rag_router,
        prefix="/api",
    )

    request_schema = app.openapi()[
        "components"
    ][
        "schemas"
    ][
        "RagAnswerRequest"
    ]

    properties = request_schema[
        "properties"
    ]

    assert "conversation_id" in properties
    assert "user_id" not in properties
    assert "access_token" not in properties