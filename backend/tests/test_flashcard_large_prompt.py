# File: /backend/tests/test_flashcard_large_prompt.py
# Purpose: Tests partial-batch and final-synthesis prompts used
# for large-material Flashcard generation.

from uuid import UUID

from app.ai.flashcard_prompt import (
    FlashcardPromptBuilder,
)
from app.schemas.flashcard import (
    FlashcardContent,
    FlashcardGenerateRequest,
    FlashcardItem,
    FlashcardScopeType,
)
from app.services.flashcard_batching import (
    FlashcardSourceBatch,
)
from app.services.flashcard_source_loader import (
    FlashcardSourceBundle,
    FlashcardSourceChunk,
)

USER_ID = UUID(
    "11111111-1111-1111-1111-111111111111",
)

SUBJECT_ID = UUID(
    "22222222-2222-2222-2222-222222222222",
)

FILE_ID = UUID(
    "33333333-3333-3333-3333-333333333333",
)


def make_request() -> FlashcardGenerateRequest:
    """Create one deterministic Flashcard generation request."""

    return FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.FILE,
        subject_id=SUBJECT_ID,
        study_file_id=FILE_ID,
        card_count=5,
    )


def make_chunks() -> tuple[
    FlashcardSourceChunk,
    ...,
]:
    """Create ordered source chunks for large-material tests."""

    return (
        FlashcardSourceChunk(
            study_file_id=FILE_ID,
            source_name="Biology Notes.pdf",
            chunk_index=0,
            content="CELL_BATCH_ONLY_CONTENT",
        ),
        FlashcardSourceChunk(
            study_file_id=FILE_ID,
            source_name="Biology Notes.pdf",
            chunk_index=1,
            content="GENETICS_BATCH_ONLY_CONTENT",
        ),
    )


def make_bundle() -> FlashcardSourceBundle:
    """Create the complete Flashcard source bundle."""

    return FlashcardSourceBundle(
        user_id=USER_ID,
        subject_id=SUBJECT_ID,
        scope_type=FlashcardScopeType.FILE,
        study_file_id=FILE_ID,
        chunks=make_chunks(),
    )


def test_batch_prompt_contains_only_selected_batch_chunks() -> None:
    """A partial prompt must not include unseen source batches."""

    request = make_request()
    bundle = make_bundle()

    source_batch = FlashcardSourceBatch(
        batch_index=0,
        chunks=(
            bundle.chunks[
                0
            ],
        ),
        source_character_count=len(
            bundle.chunks[
                0
            ].content,
        ),
    )

    prompt = (
        FlashcardPromptBuilder()
        .build_batch(
            request=request,
            source_bundle=bundle,
            source_batch=source_batch,
            total_batch_count=2,
        )
    )

    assert (
        "FLASHCARD_PARTIAL_BATCH"
        in prompt.user_prompt
    )

    assert (
        "Batch 1 of 2"
        in prompt.user_prompt
    )

    assert (
        "CELL_BATCH_ONLY_CONTENT"
        in prompt.user_prompt
    )

    assert (
        "GENETICS_BATCH_ONLY_CONTENT"
        not in prompt.user_prompt
    )

    assert (
        "exactly 5 candidate flashcards"
        in prompt.user_prompt.lower()
    )

    assert (
        prompt.source_character_count
        == len(
            bundle.chunks[
                0
            ].content,
        )
    )

    assert (
        prompt.source_chunk_count
        == 1
    )

    assert (
        prompt.source_file_count
        == 1
    )


def test_batch_prompt_identifies_later_batch_order() -> None:
    """Partial prompts must preserve deterministic batch ordering."""

    request = make_request()
    bundle = make_bundle()

    source_batch = FlashcardSourceBatch(
        batch_index=1,
        chunks=(
            bundle.chunks[
                1
            ],
        ),
        source_character_count=len(
            bundle.chunks[
                1
            ].content,
        ),
    )

    prompt = (
        FlashcardPromptBuilder()
        .build_batch(
            request=request,
            source_bundle=bundle,
            source_batch=source_batch,
            total_batch_count=2,
        )
    )

    assert (
        "Batch 2 of 2"
        in prompt.user_prompt
    )

    assert (
        "GENETICS_BATCH_ONLY_CONTENT"
        in prompt.user_prompt
    )

    assert (
        "CELL_BATCH_ONLY_CONTENT"
        not in prompt.user_prompt
    )


def test_synthesis_prompt_contains_ordered_partial_decks() -> None:
    """Final synthesis must receive every validated partial deck."""

    request = make_request()
    bundle = make_bundle()

    partials = (
        FlashcardContent(
            cards=(
                FlashcardItem(
                    question="Partial question A?",
                    answer="Partial answer A.",
                ),
            ),
        ),
        FlashcardContent(
            cards=(
                FlashcardItem(
                    question="Partial question B?",
                    answer="Partial answer B.",
                ),
            ),
        ),
    )

    prompt = (
        FlashcardPromptBuilder()
        .build_synthesis(
            request=request,
            source_bundle=bundle,
            partial_contents=partials,
        )
    )

    assert (
        "FLASHCARD_FINAL_SYNTHESIS"
        in prompt.user_prompt
    )

    assert (
        "exactly 5 flashcards"
        in prompt.user_prompt.lower()
    )

    first_position = (
        prompt.user_prompt.index(
            "Partial question A?",
        )
    )

    second_position = (
        prompt.user_prompt.index(
            "Partial question B?",
        )
    )

    assert (
        first_position
        < second_position
    )

    assert (
        "remove duplicate"
        in prompt.user_prompt.lower()
    )

    assert (
        "outside knowledge"
        in prompt.user_prompt.lower()
    )


def test_synthesis_prompt_reports_complete_source_metadata() -> None:
    """Final result metadata must describe the original source bundle."""

    request = make_request()
    bundle = make_bundle()

    partials = (
        FlashcardContent(
            cards=(
                FlashcardItem(
                    question="Question?",
                    answer="Answer.",
                ),
            ),
        ),
    )

    prompt = (
        FlashcardPromptBuilder()
        .build_synthesis(
            request=request,
            source_bundle=bundle,
            partial_contents=partials,
        )
    )

    assert (
        prompt.source_character_count
        == bundle.character_count
    )

    assert (
        prompt.source_chunk_count
        == bundle.chunk_count
    )

    assert (
        prompt.source_file_count
        == bundle.file_count
    )


def test_synthesis_prompt_does_not_repeat_raw_source_content() -> None:
    """Synthesis should use validated candidates, not resend raw material."""

    request = make_request()
    bundle = make_bundle()

    partials = (
        FlashcardContent(
            cards=(
                FlashcardItem(
                    question="Candidate question?",
                    answer="Candidate answer.",
                ),
            ),
        ),
    )

    prompt = (
        FlashcardPromptBuilder()
        .build_synthesis(
            request=request,
            source_bundle=bundle,
            partial_contents=partials,
        )
    )

    assert (
        "Candidate question?"
        in prompt.user_prompt
    )

    assert (
        "CELL_BATCH_ONLY_CONTENT"
        not in prompt.user_prompt
    )

    assert (
        "GENETICS_BATCH_ONLY_CONTENT"
        not in prompt.user_prompt
    )