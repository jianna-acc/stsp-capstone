# File: /backend/tests/test_flashcard_schemas.py
# Purpose: Verifies Flashcard generation, content, source,
# scope, and persistence API contracts.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.flashcard import (
    MAX_FLASHCARDS_PER_DECK,
    FlashcardContent,
    FlashcardDeckResponse,
    FlashcardGenerateRequest,
    FlashcardItem,
    FlashcardLocatorType,
    FlashcardScopeType,
    FlashcardSource,
)


def test_file_scope_requires_study_file() -> None:
    """File-scoped flashcards must identify one study file."""

    with pytest.raises(
        ValidationError,
    ):
        FlashcardGenerateRequest(
            scope_type=FlashcardScopeType.FILE,
            subject_id=uuid4(),
            card_count=20,
        )


def test_subject_scope_rejects_study_file() -> None:
    """Subject-scoped flashcards must not identify one file."""

    with pytest.raises(
        ValidationError,
    ):
        FlashcardGenerateRequest(
            scope_type=FlashcardScopeType.SUBJECT,
            subject_id=uuid4(),
            study_file_id=uuid4(),
            card_count=20,
        )


def test_generate_request_defaults_to_twenty_cards() -> None:
    """Normal generation should request twenty cards by default."""

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.SUBJECT,
        subject_id=uuid4(),
    )

    assert request.card_count == 20


@pytest.mark.parametrize(
    "invalid_count",
    (
        0,
        4,
        MAX_FLASHCARDS_PER_DECK + 1,
    ),
)
def test_generate_request_rejects_invalid_card_count(
    invalid_count: int,
) -> None:
    """Requested deck size must stay within supported limits."""

    with pytest.raises(
        ValidationError,
    ):
        FlashcardGenerateRequest(
            scope_type=FlashcardScopeType.SUBJECT,
            subject_id=uuid4(),
            card_count=invalid_count,
        )


def test_flashcard_item_normalizes_text() -> None:
    """Question and answer text must be trimmed."""

    card = FlashcardItem(
        question="  What is leverage?  ",
        answer="  The use of debt to finance assets.  ",
    )

    assert card.question == "What is leverage?"
    assert (
        card.answer
        == "The use of debt to finance assets."
    )


@pytest.mark.parametrize(
    (
        "question",
        "answer",
    ),
    (
        (
            "",
            "Valid answer.",
        ),
        (
            "Valid question?",
            "",
        ),
        (
            "   ",
            "Valid answer.",
        ),
        (
            "Valid question?",
            "   ",
        ),
    ),
)
def test_flashcard_item_rejects_empty_text(
    question: str,
    answer: str,
) -> None:
    """Generated cards must have both sides populated."""

    with pytest.raises(
        ValidationError,
    ):
        FlashcardItem(
            question=question,
            answer=answer,
        )


def test_flashcard_content_requires_cards() -> None:
    """Generated flashcard content cannot be empty."""

    with pytest.raises(
        ValidationError,
    ):
        FlashcardContent(
            cards=(),
        )


def test_flashcard_content_accepts_valid_cards() -> None:
    """Generated content should preserve valid ordered cards."""

    first = FlashcardItem(
        question="What is liquidity?",
        answer="The ability to meet short-term obligations.",
    )

    second = FlashcardItem(
        question="What is solvency?",
        answer="The ability to meet long-term obligations.",
    )

    content = FlashcardContent(
        cards=(
            first,
            second,
        ),
    )

    assert content.cards == (
        first,
        second,
    )


def test_flashcard_source_normalizes_locator() -> None:
    """Saved flashcard sources should retain safe location data."""

    source = FlashcardSource(
        study_file_id=uuid4(),
        source_name="  Finance.pdf  ",
        chunk_index=3,
        locator_type=FlashcardLocatorType.PAGE,
        locator_label="  Page 4  ",
    )

    assert source.source_name == "Finance.pdf"
    assert source.locator_label == "Page 4"


def test_flashcard_deck_response_preserves_file_scope() -> None:
    """Saved file-scoped deck must remain internally consistent."""

    subject_id = uuid4()
    file_id = uuid4()

    now = datetime.now(
        UTC,
    )

    deck = FlashcardDeckResponse(
        id=uuid4(),
        subject_id=subject_id,
        study_file_id=file_id,
        scope_type=FlashcardScopeType.FILE,
        title="Finance Flashcards",
        requested_card_count=20,
        cards=(
            FlashcardItem(
                question="What is leverage?",
                answer="The use of borrowed funds.",
            ),
        ),
        sources=(),
        generation_model="fake-model",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )

    assert deck.study_file_id == file_id
    assert deck.scope_type == FlashcardScopeType.FILE


def test_subject_deck_rejects_study_file() -> None:
    """Saved subject-scoped deck cannot retain one study-file ID."""

    now = datetime.now(
        UTC,
    )

    with pytest.raises(
        ValidationError,
    ):
        FlashcardDeckResponse(
            id=uuid4(),
            subject_id=uuid4(),
            study_file_id=uuid4(),
            scope_type=FlashcardScopeType.SUBJECT,
            title="Subject Flashcards",
            requested_card_count=20,
            cards=(
                FlashcardItem(
                    question="Question?",
                    answer="Answer.",
                ),
            ),
            sources=(),
            generation_model="fake-model",
            generation_count=1,
            generated_at=now,
            created_at=now,
            updated_at=now,
        )