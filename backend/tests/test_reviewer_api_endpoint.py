# File: /backend/tests/test_reviewer_api_endpoint.py
# Purpose: Tests authenticated reviewer API endpoints without
# requiring live Supabase or Gemini services.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.reviewer_dependency import (
    get_reviewer_service,
)
from app.api.reviewer_orchestration_dependency import (
    get_reviewer_orchestration_service,
)
from app.api.routes.reviewers import (
    router as reviewer_router,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerDefinition,
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerListResponse,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
    ReviewerTopic,
)
from app.services.reviewer_errors import (
    ReviewerGenerationError,
    ReviewerNotFoundError,
    ReviewerPersistenceError,
    ReviewerSourceUnavailableError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

REVIEWER_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

STUDY_FILE_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_reviewer() -> ReviewerResponse:
    """Return one safe reviewer API response."""

    now = datetime.now(
        UTC,
    )

    return ReviewerResponse(
        id=REVIEWER_ID,
        subject_id=SUBJECT_ID,
        study_file_id=STUDY_FILE_ID,
        scope_type=ReviewerScopeType.FILE,
        title="Biology Reviewer",
        reviewer_length=ReviewerLength.MEDIUM,
        content=ReviewerContent(
            overview="Biology lesson overview.",
            topics=(
                ReviewerTopic(
                    title="Photosynthesis",
                    summary=(
                        "Summary of the uploaded lesson."
                    ),
                    key_points=(
                        "Plants convert light energy.",
                    ),
                    definitions=(
                        ReviewerDefinition(
                            term="Photosynthesis",
                            definition=(
                                "A process described in "
                                "the uploaded material."
                            ),
                        ),
                    ),
                ),
            ),
        ),
        sources=(
            ReviewerSource(
                study_file_id=STUDY_FILE_ID,
                source_name="Biology Notes.pdf",
                chunk_index=0,
                locator_type="page",
                locator_label="Page 1",
            ),
        ),
        generation_model="fake-model",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


class FakeReviewerService:
    """Record synchronous saved-reviewer API operations."""

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

    def list_reviewers(
        self,
        *,
        user_id: UUID,
        limit: int,
    ) -> ReviewerListResponse:
        self.calls.append(
            (
                "list",
                user_id,
                limit,
            )
        )

        self._raise_error()

        return ReviewerListResponse(
            items=(
                make_reviewer(),
            ),
        )

    def get_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse:
        self.calls.append(
            (
                "get",
                user_id,
                reviewer_id,
            )
        )

        self._raise_error()

        return make_reviewer()

    def delete_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> None:
        self.calls.append(
            (
                "delete",
                user_id,
                reviewer_id,
            )
        )

        self._raise_error()


class FakeReviewerOrchestrationService:
    """Record asynchronous reviewer generation requests."""

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

    async def generate_reviewer(
        self,
        *,
        user_id: UUID,
        request: ReviewerGenerateRequest,
    ) -> ReviewerResponse:
        self.calls.append(
            (
                "generate",
                user_id,
                request,
            )
        )

        if self.error is not None:
            raise self.error

        return make_reviewer()


class UnusedFakeSupabaseClient:
    """Placeholder used when real authentication is not needed."""

    auth = object()


def create_test_client(
    *,
    reviewer_service: FakeReviewerService | None = None,
    orchestration_service: (
        FakeReviewerOrchestrationService | None
    ) = None,
    authenticated: bool = True,
) -> TestClient:
    """Create an isolated reviewer API application."""

    app = FastAPI()

    app.include_router(
        reviewer_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_reviewer_service
    ] = lambda: (
        reviewer_service
        if reviewer_service is not None
        else FakeReviewerService()
    )

    app.dependency_overrides[
        get_reviewer_orchestration_service
    ] = lambda: (
        orchestration_service
        if orchestration_service is not None
        else FakeReviewerOrchestrationService()
    )

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


def test_generate_reviewer_uses_authenticated_owner() -> None:
    """Generation must use authenticated ownership."""

    orchestration = (
        FakeReviewerOrchestrationService()
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/reviewers/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "reviewer_length": "medium",
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(
        REVIEWER_ID,
    )

    assert body["title"] == "Biology Reviewer"
    assert "user_id" not in body

    call = orchestration.calls[
        0
    ]

    assert call[
        0
    ] == "generate"

    assert call[
        1
    ] == USER_ID

    request = call[
        2
    ]

    assert isinstance(
        request,
        ReviewerGenerateRequest,
    )

    assert request.study_file_id == STUDY_FILE_ID


def test_list_reviewers_uses_default_limit() -> None:
    """Saved reviewer lists must use the authenticated owner."""

    service = FakeReviewerService()

    with create_test_client(
        reviewer_service=service,
    ) as client:
        response = client.get(
            "/api/reviewers",
        )

    assert response.status_code == 200

    assert len(
        response.json()[
            "items"
        ]
    ) == 1

    assert service.calls == [
        (
            "list",
            USER_ID,
            20,
        )
    ]


def test_get_reviewer_uses_authenticated_owner() -> None:
    """Single reviewer retrieval must remain ownership scoped."""

    service = FakeReviewerService()

    with create_test_client(
        reviewer_service=service,
    ) as client:
        response = client.get(
            f"/api/reviewers/{REVIEWER_ID}",
        )

    assert response.status_code == 200

    assert response.json()[
        "id"
    ] == str(
        REVIEWER_ID,
    )

    assert service.calls == [
        (
            "get",
            USER_ID,
            REVIEWER_ID,
        )
    ]


def test_delete_reviewer_returns_no_content() -> None:
    """Successful reviewer deletion must return HTTP 204."""

    service = FakeReviewerService()

    with create_test_client(
        reviewer_service=service,
    ) as client:
        response = client.delete(
            f"/api/reviewers/{REVIEWER_ID}",
        )

    assert response.status_code == 204
    assert response.content == b""

    assert service.calls == [
        (
            "delete",
            USER_ID,
            REVIEWER_ID,
        )
    ]


def test_missing_reviewer_returns_404() -> None:
    """Owned lookup failures must return a safe 404."""

    service = FakeReviewerService(
        error=ReviewerNotFoundError(
            "missing",
        ),
    )

    with create_test_client(
        reviewer_service=service,
    ) as client:
        response = client.get(
            f"/api/reviewers/{REVIEWER_ID}",
        )

    assert response.status_code == 404

    assert response.json()[
        "error_code"
    ] == "REVIEWER_NOT_FOUND"


def test_unready_source_returns_409() -> None:
    """Reviewer generation must expose a safe source-state conflict."""

    orchestration = (
        FakeReviewerOrchestrationService(
            error=ReviewerSourceUnavailableError(
                "not ready",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/reviewers/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "reviewer_length": "medium",
            },
        )

    assert response.status_code == 409

    assert response.json()[
        "error_code"
    ] == "REVIEWER_SOURCE_UNAVAILABLE"


def test_generation_failure_returns_502() -> None:
    """Provider failures must return a safe gateway error."""

    orchestration = (
        FakeReviewerOrchestrationService(
            error=ReviewerGenerationError(
                "provider failed",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/reviewers/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "reviewer_length": "medium",
            },
        )

    assert response.status_code == 502

    assert response.json()[
        "error_code"
    ] == "REVIEWER_GENERATION_FAILED"


def test_persistence_failure_returns_503() -> None:
    """Reviewer storage failures must be service-unavailable errors."""

    service = FakeReviewerService(
        error=ReviewerPersistenceError(
            "database unavailable",
        ),
    )

    with create_test_client(
        reviewer_service=service,
    ) as client:
        response = client.get(
            "/api/reviewers",
        )

    assert response.status_code == 503

    assert response.json()[
        "error_code"
    ] == "REVIEWER_PERSISTENCE_FAILED"


def test_invalid_list_limit_returns_422() -> None:
    """FastAPI must validate reviewer list bounds."""

    with create_test_client() as client:
        response = client.get(
            "/api/reviewers?limit=101",
        )

    assert response.status_code == 422