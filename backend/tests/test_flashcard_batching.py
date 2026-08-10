# File: /backend/tests/test_flashcard_batching.py
# Purpose: Tests bounded Flashcard source batching without
# dropping, duplicating, reordering, or truncating chunks.

from uuid import UUID

import pytest
from app.services.flashcard_batching import (
    MAX_FLASHCARD_BATCH_SOURCE_CHARACTERS,
    MIN_FLASHCARD_BATCH_SOURCE_CHARACTERS,
    FlashcardBatchingError,
    FlashcardSourceBatcher,
)

from app.schemas.flashcard import (
    FlashcardScopeType,
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


def make_chunk(
    *,
    chunk_index: int,
    character_count: int,
) -> FlashcardSourceChunk:
    """Create one deterministic Flashcard source chunk."""

    return FlashcardSourceChunk(
        study_file_id=FILE_ID,
        source_name="Biology Notes.pdf",
        chunk_index=chunk_index,
        content=(
            chr(
                ord("A")
                + chunk_index
            )
            * character_count
        ),
    )


def make_bundle(
    *chunks: FlashcardSourceChunk,
) -> FlashcardSourceBundle:
    """Create one file-scoped Flashcard source bundle."""

    return FlashcardSourceBundle(
        user_id=USER_ID,
        subject_id=SUBJECT_ID,
        scope_type=FlashcardScopeType.FILE,
        study_file_id=FILE_ID,
        chunks=tuple(
            chunks,
        ),
    )


def test_uses_bounded_default_batch_size() -> None:
    batcher = (
        FlashcardSourceBatcher()
    )

    assert (
        MIN_FLASHCARD_BATCH_SOURCE_CHARACTERS
        <= batcher.max_source_characters
        <= MAX_FLASHCARD_BATCH_SOURCE_CHARACTERS
    )


def test_keeps_small_bundle_in_one_batch() -> None:
    bundle = make_bundle(
        make_chunk(
            chunk_index=0,
            character_count=400,
        ),
        make_chunk(
            chunk_index=1,
            character_count=500,
        ),
    )

    batcher = (
        FlashcardSourceBatcher(
            max_source_characters=1_000,
        )
    )

    batches = batcher.partition(
        bundle,
    )

    assert len(
        batches,
    ) == 1

    assert batches[
        0
    ].batch_index == 0

    assert (
        batches[
            0
        ].chunks
        == bundle.chunks
    )

    assert (
        batches[
            0
        ].source_character_count
        == 900
    )


def test_splits_only_at_chunk_boundaries() -> None:
    chunks = (
        make_chunk(
            chunk_index=0,
            character_count=600,
        ),
        make_chunk(
            chunk_index=1,
            character_count=300,
        ),
        make_chunk(
            chunk_index=2,
            character_count=700,
        ),
        make_chunk(
            chunk_index=3,
            character_count=200,
        ),
    )

    bundle = make_bundle(
        *chunks,
    )

    batcher = (
        FlashcardSourceBatcher(
            max_source_characters=1_000,
        )
    )

    batches = batcher.partition(
        bundle,
    )

    assert len(
        batches,
    ) == 2

    assert (
        batches[
            0
        ].chunks
        == chunks[
            0:2
        ]
    )

    assert (
        batches[
            1
        ].chunks
        == chunks[
            2:4
        ]
    )

    assert (
        batches[
            0
        ].source_character_count
        == 900
    )

    assert (
        batches[
            1
        ].source_character_count
        == 900
    )


def test_preserves_every_chunk_exactly_once_and_in_order() -> None:
    chunks = tuple(
        make_chunk(
            chunk_index=index,
            character_count=600,
        )
        for index in range(
            4,
        )
    )

    bundle = make_bundle(
        *chunks,
    )

    batcher = (
        FlashcardSourceBatcher(
            max_source_characters=1_000,
        )
    )

    batches = batcher.partition(
        bundle,
    )

    flattened_chunks = tuple(
        chunk
        for batch in batches
        for chunk in batch.chunks
    )

    assert (
        flattened_chunks
        == bundle.chunks
    )

    assert [
        batch.batch_index
        for batch in batches
    ] == [
        0,
        1,
        2,
        3,
    ]

    assert all(
        batch.source_character_count
        <= 1_000
        for batch in batches
    )


def test_rejects_one_chunk_larger_than_batch_limit() -> None:
    bundle = make_bundle(
        make_chunk(
            chunk_index=0,
            character_count=1_001,
        ),
    )

    batcher = (
        FlashcardSourceBatcher(
            max_source_characters=1_000,
        )
    )

    with pytest.raises(
        FlashcardBatchingError,
        match=(
            "source chunk exceeds"
        ),
    ):
        batcher.partition(
            bundle,
        )


@pytest.mark.parametrize(
    "max_source_characters",
    [
        True,
        999,
        80_001,
    ],
)
def test_rejects_invalid_batch_limits(
    max_source_characters: object,
) -> None:
    with pytest.raises(
        FlashcardBatchingError,
        match=(
            "batch source-character limit"
        ),
    ):
        FlashcardSourceBatcher(
            max_source_characters=(
                max_source_characters
            ),
        )