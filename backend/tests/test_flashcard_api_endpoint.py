# File: /backend/tests/test_flashcard_api_endpoint.py
# Purpose: Tests authenticated Flashcard generation, listing,
# retrieval, deletion, and controlled API errors without
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
from app.api.flashcard_dependency import (
    get_flashcard_service,
)
from app.api.flashcard_orchestration_dependency import (
    get_flashcard_orchestration_service,
)
from app.api.routes.flashcards import (
    router as flashcard_router,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.schemas.flashcard import (
    FlashcardDeckResponse,
    FlashcardGenerateRequest,
    FlashcardItem,
    FlashcardLocatorType,
    FlashcardScopeType,
    FlashcardSource,
)
from app.schemas.flashcard_summary import (
    FlashcardDeckSummary,
)
from app.services.flashcard_errors import (
    FlashcardGenerationError,
    FlashcardGenerationResponseError,
    FlashcardPersistenceError,
    FlashcardSourceNotFoundError,
    FlashcardSourceUnavailableError,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

DECK_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

STUDY_FILE_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def _cards() -> tuple[
    FlashcardItem,
    ...,
]:
    """Return one safe five-card deck."""

    return tuple(
        FlashcardItem(
            question=f"Question {index}",
            answer=f"Answer {index}",
        )
        for index in range(
            1,
            6,
        )
    )


def _sources() -> tuple[
    FlashcardSource,
    ...,
]:
    """Return safe source metadata."""

    return (
        FlashcardSource(
            study_file_id=STUDY_FILE_ID,
            source_name="Biology Notes.pdf",
            chunk_index=0,
            locator_type=FlashcardLocatorType.PAGE,
            locator_label="Page 1",
        ),
    )


def make_flashcard_deck() -> FlashcardDeckResponse:
    """Return one safe Flashcard API response."""

    now = datetime.now(
        UTC,
    )

    return FlashcardDeckResponse(
        id=DECK_ID,
        subject_id=SUBJECT_ID,
        study_file_id=STUDY_FILE_ID,
        scope_type=FlashcardScopeType.FILE,
        title="Biology Notes Flashcards",
        requested_card_count=5,
        cards=_cards(),
        sources=_sources(),
        generation_model="fake-model",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


def make_flashcard_summary() -> FlashcardDeckSummary:
    """Return one safe saved-deck summary."""

    deck = make_flashcard_deck()

    return FlashcardDeckSummary(
        id=deck.id,
        subject_id=deck.subject_id,
        study_file_id=deck.study_file_id,
        scope_type=deck.scope_type,
        title=deck.title,
        requested_card_count=deck.requested_card_count,
        sources=deck.sources,
        generation_model=deck.generation_model,
        generation_count=deck.generation_count,
        generated_at=deck.generated_at,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


class FakeFlashcardService:
    """Record synchronous saved-Flashcard API operations."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
        missing_deck: bool = False,
    ) -> None:
        self.error = error
        self.missing_deck = missing_deck

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

    def list_decks(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
    ) -> tuple[
        FlashcardDeckSummary,
        ...,
    ]:
        """Return one controlled saved-deck listing."""

        self.calls.append(
            (
                "list",
                user_id,
                subject_id,
            )
        )

        self._raise_error()

        return (
            make_flashcard_summary(),
        )

    def get_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> FlashcardDeckResponse | None:
        """Return one controlled saved deck."""

        self.calls.append(
            (
                "get",
                user_id,
                deck_id,
            )
        )

        self._raise_error()

        if self.missing_deck:
            return None

        return make_flashcard_deck()

    def delete_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> bool:
        """Delete one controlled saved deck."""

        self.calls.append(
            (
                "delete",
                user_id,
                deck_id,
            )
        )

        self._raise_error()

        return not self.missing_deck


class FakeFlashcardOrchestrationService:
    """Record asynchronous Flashcard generation requests."""

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

    async def generate_deck(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> FlashcardDeckResponse:
        """Return one controlled generated deck."""

        self.calls.append(
            (
                "generate",
                user_id,
                request,
            )
        )

        if self.error is not None:
            raise self.error

        return make_flashcard_deck()


class UnusedFakeSupabaseClient:
    """Placeholder when real authentication is unnecessary."""

    auth = object()


def create_test_client(
    *,
    flashcard_service: FakeFlashcardService | None = None,
    orchestration_service: (
        FakeFlashcardOrchestrationService | None
    ) = None,
    authenticated: bool = True,
) -> TestClient:
    """Create an isolated Flashcard API application."""

    app = FastAPI()

    app.include_router(
        flashcard_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_flashcard_service
    ] = lambda: (
        flashcard_service
        if flashcard_service is not None
        else FakeFlashcardService()
    )

    app.dependency_overrides[
        get_flashcard_orchestration_service
    ] = lambda: (
        orchestration_service
        if orchestration_service is not None
        else FakeFlashcardOrchestrationService()
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


def test_generate_flashcards_uses_authenticated_owner() -> None:
    """Generation must use the authenticated student's UUID."""

    orchestration = (
        FakeFlashcardOrchestrationService()
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body[
        "id"
    ] == str(
        DECK_ID,
    )

    assert (
        body[
            "title"
        ]
        == "Biology Notes Flashcards"
    )

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
        FlashcardGenerateRequest,
    )

    assert request.subject_id == SUBJECT_ID
    assert request.study_file_id == STUDY_FILE_ID
    assert request.card_count == 5


def test_list_flashcards_uses_authenticated_owner() -> None:
    """Saved deck listing must remain owner scoped."""

    service = FakeFlashcardService()

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.get(
            "/api/flashcards",
        )

    assert response.status_code == 200

    body = response.json()

    assert len(
        body[
            "items"
        ]
    ) == 1

    assert (
        body[
            "items"
        ][
            0
        ][
            "id"
        ]
        == str(
            DECK_ID,
        )
    )

    assert service.calls == [
        (
            "list",
            USER_ID,
            None,
        )
    ]


def test_list_flashcards_can_filter_subject() -> None:
    """Saved deck listing may be narrowed to one subject."""

    service = FakeFlashcardService()

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.get(
            "/api/flashcards"
            f"?subject_id={SUBJECT_ID}"
        )

    assert response.status_code == 200

    assert service.calls == [
        (
            "list",
            USER_ID,
            SUBJECT_ID,
        )
    ]

def test_get_flashcard_deck_uses_authenticated_owner() -> None:
    """Single-deck retrieval must remain owner scoped."""

    service = FakeFlashcardService()

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.get(
            f"/api/flashcards/{DECK_ID}",
        )

    assert response.status_code == 200

    assert (
        response.json()[
            "id"
        ]
        == str(
            DECK_ID,
        )
    )

    assert service.calls == [
        (
            "get",
            USER_ID,
            DECK_ID,
        )
    ]


def test_delete_flashcard_deck_returns_no_content() -> None:
    """Successful deletion must return HTTP 204."""

    service = FakeFlashcardService()

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.delete(
            f"/api/flashcards/{DECK_ID}",
        )

    assert response.status_code == 204
    assert response.content == b""

    assert service.calls == [
        (
            "delete",
            USER_ID,
            DECK_ID,
        )
    ]


def test_missing_flashcard_deck_returns_404() -> None:
    """Missing owned decks must return a safe 404."""

    service = FakeFlashcardService(
        missing_deck=True,
    )

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.get(
            f"/api/flashcards/{DECK_ID}",
        )

    assert response.status_code == 404

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_NOT_FOUND"
    )


def test_delete_missing_flashcard_deck_returns_404() -> None:
    """Deleting a missing owned deck must return 404."""

    service = FakeFlashcardService(
        missing_deck=True,
    )

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.delete(
            f"/api/flashcards/{DECK_ID}",
        )

    assert response.status_code == 404

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_NOT_FOUND"
    )


def test_missing_source_returns_404() -> None:
    """Missing owned source material must return 404."""

    orchestration = (
        FakeFlashcardOrchestrationService(
            error=FlashcardSourceNotFoundError(
                "missing source",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 404

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_NOT_FOUND"
    )


def test_unready_source_returns_409() -> None:
    """Unready source material must return a safe conflict."""

    orchestration = (
        FakeFlashcardOrchestrationService(
            error=FlashcardSourceUnavailableError(
                "not ready",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 409

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_SOURCE_UNAVAILABLE"
    )


def test_generation_failure_returns_502() -> None:
    """AI-provider failures must become safe gateway errors."""

    orchestration = (
        FakeFlashcardOrchestrationService(
            error=FlashcardGenerationError(
                "provider failed",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 502

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_GENERATION_FAILED"
    )


def test_invalid_generation_response_returns_500() -> None:
    """Malformed AI output must become a safe internal error."""

    orchestration = (
        FakeFlashcardOrchestrationService(
            error=FlashcardGenerationResponseError(
                "bad response",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 500

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_GENERATION_RESPONSE_FAILED"
    )


def test_persistence_failure_returns_503() -> None:
    """Flashcard storage failure must be service unavailable."""

    service = FakeFlashcardService(
        error=FlashcardPersistenceError(
            "database unavailable",
        ),
    )

    with create_test_client(
        flashcard_service=service,
    ) as client:
        response = client.get(
            "/api/flashcards",
        )

    assert response.status_code == 503

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_PERSISTENCE_FAILED"
    )


def test_source_storage_failure_returns_503() -> None:
    """Trusted source-storage failures must be hidden safely."""

    orchestration = (
        FakeFlashcardOrchestrationService(
            error=SupabaseAdminError(
                "source storage unavailable",
            ),
        )
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 503

    assert (
        response.json()[
            "error_code"
        ]
        == "FLASHCARD_SOURCE_STORAGE_FAILED"
    )


def test_generate_requires_authentication() -> None:
    """Generation must reject missing student authentication."""

    with create_test_client(
        authenticated=False,
    ) as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 5,
            },
        )

    assert response.status_code == 401

    assert (
        response.json()[
            "detail"
        ]
        == "Student authentication is required."
    )


def test_invalid_card_count_returns_422() -> None:
    """FastAPI must enforce the public Flashcard request schema."""

    with create_test_client() as client:
        response = client.post(
            "/api/flashcards/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "card_count": 4,
            },
        )

    assert response.status_code == 422