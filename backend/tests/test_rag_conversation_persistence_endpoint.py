# File: /backend/tests/test_rag_conversation_persistence_endpoint.py
# Purpose: Tests persisted conversation behavior of the protected
# RAG endpoint without live database or AI-provider calls.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
from app.schemas.study_conversation import (
    StudyConversationResponse,
    StudyMessageResponse,
)
from app.services.rag_orchestration import (
    RagOrchestrationRequest,
    RagOrchestrationResult,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationResult,
)
from app.services.study_conversation_errors import (
    StudyConversationNotFoundError,
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
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


def make_persisted_result(
    request: RagOrchestrationRequest,
) -> StudyConversationRagResult:
    """Create one persisted no-context RAG result."""

    resolved_request = RagOrchestrationRequest(
        user_id=request.user_id,
        question=request.question,
        conversation_id=(
            request.conversation_id
            or CONVERSATION_ID
        ),
        study_file_id=request.study_file_id,
        subject_id=request.subject_id,
        match_count=request.match_count,
        similarity_threshold=(
            request.similarity_threshold
        ),
    )

    retrieval = RetrievalOrchestrationResult(
        request=resolved_request.to_retrieval_request(),
        chunks=(),
        embedding_provider="gemini",
        embedding_model="fake-embedding-model",
        embedding_dimensions=768,
    )

    grounded_request = GroundedAnswerRequest(
        question=resolved_request.question,
        chunks=(),
    )

    grounded_result = GroundedAnswerResult.no_context(
        grounded_request,
    )

    rag_result = RagOrchestrationResult(
        request=resolved_request,
        retrieval=retrieval,
        grounded_answer=grounded_result,
    )

    now = datetime.now(
        UTC,
    )

    conversation = StudyConversationResponse(
        id=resolved_request.conversation_id,
        title="Explain this material.",
        subject_id=resolved_request.subject_id,
        study_file_id=resolved_request.study_file_id,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    user_message = StudyMessageResponse(
        id=uuid4(),
        conversation_id=conversation.id,
        role="user",
        content=resolved_request.question,
        created_at=now,
    )

    assistant_message = StudyMessageResponse(
        id=uuid4(),
        conversation_id=conversation.id,
        role="assistant",
        content=grounded_result.answer,
        outcome="no_context",
        sources=[],
        created_at=now,
    )

    return StudyConversationRagResult(
        conversation=conversation,
        user_message=user_message,
        assistant_message=assistant_message,
        rag_result=rag_result,
    )


class FakeConversationRagService:
    """Record requests and return controlled persisted results."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error

        self.requests: list[
            RagOrchestrationRequest
        ] = []

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> StudyConversationRagResult:
        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        return make_persisted_result(
            request,
        )


def create_test_client(
    service: FakeConversationRagService,
) -> TestClient:
    """Create an isolated authenticated persisted RAG API."""

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
    ] = lambda: service

    return TestClient(
        app,
    )


def test_new_answer_returns_created_conversation_id() -> None:
    service = FakeConversationRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain this material.",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["conversation_id"] == str(
        CONVERSATION_ID,
    )

    assert body["outcome"] == "no_context"

    assert len(
        service.requests,
    ) == 1

    assert service.requests[0].conversation_id is None
    assert service.requests[0].user_id == USER_ID


def test_existing_conversation_id_is_forwarded() -> None:
    service = FakeConversationRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Continue the discussion.",
                "conversation_id": str(
                    CONVERSATION_ID,
                ),
            },
        )

    assert response.status_code == 200

    assert response.json()[
        "conversation_id"
    ] == str(
        CONVERSATION_ID,
    )

    assert (
        service.requests[0].conversation_id
        == CONVERSATION_ID
    )


@pytest.mark.parametrize(
    (
        "error",
        "expected_status",
        "expected_code",
    ),
    (
        (
            StudyConversationValidationError(
                "Private validation details.",
            ),
            400,
            "STUDY_CONVERSATION_VALIDATION_FAILED",
        ),
        (
            StudyConversationNotFoundError(
                "Private not-found details.",
            ),
            404,
            "STUDY_CONVERSATION_NOT_FOUND",
        ),
        (
            StudyConversationPersistenceError(
                "Private persistence details.",
            ),
            503,
            "STUDY_CONVERSATION_PERSISTENCE_FAILED",
        ),
        (
            StudyConversationResponseError(
                "Private response details.",
            ),
            500,
            "STUDY_CONVERSATION_RESPONSE_FAILED",
        ),
    ),
)
def test_endpoint_maps_conversation_errors(
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = FakeConversationRagService(
        error=error,
    )

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain this material.",
            },
        )

    assert response.status_code == expected_status
    assert response.json()["error_code"] == expected_code
    assert "Private" not in response.text


def test_openapi_requires_response_conversation_id() -> None:
    app = FastAPI()

    app.include_router(
        rag_router,
        prefix="/api",
    )

    schema = app.openapi()[
        "components"
    ][
        "schemas"
    ][
        "RagAnswerResponse"
    ]

    assert "conversation_id" in schema[
        "properties"
    ]

    assert "conversation_id" in schema[
        "required"
    ]