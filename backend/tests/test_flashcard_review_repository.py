# File: /backend/tests/test_flashcard_review_repository.py
# Purpose: Verifies owner-scoped Flashcard review persistence.

from __future__ import annotations

from typing import Self
from uuid import UUID

import pytest

from app.repositories.flashcard_review_repository import (
    FlashcardReviewRepository,
)
from app.schemas.flashcard_review import (
    FlashcardReviewOutcome,
)
from app.services.flashcard_review_errors import (
    FlashcardReviewNotFoundError,
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


class FakeResponse:
    """Minimal Supabase response."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record one fake Supabase query chain."""

    def __init__(
        self,
        *,
        table_name: str,
        client: FakeClient,
    ) -> None:
        self.table_name = table_name
        self.client = client

        self.filters: list[
            tuple[
                str,
                object,
            ]
        ] = []

        self.selected_columns: str | None = None

        self.inserted_payload: dict[
            str,
            object,
        ] | None = None

    def select(
        self,
        columns: str,
    ) -> Self:
        self.selected_columns = columns
        return self

    def insert(
        self,
        payload: dict[
            str,
            object,
        ],
    ) -> Self:
        self.inserted_payload = payload
        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self:
        self.filters.append(
            (
                column,
                value,
            ),
        )
        return self

    def execute(
        self,
    ) -> FakeResponse:
        if self.table_name == "flashcard_decks":
            return FakeResponse(
                self.client.deck_rows,
            )

        if self.table_name == "flashcards":
            return FakeResponse(
                self.client.card_rows,
            )

        return FakeResponse(
            self.client.review_rows,
        )


class FakeClient:
    """Provide deterministic Flashcard review table responses."""

    def __init__(self) -> None:
        self.deck_rows: object = [
            {
                "id": str(
                    DECK_ID,
                ),
            },
        ]

        self.card_rows: object = [
            {
                "id": "card-1",
            },
        ]

        self.review_rows: object = [
            {
                "id": str(
                    REVIEW_ID,
                ),
                "deck_id": str(
                    DECK_ID,
                ),
                "card_position": 1,
                "outcome": "known",
                "reviewed_at": (
                    "2026-08-11T08:00:00+00:00"
                ),
            },
        ]

        self.queries: list[
            FakeQuery
        ] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        query = FakeQuery(
            table_name=table_name,
            client=self,
        )

        self.queries.append(
            query,
        )

        return query


def test_create_review_checks_owner_and_card_then_inserts() -> None:
    """Review persistence validates the owned target before insert."""

    client = FakeClient()

    repository = FlashcardReviewRepository(
        client,
    )

    response = repository.create_review(
        user_id=USER_ID,
        deck_id=DECK_ID,
        card_position=1,
        outcome=FlashcardReviewOutcome.KNOWN,
    )

    assert response.id == REVIEW_ID
    assert response.deck_id == DECK_ID
    assert response.card_position == 1
    assert response.outcome is FlashcardReviewOutcome.KNOWN

    deck_query = client.queries[0]

    assert deck_query.filters == [
        (
            "id",
            str(DECK_ID),
        ),
        (
            "user_id",
            str(USER_ID),
        ),
    ]

    card_query = client.queries[1]

    assert card_query.filters == [
        (
            "deck_id",
            str(DECK_ID),
        ),
        (
            "position",
            1,
        ),
    ]

    insert_query = client.queries[2]

    assert insert_query.inserted_payload == {
        "user_id": str(
            USER_ID,
        ),
        "deck_id": str(
            DECK_ID,
        ),
        "card_position": 1,
        "outcome": "known",
    }


def test_missing_owned_deck_is_rejected() -> None:
    """A student cannot review a deck that is not owned."""

    client = FakeClient()
    client.deck_rows = []

    repository = FlashcardReviewRepository(
        client,
    )

    with pytest.raises(
        FlashcardReviewNotFoundError,
        match="deck was not found",
    ):
        repository.create_review(
            user_id=USER_ID,
            deck_id=DECK_ID,
            card_position=0,
            outcome=FlashcardReviewOutcome.KNOWN,
        )


def test_missing_card_position_is_rejected() -> None:
    """A review cannot target a nonexistent card position."""

    client = FakeClient()
    client.card_rows = []

    repository = FlashcardReviewRepository(
        client,
    )

    with pytest.raises(
        FlashcardReviewNotFoundError,
        match="card was not found",
    ):
        repository.create_review(
            user_id=USER_ID,
            deck_id=DECK_ID,
            card_position=99,
            outcome=FlashcardReviewOutcome.REVIEW_AGAIN,
        )