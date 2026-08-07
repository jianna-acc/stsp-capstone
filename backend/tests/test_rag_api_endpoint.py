# File: /backend/tests/test_rag_api_endpoint.py

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
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.api.authenticated_user_dependency import (
    AUTHENTICATION_REQUIRED_MESSAGE,
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.router import api_router
from app.api.routes.rag import router as rag_router
from app.api.study_conversation_rag_dependency import (
    get_study_conversation_rag_service,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.schemas.study_conversation import (
    StudyConversationResponse,
    StudyMessageResponse,
    StudyMessageSourceResponse,
)
from app.services.rag_orchestration import (
    RagOrchestrationGenerationError,
    RagOrchestrationRequest,
    RagOrchestrationResponseError,
    RagOrchestrationResult,
    RagOrchestrationRetrievalError,
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
    "55555555-5555-4555-8555-555555555555"
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)


def make_chunk() -> RetrievedStudyChunk:
    """Create one valid retrieved study chunk."""

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
            "chunk_index": 2,
            "content": content,
            "start_offset": 200,
            "end_offset": 200 + len(
                content,
            ),
            "chunk_metadata": {
                "page_number": 3,
            },
            "embedding_model": "fake-embedding-model",
            "similarity_score": 0.93,
        }
    )


def make_answered_result(
    request: RagOrchestrationRequest,
) -> RagOrchestrationResult:
    """Create one valid answered orchestration result."""

    chunk = make_chunk()

    retrieval_result = RetrievalOrchestrationResult(
        request=request.to_retrieval_request(),
        chunks=(
            chunk,
        ),
        embedding_provider="gemini",
        embedding_model="fake-embedding-model",
        embedding_dimensions=768,
    )

    grounded_request = GroundedAnswerRequest(
        question=request.question,
        chunks=(
            chunk,
        ),
    )

    grounded_result = GroundedAnswerResult.generated(
        request=grounded_request,
        answer=(
            "Photosynthesis converts light energy "
            "into chemical energy. [Source 1]"
        ),
        provider="gemini",
        model="fake-generation-model",
    )

    return RagOrchestrationResult(
        request=request,
        retrieval=retrieval_result,
        grounded_answer=grounded_result,
    )


def make_no_context_result(
    request: RagOrchestrationRequest,
) -> RagOrchestrationResult:
    """Create one valid no-context orchestration result."""

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


class FakeRagService:
    """Return controlled combined RAG results."""

    def __init__(
        self,
        *,
        no_context: bool = False,
        error: Exception | None = None,
    ) -> None:
        self.no_context = no_context
        self.error = error
        self.requests: list[
            RagOrchestrationRequest
        ] = []

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> RagOrchestrationResult:
        """Record and answer one controlled request."""

        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        if self.no_context:
            return make_no_context_result(
                request,
            )

        return make_answered_result(
            request,
        )


class UnusedFakeSupabaseClient:
    """Placeholder client for missing-authentication testing."""

    auth = object()



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
    *,
    service: FakeRagService,
    authenticated_user: AuthenticatedUser | None = None,
) -> TestClient:
    """Create an isolated FastAPI application."""

    app = FastAPI()

    app.include_router(
        rag_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_study_conversation_rag_service
    ] = lambda: FakeConversationRagServiceAdapter(
        service,
    )

    if authenticated_user is not None:
        app.dependency_overrides[
            require_authenticated_user
        ] = lambda: authenticated_user

    app.dependency_overrides[
        get_supabase_client
    ] = lambda: UnusedFakeSupabaseClient()

    return TestClient(
        app,
    )


def test_answer_endpoint_returns_grounded_answer() -> None:
    service = FakeRagService()

    with create_test_client(
        service=service,
        authenticated_user=AuthenticatedUser(
            user_id=USER_ID,
        ),
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "What is photosynthesis?",
                "study_file_id": str(
                    FILE_ID,
                ),
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "match_count": 5,
                "similarity_threshold": 0.75,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["outcome"] == "answered"
    assert body["context_available"] is True
    assert body["retrieved_count"] == 1
    assert body["source_count"] == 1
    assert body["answer"].endswith(
        "[Source 1]"
    )

    assert body["sources"] == [
        {
            "source_number": 1,
            "source_name": "Biology Notes.pdf",
            "chunk_index": 2,
            "similarity_score": 0.93,
        }
    ]

    assert len(
        service.requests,
    ) == 1

    captured_request = service.requests[0]

    assert captured_request.user_id == USER_ID
    assert captured_request.study_file_id == FILE_ID
    assert captured_request.subject_id == SUBJECT_ID
    assert captured_request.match_count == 5
    assert captured_request.similarity_threshold == 0.75


def test_endpoint_returns_no_context_response() -> None:
    service = FakeRagService(
        no_context=True,
    )

    with create_test_client(
        service=service,
        authenticated_user=AuthenticatedUser(
            user_id=USER_ID,
        ),
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain an unavailable topic.",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["outcome"] == "no_context"
    assert body["context_available"] is False
    assert body["retrieved_count"] == 0
    assert body["source_count"] == 0
    assert body["sources"] == []


def test_endpoint_requires_student_authentication() -> None:
    service = FakeRagService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "What is photosynthesis?",
            },
        )

    assert response.status_code == 401
    assert response.json() == {
        "detail": AUTHENTICATION_REQUIRED_MESSAGE,
    }

    assert response.headers[
        "www-authenticate"
    ] == "Bearer"

    assert service.requests == []


def test_endpoint_rejects_unknown_request_fields() -> None:
    service = FakeRagService()

    with create_test_client(
        service=service,
        authenticated_user=AuthenticatedUser(
            user_id=USER_ID,
        ),
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Valid question.",
                "user_id": str(
                    uuid4(),
                ),
            },
        )

    assert response.status_code == 422
    assert service.requests == []


@pytest.mark.parametrize(
    (
        "error",
        "expected_status",
        "expected_code",
    ),
    [
        (
            RagOrchestrationValidationError(
                "Private validation details.",
            ),
            400,
            "RAG_ORCHESTRATION_VALIDATION_FAILED",
        ),
        (
            RagOrchestrationRetrievalError(
                "Private retrieval details.",
            ),
            503,
            "RAG_ORCHESTRATION_RETRIEVAL_FAILED",
        ),
        (
            RagOrchestrationGenerationError(
                "Private generation details.",
            ),
            502,
            "RAG_ORCHESTRATION_GENERATION_FAILED",
        ),
        (
            RagOrchestrationResponseError(
                "Private response details.",
            ),
            500,
            "RAG_ORCHESTRATION_RESPONSE_FAILED",
        ),
    ],
)
def test_endpoint_maps_controlled_errors(
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = FakeRagService(
        error=error,
    )

    with create_test_client(
        service=service,
        authenticated_user=AuthenticatedUser(
            user_id=USER_ID,
        ),
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain the material.",
            },
        )

    assert response.status_code == expected_status
    assert response.json()["error_code"] == expected_code
    assert "Private" not in response.text


def test_answer_response_excludes_internal_data() -> None:
    service = FakeRagService()

    with create_test_client(
        service=service,
        authenticated_user=AuthenticatedUser(
            user_id=USER_ID,
        ),
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "What is photosynthesis?",
            },
        )

    response_text = response.text

    assert response.status_code == 200
    assert "chunk_id" not in response_text
    assert "study_file_id" not in response_text
    assert "subject_id" not in response_text
    assert "content" not in response_text
    assert "embedding" not in response_text
    assert str(
        USER_ID,
    ) not in response_text


def test_rag_router_is_registered() -> None:
    app = FastAPI()

    app.include_router(
        api_router,
        prefix="/api",
    )

    openapi_paths = app.openapi()[
        "paths"
    ]

    assert "/api/rag/answer" in openapi_paths
    assert "post" in openapi_paths[
        "/api/rag/answer"
    ]
