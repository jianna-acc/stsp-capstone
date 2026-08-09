# File: /backend/tests/test_reviewer_batching.py
# Purpose: Verifies deterministic batching of large reviewer
# source bundles without dropping or reordering source chunks.

from __future__ import annotations

from uuid import uuid4

import pytest

from app.schemas.reviewer import (
    ReviewerScopeType,
)
from app.services.reviewer_batching import (
    ReviewerSourceBatcher,
)
from app.services.reviewer_errors import (
    ReviewerValidationError,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
    ReviewerSourceChunk,
)


def _bundle(
    *content_lengths: int,
) -> ReviewerSourceBundle:
    """Build one file-scoped source bundle for batching tests."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    chunks = tuple(
        ReviewerSourceChunk(
            study_file_id=file_id,
            source_name="Large Lecture.pdf",
            chunk_index=index,
            content="A" * content_length,
        )
        for index, content_length in enumerate(
            content_lengths,
        )
    )

    return ReviewerSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.FILE,
        study_file_id=file_id,
        chunks=chunks,
    )


def test_small_bundle_stays_in_one_batch() -> None:
    """A bundle within the limit must not be split unnecessarily."""

    bundle = _bundle(
        200,
        300,
        400,
    )

    batcher = ReviewerSourceBatcher(
        max_source_characters=1_000,
    )

    batches = batcher.partition(
        bundle,
    )

    assert len(
        batches,
    ) == 1

    assert batches[
        0
    ].chunks == bundle.chunks

    assert (
        batches[
            0
        ].source_character_count
        == 900
    )


def test_large_bundle_is_split_at_chunk_boundaries() -> None:
    """Large material must be divided without splitting source chunks."""

    bundle = _bundle(
        400,
        400,
        400,
        400,
        400,
    )

    batcher = ReviewerSourceBatcher(
        max_source_characters=1_000,
    )

    batches = batcher.partition(
        bundle,
    )

    assert len(
        batches,
    ) == 3

    assert [
        batch.source_character_count
        for batch in batches
    ] == [
        800,
        800,
        400,
    ]


def test_batching_preserves_every_chunk_in_order() -> None:
    """Every original chunk must appear exactly once and in order."""

    bundle = _bundle(
        600,
        600,
        600,
    )

    batcher = ReviewerSourceBatcher(
        max_source_characters=1_000,
    )

    batches = batcher.partition(
        bundle,
    )

    flattened_chunks = tuple(
        chunk
        for batch in batches
        for chunk in batch.chunks
    )

    assert flattened_chunks == bundle.chunks


def test_each_batch_stays_within_character_limit() -> None:
    """No generated source batch may exceed the configured limit."""

    bundle = _bundle(
        250,
        250,
        250,
        250,
        250,
        250,
    )

    maximum = 1_000

    batcher = ReviewerSourceBatcher(
        max_source_characters=maximum,
    )

    batches = batcher.partition(
        bundle,
    )

    assert all(
        batch.source_character_count
        <= maximum
        for batch in batches
    )


def test_batch_indices_are_contiguous() -> None:
    """Source batches must receive stable zero-based indices."""

    bundle = _bundle(
        600,
        600,
        600,
    )

    batcher = ReviewerSourceBatcher(
        max_source_characters=1_000,
    )

    batches = batcher.partition(
        bundle,
    )

    assert [
        batch.batch_index
        for batch in batches
    ] == [
        0,
        1,
        2,
    ]


def test_single_chunk_larger_than_batch_limit_is_rejected() -> None:
    """One oversized source chunk must fail instead of being truncated."""

    bundle = _bundle(
        1_001,
    )

    batcher = ReviewerSourceBatcher(
        max_source_characters=1_000,
    )

    with pytest.raises(
        ReviewerValidationError,
        match="source chunk exceeds",
    ):
        batcher.partition(
            bundle,
        )


@pytest.mark.parametrize(
    "invalid_limit",
    (
        True,
        999,
        80_001,
    ),
)
def test_invalid_batch_character_limit_is_rejected(
    invalid_limit: object,
) -> None:
    """Unsafe batching limits must be rejected during configuration."""

    with pytest.raises(
        ReviewerValidationError,
    ):
        ReviewerSourceBatcher(
            max_source_characters=invalid_limit,
        )