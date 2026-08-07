# File: /backend/tests/test_rag_api_auth_integration.py

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.grounded_answer_contracts import (
    GroundedAnswerRequest,
    GroundedAnswerResult,
)
from app.api.authenticated_user_dependency import (
    INVALID_AUTHENTICATION_MESSAGE,
)
from app.api.router import api_router
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
    RagOrchestrationRequest,
    RagOrchestrationResult,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationResult,
)
from app.services.study_conversation_rag import (
    StudyConversationRagResult,
)

AUTHENTICATED_USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

ATTACKER_USER_ID = UUID(
    "99999999-9999-4999-8999-999999999999"
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

VALID_ACCESS_TOKEN = "valid-student-access-token"


class FakeSupabaseAuth:
    """Synchronous fake for Supabase Auth token validation."""

    def __init__(
        self,
        *,
        user_id: object = AUTHENTICATED_USER_ID,
        error: Exception | None = None,
    ) -> None:
        self.user_id = user_id
        self.error = error
        self.received_tokens: list[str | None] = []

    def get_user(
        self,
        jwt: str | None = None,
    ) -> object:
        """Return a controlled UserResponse-like object."""

        self.received_tokens.append(
            jwt,
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            user=SimpleNamespace(
                id=self.user_id,
            ),
        )


class FakeSupabaseClient:
    """Fake Supabase client containing the Auth interface."""

    def __init__(
        self,
        auth: FakeSupabaseAuth,
    ) -> None:
        self.auth = auth


class FakeRagService:
    """Record RAG requests and return no-context results."""

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
        """Return one controlled no-context result."""

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
    *,
    auth: FakeSupabaseAuth,
    service: FakeRagService,
) -> TestClient:
    """Create an isolated app using the real auth dependency."""

    app = FastAPI()

    app.include_router(
        api_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_supabase_client
    ] = lambda: FakeSupabaseClient(
        auth,
    )

    app.dependency_overrides[
        get_study_conversation_rag_service
    ] = lambda: FakeConversationRagServiceAdapter(
        service,
    )

    return TestClient(
        app,
    )


def bearer_headers(
    token: str = VALID_ACCESS_TOKEN,
) -> dict[str, str]:
    """Return a bearer-token request header."""

    return {
        "Authorization": f"Bearer {token}",
    }


def test_valid_token_binds_request_to_authenticated_user() -> None:
    auth = FakeSupabaseAuth()
    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers=bearer_headers(),
            json={
                "question": "Explain the uploaded material.",
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

    assert auth.received_tokens == [
        VALID_ACCESS_TOKEN,
    ]

    assert len(
        service.requests,
    ) == 1

    captured_request = service.requests[0]

    assert (
        captured_request.user_id
        == AUTHENTICATED_USER_ID
    )

    assert captured_request.study_file_id == FILE_ID
    assert captured_request.subject_id == SUBJECT_ID
    assert captured_request.match_count == 5
    assert captured_request.similarity_threshold == 0.75


def test_client_cannot_submit_user_id() -> None:
    auth = FakeSupabaseAuth()
    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers=bearer_headers(),
            json={
                "question": "Explain the uploaded material.",
                "user_id": str(
                    ATTACKER_USER_ID,
                ),
            },
        )

    assert response.status_code == 422
    assert service.requests == []


def test_processor_key_cannot_authenticate_student() -> None:
    auth = FakeSupabaseAuth()
    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers={
                "X-Processor-Key": "internal-processor-key",
            },
            json={
                "question": "Explain the uploaded material.",
            },
        )

    assert response.status_code == 401
    assert auth.received_tokens == []
    assert service.requests == []

    assert response.headers[
        "www-authenticate"
    ] == "Bearer"


def test_invalid_token_returns_safe_unauthorized_response() -> None:
    auth = FakeSupabaseAuth(
        error=RuntimeError(
            "Private Supabase authentication details.",
        ),
    )

    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers=bearer_headers(
                "invalid-or-expired-token",
            ),
            json={
                "question": "Explain the uploaded material.",
            },
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": INVALID_AUTHENTICATION_MESSAGE,
    }

    assert response.headers[
        "www-authenticate"
    ] == "Bearer"

    assert auth.received_tokens == [
        "invalid-or-expired-token",
    ]

    assert service.requests == []

    assert "Private Supabase" not in response.text


def test_invalid_authenticated_user_id_is_rejected() -> None:
    auth = FakeSupabaseAuth(
        user_id="not-a-valid-uuid",
    )

    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers=bearer_headers(),
            json={
                "question": "Explain the uploaded material.",
            },
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": INVALID_AUTHENTICATION_MESSAGE,
    }

    assert service.requests == []


def test_non_bearer_authorization_is_rejected() -> None:
    auth = FakeSupabaseAuth()
    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers={
                "Authorization": (
                    "Basic dXNlcjpwYXNzd29yZA=="
                ),
            },
            json={
                "question": "Explain the uploaded material.",
            },
        )

    assert response.status_code == 401
    assert auth.received_tokens == []
    assert service.requests == []


def test_response_does_not_expose_authentication_data() -> None:
    auth = FakeSupabaseAuth()
    service = FakeRagService()

    with create_test_client(
        auth=auth,
        service=service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            headers=bearer_headers(),
            json={
                "question": "Explain the uploaded material.",
            },
        )

    assert response.status_code == 200

    response_text = response.text

    assert VALID_ACCESS_TOKEN not in response_text
    assert str(
        AUTHENTICATED_USER_ID,
    ) not in response_text
    assert "authorization" not in response_text.lower()
    assert "access_token" not in response_text.lower()
    assert "processor" not in response_text.lower()