# File: /backend/tests/test_flashcard_review_api_endpoint.py
# Purpose: Verifies authenticated Flashcard review API behavior.

from datetime import (
    datetime,
    timezone,
)
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import (
    TestClient,
)

from app.api.authenticated_user_dependency import (
    require_authenticated_user,
)
from app.api.flashcard_review_dependency import (
    get_flashcard_review_service,
)
from app.main import app
from app.schemas.flashcard_review import (
    FlashcardReviewOutcome,
    FlashcardReviewResponse,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

DECK_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

REVIEW_ID = UUID(
    "33333333-3333-4333-8333-333333333333",
)


def _authenticated_user() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=USER_ID,
    )


class FakeFlashcardReviewService:
    """Return one deterministic persisted review."""

    def record_review(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        card_position: int,
        outcome: FlashcardReviewOutcome,
    ) -> FlashcardReviewResponse:
        assert user_id == USER_ID
        assert deck_id == DECK_ID

        return FlashcardReviewResponse(
            id=REVIEW_ID,
            deck_id=deck_id,
            card_position=card_position,
            outcome=outcome,
            reviewed_at=datetime(
                2026,
                8,
                11,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        )


def _review_service() -> FakeFlashcardReviewService:
    return FakeFlashcardReviewService()


def test_flashcard_review_requires_authentication() -> None:
    """Review writes must reject unauthenticated students."""

    with TestClient(
        app,
    ) as client:
        response = client.post(
            (
                f"/api/flashcards/"
                f"{DECK_ID}/reviews"
            ),
            json={
                "card_position": 0,
                "outcome": "known",
            },
        )

    assert response.status_code == 401


def test_authenticated_student_can_record_known_review() -> None:
    """Authenticated students can persist known-card evidence."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_flashcard_review_service
    ] = _review_service

    try:
        with TestClient(
            app,
        ) as client:
            response = client.post(
                (
                    f"/api/flashcards/"
                    f"{DECK_ID}/reviews"
                ),
                json={
                    "card_position": 2,
                    "outcome": "known",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    payload = response.json()

    assert payload["deck_id"] == str(
        DECK_ID,
    )
    assert payload["card_position"] == 2
    assert payload["outcome"] == "known"


def test_flashcard_review_rejects_invalid_outcome() -> None:
    """Unsupported self-assessment values fail request validation."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user

    app.dependency_overrides[
        get_flashcard_review_service
    ] = _review_service

    try:
        with TestClient(
            app,
        ) as client:
            response = client.post(
                (
                    f"/api/flashcards/"
                    f"{DECK_ID}/reviews"
                ),
                json={
                    "card_position": 0,
                    "outcome": "easy",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422