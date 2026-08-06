# File: /backend/tests/test_rag_api_contract.py

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.ai.grounded_answer_contracts import (
    NO_CONTEXT_ANSWER,
    GroundedAnswerRequest,
    GroundedAnswerResult,
)
from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.rag_orchestration_dependency import (
    get_rag_orchestration_service,
)
from app.api.router import api_router
from app.api.validation_error_handler import (
    handle_request_validation_error,
)
from app.schemas.rag import (
    DEFAULT_RAG_MATCH_COUNT,
    DEFAULT_RAG_SIMILARITY_THRESHOLD,
    MAX_RAG_MATCH_COUNT,
    MAX_RAG_QUESTION_CHARACTERS,
)
from app.services.rag_orchestration import (
    RagOrchestrationRequest,
    RagOrchestrationResult,
)
from app.services.retrieval_orchestration import (
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


class FakeRagService:
    """Record valid requests and return no-context responses."""

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
        """Return a controlled no-context orchestration result."""

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


def create_test_client(
    service: FakeRagService,
) -> TestClient:
    """Create an isolated authenticated RAG API."""

    app = FastAPI()

    app.add_exception_handler(
    RequestValidationError,
    handle_request_validation_error,
    )

    app.include_router(
        api_router,
        prefix="/api",
    )

    app.dependency_overrides[
        require_authenticated_user
    ] = lambda: AuthenticatedUser(
        user_id=USER_ID,
    )

    app.dependency_overrides[
        get_rag_orchestration_service
    ] = lambda: service

    return TestClient(
        app,
    )


def test_minimal_request_uses_documented_defaults() -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": (
                    "  Explain the uploaded material.  "
                ),
            },
        )

    assert response.status_code == 200

    assert len(
        service.requests,
    ) == 1

    request = service.requests[0]

    assert request.user_id == USER_ID
    assert request.question == (
        "Explain the uploaded material."
    )
    assert request.study_file_id is None
    assert request.subject_id is None
    assert request.match_count == DEFAULT_RAG_MATCH_COUNT
    assert request.similarity_threshold == (
        DEFAULT_RAG_SIMILARITY_THRESHOLD
    )


@pytest.mark.parametrize(
    "method",
    [
        "GET",
        "PUT",
        "PATCH",
        "DELETE",
    ],
)
def test_endpoint_rejects_unsupported_methods(
    method: str,
) -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.request(
            method,
            "/api/rag/answer",
        )

    assert response.status_code == 405
    assert service.requests == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "question": "",
        },
        {
            "question": "   ",
        },
        {
            "question": (
                "x"
                * (
                    MAX_RAG_QUESTION_CHARACTERS
                    + 1
                )
            ),
        },
    ],
)
def test_endpoint_rejects_invalid_question_payloads(
    payload: dict[str, object],
) -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json=payload,
        )

    assert response.status_code == 422
    assert service.requests == []


@pytest.mark.parametrize(
    "payload",
    [
        {
            "question": "Valid question.",
            "study_file_id": "not-a-uuid",
        },
        {
            "question": "Valid question.",
            "subject_id": "not-a-uuid",
        },
        {
            "question": "Valid question.",
            "match_count": 0,
        },
        {
            "question": "Valid question.",
            "match_count": (
                MAX_RAG_MATCH_COUNT
                + 1
            ),
        },
        {
            "question": "Valid question.",
            "similarity_threshold": -0.01,
        },
        {
            "question": "Valid question.",
            "similarity_threshold": 1.01,
        },
    ],
)
def test_endpoint_rejects_invalid_filter_values(
    payload: dict[str, object],
) -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json=payload,
        )

    assert response.status_code == 422
    assert service.requests == []


@pytest.mark.parametrize(
    "internal_field",
    [
        "user_id",
        "chunk_id",
        "embedding",
        "access_token",
        "processor_key",
    ],
)
def test_endpoint_rejects_internal_fields(
    internal_field: str,
) -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Valid question.",
                internal_field: "not-allowed",
            },
        )

    assert response.status_code == 422
    assert service.requests == []


def test_endpoint_accepts_valid_optional_filters() -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain the selected notes.",
                "study_file_id": str(
                    FILE_ID,
                ),
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "match_count": 4,
                "similarity_threshold": 0.80,
            },
        )

    assert response.status_code == 200

    request = service.requests[0]

    assert request.study_file_id == FILE_ID
    assert request.subject_id == SUBJECT_ID
    assert request.match_count == 4
    assert request.similarity_threshold == 0.80


def test_no_context_response_contract_is_stable() -> None:
    service = FakeRagService()

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Explain the material.",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "outcome": "no_context",
        "answer": NO_CONTEXT_ANSWER,
        "sources": [],
        "retrieved_count": 0,
        "source_count": 0,
        "context_available": False,
    }


def test_validation_response_does_not_echo_internal_values() -> None:
    service = FakeRagService()

    private_value = (
        "private-token-value-that-must-not-be-returned"
    )

    with create_test_client(
        service,
    ) as client:
        response = client.post(
            "/api/rag/answer",
            json={
                "question": "Valid question.",
                "access_token": private_value,
            },
        )

    assert response.status_code == 422
    assert private_value not in response.text
    assert service.requests == []

    body = response.json()

    assert "detail" in body
    assert isinstance(
        body["detail"],
        list,
    )

    assert body["detail"]

    first_error = body["detail"][0]

    assert "type" in first_error
    assert "loc" in first_error
    assert "msg" in first_error
    assert "input" not in first_error
    assert "ctx" not in first_error


def test_openapi_registers_public_rag_schemas() -> None:
    app = FastAPI()

    app.include_router(
        api_router,
        prefix="/api",
    )

    component_schemas = app.openapi()[
        "components"
    ][
        "schemas"
    ]

    expected_schemas = {
        "RagAnswerOutcome",
        "RagAnswerRequest",
        "RagAnswerResponse",
        "RagApiErrorResponse",
        "RagSourceResponse",
    }

    assert expected_schemas.issubset(
        component_schemas.keys()
    )

    request_properties = component_schemas[
        "RagAnswerRequest"
    ][
        "properties"
    ]

    assert "user_id" not in request_properties
    assert "access_token" not in request_properties
    assert "embedding" not in request_properties
    assert "chunk_id" not in request_properties