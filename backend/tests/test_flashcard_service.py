# File: /backend/tests/test_flashcard_service.py
# Purpose: Verifies Flashcard persistence service delegation
# for creation, saved-deck listing, retrieval, and deletion.

from __future__ import annotations

from uuid import UUID, uuid4

from app.schemas.flashcard import (
    FlashcardItem,
    FlashcardScopeType,
)
from app.services.flashcard_service import (
    FlashcardService,
)


class FakeFlashcardRepository:
    """Record Flashcard repository operations."""

    def __init__(self) -> None:
        self.calls: list[
            tuple[
                str,
                object,
            ]
        ] = []

        self.created_result = object()
        self.list_result = (
            object(),
            object(),
        )
        self.get_result = object()
        self.delete_result = True

    def create_deck(
        self,
        **kwargs: object,
    ) -> object:
        self.calls.append(
            (
                "create_deck",
                kwargs,
            )
        )

        return self.created_result

    def list_decks(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
    ) -> object:
        self.calls.append(
            (
                "list_decks",
                {
                    "user_id": user_id,
                    "subject_id": subject_id,
                },
            )
        )

        return self.list_result

    def get_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> object:
        self.calls.append(
            (
                "get_deck",
                {
                    "user_id": user_id,
                    "deck_id": deck_id,
                },
            )
        )

        return self.get_result

    def delete_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> bool:
        self.calls.append(
            (
                "delete_deck",
                {
                    "user_id": user_id,
                    "deck_id": deck_id,
                },
            )
        )

        return self.delete_result


def _cards() -> tuple[
    FlashcardItem,
    ...,
]:
    return (
        FlashcardItem(
            question="Question 1",
            answer="Answer 1",
        ),
        FlashcardItem(
            question="Question 2",
            answer="Answer 2",
        ),
        FlashcardItem(
            question="Question 3",
            answer="Answer 3",
        ),
        FlashcardItem(
            question="Question 4",
            answer="Answer 4",
        ),
        FlashcardItem(
            question="Question 5",
            answer="Answer 5",
        ),
    )


def test_create_deck_delegates_to_repository() -> None:
    """Service must delegate generated persistence unchanged."""

    repository = FakeFlashcardRepository()
    service = FlashcardService(
        repository,
    )

    user_id = uuid4()
    subject_id = uuid4()

    result = service.create_deck(
        user_id=user_id,
        subject_id=subject_id,
        study_file_id=None,
        scope_type=FlashcardScopeType.SUBJECT,
        title="Biology Flashcards",
        requested_card_count=5,
        cards=_cards(),
        sources=(),
        generation_model="gemini-test-model",
    )

    assert result is repository.created_result

    operation, payload = repository.calls[
        0
    ]

    assert operation == "create_deck"

    assert isinstance(
        payload,
        dict,
    )

    assert payload[
        "user_id"
    ] == user_id

    assert payload[
        "subject_id"
    ] == subject_id

    assert payload[
        "requested_card_count"
    ] == 5


def test_list_decks_delegates_owner_and_subject() -> None:
    """Service must preserve listing ownership filters."""

    repository = FakeFlashcardRepository()
    service = FlashcardService(
        repository,
    )

    user_id = uuid4()
    subject_id = uuid4()

    result = service.list_decks(
        user_id=user_id,
        subject_id=subject_id,
    )

    assert result is repository.list_result

    assert repository.calls == [
        (
            "list_decks",
            {
                "user_id": user_id,
                "subject_id": subject_id,
            },
        )
    ]


def test_get_deck_delegates_owner_and_deck_id() -> None:
    """Service retrieval must preserve authenticated owner."""

    repository = FakeFlashcardRepository()
    service = FlashcardService(
        repository,
    )

    user_id = uuid4()
    deck_id = uuid4()

    result = service.get_deck(
        user_id=user_id,
        deck_id=deck_id,
    )

    assert result is repository.get_result

    assert repository.calls == [
        (
            "get_deck",
            {
                "user_id": user_id,
                "deck_id": deck_id,
            },
        )
    ]


def test_delete_deck_delegates_owner_and_deck_id() -> None:
    """Service deletion must preserve authenticated owner."""

    repository = FakeFlashcardRepository()
    service = FlashcardService(
        repository,
    )

    user_id = uuid4()
    deck_id = uuid4()

    result = service.delete_deck(
        user_id=user_id,
        deck_id=deck_id,
    )

    assert result is True

    assert repository.calls == [
        (
            "delete_deck",
            {
                "user_id": user_id,
                "deck_id": deck_id,
            },
        )
    ]