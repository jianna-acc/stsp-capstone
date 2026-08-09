# File: /backend/tests/test_flashcard_repository.py
# Purpose: Verifies owned Flashcard deck persistence,
# retrieval, deletion, RPC usage, and response validation.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.flashcard_repository import (
    FlashcardRepository,
)
from app.schemas.flashcard import (
    FlashcardItem,
    FlashcardLocatorType,
    FlashcardScopeType,
    FlashcardSource,
)
from app.services.flashcard_errors import (
    FlashcardPersistenceError,
    FlashcardResponseError,
    FlashcardValidationError,
)


class FakeResponse:
    """Minimal Supabase-style response."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record chained Supabase table operations."""

    def __init__(
        self,
        response_data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error

        self.operations: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.operations.append(
            (
                "select",
                columns,
            )
        )

        return self

    def delete(
        self,
    ) -> FakeQuery:
        self.operations.append(
            (
                "delete",
                None,
            )
        )

        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "eq",
                (
                    column,
                    value,
                ),
            )
        )

        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> FakeQuery:
        self.operations.append(
            (
                "order",
                (
                    column,
                    desc,
                ),
            )
        )

        return self

    def execute(
        self,
    ) -> FakeResponse:
        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.response_data,
        )


class FakeRpcQuery:
    """Record one Supabase RPC execution."""

    def __init__(
        self,
        response_data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error
        self.executed = False

    def execute(
        self,
    ) -> FakeResponse:
        self.executed = True

        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.response_data,
        )


class FakeClient:
    """Minimal Supabase client for Flashcard persistence."""

    def __init__(
        self,
        *,
        deck_query: FakeQuery | None = None,
        card_query: FakeQuery | None = None,
        rpc_query: FakeRpcQuery | None = None,
    ) -> None:
        self.deck_query = deck_query
        self.card_query = card_query
        self.rpc_query = rpc_query

        self.table_names: list[
            str
        ] = []

        self.rpc_calls: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        self.table_names.append(
            table_name,
        )

        if table_name == "flashcard_decks":
            assert self.deck_query is not None
            return self.deck_query

        if table_name == "flashcards":
            assert self.card_query is not None
            return self.card_query

        raise AssertionError(
            f"Unexpected table: {table_name}"
        )

    def rpc(
        self,
        function_name: str,
        params: object,
    ) -> FakeRpcQuery:
        self.rpc_calls.append(
            (
                function_name,
                params,
            )
        )

        assert self.rpc_query is not None

        return self.rpc_query


def _source(
    study_file_id: UUID,
) -> FlashcardSource:
    return FlashcardSource(
        study_file_id=study_file_id,
        source_name="Lecture 1.pdf",
        chunk_index=0,
        locator_type=FlashcardLocatorType.PAGE,
        locator_label="Page 1",
    )


def _cards() -> tuple[
    FlashcardItem,
    ...,
]:
    return (
        FlashcardItem(
            question="What is photosynthesis?",
            answer=(
                "The process by which plants convert "
                "light energy into chemical energy."
            ),
        ),
        FlashcardItem(
            question="Where does photosynthesis occur?",
            answer="Primarily in chloroplasts.",
        ),
        FlashcardItem(
            question="What pigment absorbs light?",
            answer="Chlorophyll.",
        ),
        FlashcardItem(
            question="What gas do plants absorb?",
            answer="Carbon dioxide.",
        ),
        FlashcardItem(
            question="What gas is released?",
            answer="Oxygen.",
        ),
    )


def _deck_row(
    *,
    deck_id: UUID | None = None,
    subject_id: UUID | None = None,
    study_file_id: UUID | None = None,
    requested_card_count: int = 5,
) -> dict[
    str,
    object,
]:
    now = datetime.now(
        UTC,
    ).isoformat()

    return {
        "id": str(
            deck_id or uuid4(),
        ),
        "subject_id": str(
            subject_id or uuid4(),
        ),
        "study_file_id": (
            str(
                study_file_id,
            )
            if study_file_id is not None
            else None
        ),
        "scope_type": (
            "file"
            if study_file_id is not None
            else "subject"
        ),
        "title": "Biology Flashcards",
        "requested_card_count": requested_card_count,
        "sources": (
            [
                {
                    "study_file_id": str(
                        study_file_id,
                    ),
                    "source_name": "Lecture 1.pdf",
                    "chunk_index": 0,
                    "locator_type": "page",
                    "locator_label": "Page 1",
                }
            ]
            if study_file_id is not None
            else []
        ),
        "generation_model": "gemini-test-model",
        "generation_count": 1,
        "generated_at": now,
        "created_at": now,
        "updated_at": now,
    }


def _card_rows(
    *,
    deck_id: UUID,
) -> list[
    dict[
        str,
        object,
    ]
]:
    now = datetime.now(
        UTC,
    ).isoformat()

    return [
        {
            "id": str(
                uuid4(),
            ),
            "deck_id": str(
                deck_id,
            ),
            "position": 0,
            "question": "What is photosynthesis?",
            "answer": (
                "The process by which plants convert "
                "light energy into chemical energy."
            ),
            "created_at": now,
        },
        {
            "id": str(
                uuid4(),
            ),
            "deck_id": str(
                deck_id,
            ),
            "position": 1,
            "question": (
                "Where does photosynthesis occur?"
            ),
            "answer": "Primarily in chloroplasts.",
            "created_at": now,
        },
        {
            "id": str(
                uuid4(),
            ),
            "deck_id": str(
                deck_id,
            ),
            "position": 2,
            "question": (
                "What pigment absorbs light?"
            ),
            "answer": "Chlorophyll.",
            "created_at": now,
        },
        {
            "id": str(
                uuid4(),
            ),
            "deck_id": str(
                deck_id,
            ),
            "position": 3,
            "question": (
                "What gas do plants absorb?"
            ),
            "answer": "Carbon dioxide.",
            "created_at": now,
        },
        {
            "id": str(
                uuid4(),
            ),
            "deck_id": str(
                deck_id,
            ),
            "position": 4,
            "question": (
                "What gas is released?"
            ),
            "answer": "Oxygen.",
            "created_at": now,
        },
    ]

def test_create_deck_uses_atomic_rpc_and_returns_deck() -> None:
    """Creation must use the trusted atomic persistence RPC."""

    user_id = uuid4()
    subject_id = uuid4()
    study_file_id = uuid4()
    deck_id = uuid4()

    deck_query = FakeQuery(
        [
            _deck_row(
                deck_id=deck_id,
                subject_id=subject_id,
                study_file_id=study_file_id,
            )
        ],
    )

    card_query = FakeQuery(
        _card_rows(
            deck_id=deck_id,
        ),
    )

    rpc_query = FakeRpcQuery(
        str(
            deck_id,
        ),
    )

    client = FakeClient(
        deck_query=deck_query,
        card_query=card_query,
        rpc_query=rpc_query,
    )

    repository = FlashcardRepository(
        client,
    )

    result = repository.create_deck(
        user_id=user_id,
        subject_id=subject_id,
        study_file_id=study_file_id,
        scope_type=FlashcardScopeType.FILE,
        title=" Biology Flashcards ",
        requested_card_count=5,
        cards=_cards(),
        sources=(
            _source(
                study_file_id,
            ),
        ),
        generation_model=" gemini-test-model ",
    )

    assert result.id == deck_id
    assert result.subject_id == subject_id
    assert result.study_file_id == study_file_id

    assert len(
        result.cards,
    ) == 5

    assert client.rpc_calls

    function_name, params = client.rpc_calls[0]

    assert (
        function_name
        == "create_flashcard_deck_with_cards"
    )

    assert isinstance(
        params,
        dict,
    )

    assert params[
        "p_user_id"
    ] == str(
        user_id,
    )

    assert params[
        "p_subject_id"
    ] == str(
        subject_id,
    )

    assert params[
        "p_study_file_id"
    ] == str(
        study_file_id,
    )

    assert params[
        "p_scope_type"
    ] == "file"

    assert params[
        "p_title"
    ] == "Biology Flashcards"

    assert params[
        "p_requested_card_count"
    ] == 5

    assert params[
        "p_generation_model"
    ] == "gemini-test-model"

    assert len(
        params[
            "p_cards"
        ],
    ) == 5

    assert rpc_query.executed is True


def test_create_deck_rejects_empty_title() -> None:
    """Repository must reject an empty generated title."""

    repository = FlashcardRepository(
        FakeClient(),
    )

    with pytest.raises(
        FlashcardValidationError,
    ):
        repository.create_deck(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=FlashcardScopeType.SUBJECT,
            title="   ",
            requested_card_count=2,
            cards=_cards(),
            sources=(),
            generation_model="gemini-test-model",
        )


def test_create_deck_rejects_empty_generation_model() -> None:
    """Repository must reject an empty model identifier."""

    repository = FlashcardRepository(
        FakeClient(),
    )

    with pytest.raises(
        FlashcardValidationError,
    ):
        repository.create_deck(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=FlashcardScopeType.SUBJECT,
            title="Biology Flashcards",
            requested_card_count=2,
            cards=_cards(),
            sources=(),
            generation_model="   ",
        )


def test_create_deck_requires_generated_count_match() -> None:
    """Generated card count must match requested count."""

    repository = FlashcardRepository(
        FakeClient(),
    )

    with pytest.raises(
        FlashcardValidationError,
    ):
        repository.create_deck(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=FlashcardScopeType.SUBJECT,
            title="Biology Flashcards",
            requested_card_count=6,
            cards=_cards(),
            sources=(),
            generation_model="gemini-test-model",
        )


def test_get_deck_filters_owner_and_loads_ordered_cards() -> None:
    """Retrieval must remain owner scoped and preserve card order."""

    user_id = uuid4()
    subject_id = uuid4()
    deck_id = uuid4()

    deck_query = FakeQuery(
        [
            _deck_row(
                deck_id=deck_id,
                subject_id=subject_id,
            )
        ],
    )

    card_query = FakeQuery(
        _card_rows(
            deck_id=deck_id,
        ),
    )

    repository = FlashcardRepository(
        FakeClient(
            deck_query=deck_query,
            card_query=card_query,
        ),
    )

    result = repository.get_deck(
        user_id=user_id,
        deck_id=deck_id,
    )

    assert result is not None
    assert result.id == deck_id

    assert [
    card.question
    for card in result.cards
    ] == [
        "What is photosynthesis?",
        "Where does photosynthesis occur?",
        "What pigment absorbs light?",
        "What gas do plants absorb?",
        "What gas is released?",
    ]

    assert (
        "eq",
        (
            "id",
            str(
                deck_id,
            ),
        ),
    ) in deck_query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in deck_query.operations

    assert (
        "eq",
        (
            "deck_id",
            str(
                deck_id,
            ),
        ),
    ) in card_query.operations

    assert (
        "order",
        (
            "position",
            False,
        ),
    ) in card_query.operations


def test_get_missing_deck_returns_none() -> None:
    """Missing owned deck must not be fabricated."""

    deck_query = FakeQuery(
        [],
    )

    repository = FlashcardRepository(
        FakeClient(
            deck_query=deck_query,
        ),
    )

    result = repository.get_deck(
        user_id=uuid4(),
        deck_id=uuid4(),
    )

    assert result is None


def test_delete_deck_filters_owner() -> None:
    """Deletion must remain scoped to the authenticated owner."""

    user_id = uuid4()
    deck_id = uuid4()

    deck_query = FakeQuery(
        [
            {
                "id": str(
                    deck_id,
                )
            }
        ],
    )

    repository = FlashcardRepository(
        FakeClient(
            deck_query=deck_query,
        ),
    )

    deleted = repository.delete_deck(
        user_id=user_id,
        deck_id=deck_id,
    )

    assert deleted is True

    assert (
        "delete",
        None,
    ) in deck_query.operations

    assert (
        "eq",
        (
            "id",
            str(
                deck_id,
            ),
        ),
    ) in deck_query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in deck_query.operations


def test_delete_missing_deck_returns_false() -> None:
    """Deleting a missing owned deck must return false."""

    repository = FlashcardRepository(
        FakeClient(
            deck_query=FakeQuery(
                [],
            ),
        ),
    )

    result = repository.delete_deck(
        user_id=uuid4(),
        deck_id=uuid4(),
    )

    assert result is False


def test_database_failure_is_wrapped() -> None:
    """Raw Supabase failures must not escape the repository."""

    repository = FlashcardRepository(
        FakeClient(
            deck_query=FakeQuery(
                [],
                error=RuntimeError(
                    "database unavailable",
                ),
            ),
        ),
    )

    with pytest.raises(
        FlashcardPersistenceError,
    ):
        repository.get_deck(
            user_id=uuid4(),
            deck_id=uuid4(),
        )


def test_invalid_persisted_deck_raises_response_error() -> None:
    """Malformed persisted rows must fail controlled validation."""

    deck_id = uuid4()

    row = _deck_row(
        deck_id=deck_id,
    )

    row[
        "scope_type"
    ] = "invalid-scope"

    repository = FlashcardRepository(
        FakeClient(
            deck_query=FakeQuery(
                [
                    row,
                ],
            ),
            card_query=FakeQuery(
                _card_rows(
                    deck_id=deck_id,
                ),
            ),
        ),
    )

    with pytest.raises(
        FlashcardResponseError,
    ):
        repository.get_deck(
            user_id=uuid4(),
            deck_id=deck_id,
        )

def test_list_decks_filters_owner_and_orders_newest() -> None:
    """Saved deck listing must be owner scoped and newest first."""

    user_id = uuid4()
    first_deck_id = uuid4()
    second_deck_id = uuid4()

    deck_query = FakeQuery(
        [
            _deck_row(
                deck_id=first_deck_id,
            ),
            _deck_row(
                deck_id=second_deck_id,
            ),
        ],
    )

    repository = FlashcardRepository(
        FakeClient(
            deck_query=deck_query,
        ),
    )

    result = repository.list_decks(
        user_id=user_id,
    )

    assert len(
        result,
    ) == 2

    assert result[
        0
    ].id == first_deck_id

    assert result[
        1
    ].id == second_deck_id

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in deck_query.operations

    assert (
        "order",
        (
            "created_at",
            True,
        ),
    ) in deck_query.operations


def test_list_decks_can_filter_subject() -> None:
    """Saved decks may be narrowed to one owned subject."""

    user_id = uuid4()
    subject_id = uuid4()

    deck_query = FakeQuery(
        [
            _deck_row(
                subject_id=subject_id,
            )
        ],
    )

    repository = FlashcardRepository(
        FakeClient(
            deck_query=deck_query,
        ),
    )

    result = repository.list_decks(
        user_id=user_id,
        subject_id=subject_id,
    )

    assert len(
        result,
    ) == 1

    assert result[
        0
    ].subject_id == subject_id

    assert (
        "eq",
        (
            "subject_id",
            str(
                subject_id,
            ),
        ),
    ) in deck_query.operations