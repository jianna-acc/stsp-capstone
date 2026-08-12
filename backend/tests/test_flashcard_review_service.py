# File: /backend/tests/test_flashcard_review_service.py
# Purpose: Verifies Flashcard review service delegation.

from datetime import (
    datetime,
    timezone,
)
from uuid import UUID

from app.schemas.flashcard_review import (
    FlashcardReviewOutcome,
    FlashcardReviewResponse,
)
from app.services.flashcard_review_service import (
    FlashcardReviewService,
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


class FakeReviewRepository:
    """Record Flashcard review service calls."""

    def __init__(self) -> None:
        self.calls: list[
            tuple[
                UUID,
                UUID,
                int,
                FlashcardReviewOutcome,
            ]
        ] = []

    def create_review(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        card_position: int,
        outcome: FlashcardReviewOutcome,
    ) -> FlashcardReviewResponse:
        self.calls.append(
            (
                user_id,
                deck_id,
                card_position,
                outcome,
            ),
        )

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


def test_record_review_delegates_authenticated_scope() -> None:
    """Service forwards the student, deck, card, and outcome."""

    repository = FakeReviewRepository()

    service = FlashcardReviewService(
        repository,
    )

    response = service.record_review(
        user_id=USER_ID,
        deck_id=DECK_ID,
        card_position=2,
        outcome=FlashcardReviewOutcome.KNOWN,
    )

    assert response.outcome is FlashcardReviewOutcome.KNOWN

    assert repository.calls == [
        (
            USER_ID,
            DECK_ID,
            2,
            FlashcardReviewOutcome.KNOWN,
        ),
    ]


def test_review_again_is_preserved() -> None:
    """Review-again evidence remains distinct from known evidence."""

    repository = FakeReviewRepository()

    service = FlashcardReviewService(
        repository,
    )

    response = service.record_review(
        user_id=USER_ID,
        deck_id=DECK_ID,
        card_position=0,
        outcome=FlashcardReviewOutcome.REVIEW_AGAIN,
    )

    assert response.outcome is (
        FlashcardReviewOutcome.REVIEW_AGAIN
    )