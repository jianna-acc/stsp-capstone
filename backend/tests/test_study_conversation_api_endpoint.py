# File: /backend/tests/test_study_conversation_api_endpoint.py
# Purpose: Tests authenticated Study Conversation CRUD endpoints
# without requiring a live database.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    AUTHENTICATION_REQUIRED_MESSAGE,
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.router import api_router
from app.api.routes.study_conversations import (
    router as study_conversation_router,
)
from app.api.study_conversation_dependency import (
    get_study_conversation_service,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.schemas.study_conversation import (
    StudyConversationCreateRequest,
    StudyConversationDetailResponse,
    StudyConversationListResponse,
    StudyConversationResponse,
    StudyConversationUpdateRequest,
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationNotFoundError,
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

CONVERSATION_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

STUDY_FILE_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_conversation(
    *,
    title: str = "Biology review",
) -> StudyConversationResponse:
    """Create one safe conversation response."""

    now = datetime.now(
        UTC,
    )

    return StudyConversationResponse(
        id=CONVERSATION_ID,
        title=title,
        subject_id=SUBJECT_ID,
        study_file_id=STUDY_FILE_ID,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )


def make_detail() -> StudyConversationDetailResponse:
    """Create one conversation detail response."""

    conversation = make_conversation()

    return StudyConversationDetailResponse(
        conversation=conversation,
        messages=[
            StudyMessageResponse(
                id=uuid4(),
                conversation_id=CONVERSATION_ID,
                role="user",
                content="What is photosynthesis?",
                created_at=datetime.now(
                    UTC,
                ),
            ),
            StudyMessageResponse(
                id=uuid4(),
                conversation_id=CONVERSATION_ID,
                role="assistant",
                content=(
                    "Photosynthesis converts light energy "
                    "into chemical energy. [Source 1]"
                ),
                outcome="answered",
                sources=[
                    {
                        "source_number": 1,
                        "source_name": "Biology Notes.pdf",
                        "chunk_index": 2,
                        "similarity_score": 0.93,
                    },
                ],
                created_at=datetime.now(
                    UTC,
                ),
            ),
        ],
    )


class FakeConversationService:
    """Record API calls and return controlled responses."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.calls: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def _raise_error(
        self,
    ) -> None:
        if self.error is not None:
            raise self.error

    def create_conversation(
        self,
        *,
        user_id: UUID,
        request: StudyConversationCreateRequest,
    ) -> StudyConversationResponse:
        self.calls.append(
            (
                "create",
                user_id,
                request,
            ),
        )

        self._raise_error()

        return make_conversation(
            title=request.title,
        )

    def list_conversations(
        self,
        *,
        user_id: UUID,
        limit: int,
    ) -> StudyConversationListResponse:
        self.calls.append(
            (
                "list",
                user_id,
                limit,
            ),
        )

        self._raise_error()

        return StudyConversationListResponse(
            items=[
                make_conversation(),
            ],
        )

    def get_conversation_detail(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        message_limit: int,
    ) -> StudyConversationDetailResponse:
        self.calls.append(
            (
                "detail",
                user_id,
                conversation_id,
                message_limit,
            ),
        )

        self._raise_error()

        return make_detail()

    def update_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        request: StudyConversationUpdateRequest,
    ) -> StudyConversationResponse:
        self.calls.append(
            (
                "update",
                user_id,
                conversation_id,
                request,
            ),
        )

        self._raise_error()

        return make_conversation(
            title=request.title
            or "Biology review",
        )

    def delete_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> None:
        self.calls.append(
            (
                "delete",
                user_id,
                conversation_id,
            ),
        )

        self._raise_error()


class UnusedFakeSupabaseClient:
    """Placeholder for missing-authentication tests."""

    auth = object()


def create_test_client(
    *,
    service: FakeConversationService,
    authenticated: bool = True,
) -> TestClient:
    """Create an isolated Study Conversation API."""

    app = FastAPI()

    app.include_router(
        study_conversation_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_study_conversation_service
    ] = lambda: service

    app.dependency_overrides[
        get_supabase_client
    ] = lambda: UnusedFakeSupabaseClient()

    if authenticated:
        app.dependency_overrides[
            require_authenticated_user
        ] = lambda: AuthenticatedUser(
            user_id=USER_ID,
        )

    return TestClient(
        app,
    )


def test_create_conversation_uses_authenticated_owner() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            "/api/study-conversations",
            json={
                "title": "  Biology review  ",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(
        CONVERSATION_ID,
    )

    assert body["title"] == "Biology review"
    assert "user_id" not in body

    call = service.calls[0]

    assert call[0] == "create"
    assert call[1] == USER_ID

    request = call[2]

    assert isinstance(
        request,
        StudyConversationCreateRequest,
    )

    assert request.title == "Biology review"
    assert request.subject_id == SUBJECT_ID
    assert request.study_file_id == STUDY_FILE_ID


def test_list_conversations_uses_default_limit() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/study-conversations",
        )

    assert response.status_code == 200
    assert len(
        response.json()["items"],
    ) == 1

    assert service.calls == [
        (
            "list",
            USER_ID,
            20,
        ),
    ]


def test_get_conversation_loads_messages() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            (
                "/api/study-conversations/"
                f"{CONVERSATION_ID}"
                "?message_limit=100"
            ),
        )

    assert response.status_code == 200

    body = response.json()

    assert body["conversation"]["id"] == str(
        CONVERSATION_ID,
    )

    assert len(
        body["messages"],
    ) == 2

    assert service.calls == [
        (
            "detail",
            USER_ID,
            CONVERSATION_ID,
            100,
        ),
    ]


def test_update_conversation_uses_authenticated_owner() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.patch(
            (
                "/api/study-conversations/"
                f"{CONVERSATION_ID}"
            ),
            json={
                "title": "  Updated review  ",
                "study_file_id": None,
            },
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated review"

    call = service.calls[0]

    assert call[0] == "update"
    assert call[1] == USER_ID
    assert call[2] == CONVERSATION_ID

    request = call[3]

    assert isinstance(
        request,
        StudyConversationUpdateRequest,
    )

    assert request.title == "Updated review"
    assert request.study_file_id is None


def test_delete_conversation_returns_no_content() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.delete(
            (
                "/api/study-conversations/"
                f"{CONVERSATION_ID}"
            ),
        )

    assert response.status_code == 204
    assert response.content == b""

    assert service.calls == [
        (
            "delete",
            USER_ID,
            CONVERSATION_ID,
        ),
    ]


def test_conversation_routes_require_authentication() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
        authenticated=False,
    ) as client:
        response = client.get(
            "/api/study-conversations",
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": AUTHENTICATION_REQUIRED_MESSAGE,
    }

    assert response.headers[
        "www-authenticate"
    ] == "Bearer"

    assert service.calls == []


def test_create_rejects_client_supplied_user_id() -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            "/api/study-conversations",
            json={
                "title": "Biology review",
                "user_id": str(
                    uuid4(),
                ),
            },
        )

    assert response.status_code == 422
    assert service.calls == []


@pytest.mark.parametrize(
    (
        "error",
        "expected_status",
        "expected_code",
    ),
    [
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
                "Private database details.",
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
    ],
)
def test_routes_map_controlled_errors(
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = FakeConversationService(
        error=error,
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            "/api/study-conversations",
        )

    assert response.status_code == expected_status
    assert response.json()["error_code"] == expected_code
    assert "Private" not in response.text


@pytest.mark.parametrize(
    "path",
    [
        "/api/study-conversations?limit=0",
        "/api/study-conversations?limit=51",
        (
            "/api/study-conversations/"
            f"{CONVERSATION_ID}"
            "?message_limit=0"
        ),
        (
            "/api/study-conversations/"
            f"{CONVERSATION_ID}"
            "?message_limit=501"
        ),
    ],
)
def test_routes_reject_invalid_limits(
    path: str,
) -> None:
    service = FakeConversationService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            path,
        )

    assert response.status_code == 422
    assert service.calls == []


def test_conversation_router_is_registered() -> None:
    app = FastAPI()

    app.include_router(
        api_router,
        prefix="/api",
    )

    paths = app.openapi()[
        "paths"
    ]

    collection_path = (
        "/api/study-conversations"
    )

    detail_path = (
        "/api/study-conversations/"
        "{conversation_id}"
    )

    assert collection_path in paths
    assert detail_path in paths

    assert {
        "get",
        "post",
    }.issubset(
        paths[
            collection_path
        ].keys(),
    )

    assert {
        "get",
        "patch",
        "delete",
    }.issubset(
        paths[
            detail_path
        ].keys(),
    )


def test_openapi_registers_conversation_schemas() -> None:
    app = FastAPI()

    app.include_router(
        api_router,
        prefix="/api",
    )

    schemas = app.openapi()[
        "components"
    ][
        "schemas"
    ]

    expected_schemas = {
        "StudyConversationApiErrorResponse",
        "StudyConversationCreateRequest",
        "StudyConversationDetailResponse",
        "StudyConversationListResponse",
        "StudyConversationResponse",
        "StudyConversationUpdateRequest",
        "StudyMessageResponse",
        "StudyMessageSourceResponse",
    }

    assert expected_schemas.issubset(
        schemas.keys(),
    )

    create_properties = schemas[
        "StudyConversationCreateRequest"
    ][
        "properties"
    ]

    assert "user_id" not in create_properties
    assert "access_token" not in create_properties