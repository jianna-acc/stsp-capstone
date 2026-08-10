# File: /backend/app/services/flashcard_batching.py
# Purpose: Splits large Flashcard source bundles into safe,
# ordered generation batches without dropping source chunks.

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.services.flashcard_source_loader import (
    FlashcardSourceBundle,
    FlashcardSourceChunk,
)

DEFAULT_FLASHCARD_BATCH_SOURCE_CHARACTERS: Final = 60_000

MIN_FLASHCARD_BATCH_SOURCE_CHARACTERS: Final = 1_000
MAX_FLASHCARD_BATCH_SOURCE_CHARACTERS: Final = 80_000


class FlashcardBatchingError(
    ValueError,
):
    """Raised when Flashcard source batching is invalid."""


@dataclass(
    frozen=True,
    slots=True,
)
class FlashcardSourceBatch:
    """One ordered subset of Flashcard source chunks."""

    batch_index: int

    chunks: tuple[
        FlashcardSourceChunk,
        ...,
    ]

    source_character_count: int

    def __post_init__(
        self,
    ) -> None:
        """Validate one generated Flashcard source batch."""

        if (
            isinstance(
                self.batch_index,
                bool,
            )
            or not isinstance(
                self.batch_index,
                int,
            )
            or self.batch_index < 0
        ):
            raise FlashcardBatchingError(
                "Flashcard source batch index is invalid.",
            )

        if not self.chunks:
            raise FlashcardBatchingError(
                "Flashcard source batch must contain source chunks.",
            )

        calculated_character_count = sum(
            len(
                chunk.content,
            )
            for chunk in self.chunks
        )

        if (
            self.source_character_count
            != calculated_character_count
        ):
            raise FlashcardBatchingError(
                "Flashcard source batch character count "
                "does not match its chunks.",
            )

        if self.source_character_count < 1:
            raise FlashcardBatchingError(
                "Flashcard source batch content is empty.",
            )


class FlashcardSourceBatcher:
    """Partition complete Flashcard material into bounded batches."""

    def __init__(
        self,
        *,
        max_source_characters: int = (
            DEFAULT_FLASHCARD_BATCH_SOURCE_CHARACTERS
        ),
    ) -> None:
        if (
            isinstance(
                max_source_characters,
                bool,
            )
            or not isinstance(
                max_source_characters,
                int,
            )
            or not (
                MIN_FLASHCARD_BATCH_SOURCE_CHARACTERS
                <= max_source_characters
                <= MAX_FLASHCARD_BATCH_SOURCE_CHARACTERS
            )
        ):
            raise FlashcardBatchingError(
                "Flashcard batch source-character limit must "
                f"be between "
                f"{MIN_FLASHCARD_BATCH_SOURCE_CHARACTERS} and "
                f"{MAX_FLASHCARD_BATCH_SOURCE_CHARACTERS}.",
            )

        self._max_source_characters = (
            max_source_characters
        )

    @property
    def max_source_characters(
        self,
    ) -> int:
        """Return the configured maximum batch source size."""

        return self._max_source_characters

    def partition(
        self,
        source_bundle: FlashcardSourceBundle,
    ) -> tuple[
        FlashcardSourceBatch,
        ...,
    ]:
        """Split one complete source bundle at chunk boundaries."""

        if not isinstance(
            source_bundle,
            FlashcardSourceBundle,
        ):
            raise FlashcardBatchingError(
                "source_bundle must be a FlashcardSourceBundle.",
            )

        batches: list[
            FlashcardSourceBatch
        ] = []

        current_chunks: list[
            FlashcardSourceChunk
        ] = []

        current_character_count = 0

        for chunk in source_bundle.chunks:
            chunk_character_count = len(
                chunk.content,
            )

            if (
                chunk_character_count
                > self._max_source_characters
            ):
                raise FlashcardBatchingError(
                    "A Flashcard source chunk exceeds the "
                    "configured batch character limit.",
                )

            would_exceed_limit = (
                current_chunks
                and (
                    current_character_count
                    + chunk_character_count
                    > self._max_source_characters
                )
            )

            if would_exceed_limit:
                batches.append(
                    FlashcardSourceBatch(
                        batch_index=len(
                            batches,
                        ),
                        chunks=tuple(
                            current_chunks,
                        ),
                        source_character_count=(
                            current_character_count
                        ),
                    )
                )

                current_chunks = []
                current_character_count = 0

            current_chunks.append(
                chunk,
            )

            current_character_count += (
                chunk_character_count
            )

        if current_chunks:
            batches.append(
                FlashcardSourceBatch(
                    batch_index=len(
                        batches,
                    ),
                    chunks=tuple(
                        current_chunks,
                    ),
                    source_character_count=(
                        current_character_count
                    ),
                )
            )

        if not batches:
            raise FlashcardBatchingError(
                "Flashcard source batching produced no batches.",
            )

        self._validate_partition(
            source_bundle=source_bundle,
            batches=batches,
        )

        return tuple(
            batches,
        )

    def _validate_partition(
        self,
        *,
        source_bundle: FlashcardSourceBundle,
        batches: list[
            FlashcardSourceBatch
        ],
    ) -> None:
        """Ensure batching preserved every source chunk exactly once."""

        flattened_chunks = tuple(
            chunk
            for batch in batches
            for chunk in batch.chunks
        )

        if (
            flattened_chunks
            != source_bundle.chunks
        ):
            raise FlashcardBatchingError(
                "Flashcard source batching changed or dropped "
                "source chunks.",
            )

        if any(
            batch.source_character_count
            > self._max_source_characters
            for batch in batches
        ):
            raise FlashcardBatchingError(
                "Flashcard source batching exceeded the "
                "configured character limit.",
            )

        expected_indices = list(
            range(
                len(
                    batches,
                )
            )
        )

        actual_indices = [
            batch.batch_index
            for batch in batches
        ]

        if actual_indices != expected_indices:
            raise FlashcardBatchingError(
                "Flashcard source batch ordering is invalid.",
            )