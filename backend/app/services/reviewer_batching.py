# File: /backend/app/services/reviewer_batching.py
# Purpose: Splits large reviewer source bundles into safe,
# ordered generation batches without dropping source chunks.

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.services.reviewer_errors import (
    ReviewerValidationError,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
    ReviewerSourceChunk,
)

DEFAULT_REVIEWER_BATCH_SOURCE_CHARACTERS: Final = 60_000

MIN_REVIEWER_BATCH_SOURCE_CHARACTERS: Final = 1_000
MAX_REVIEWER_BATCH_SOURCE_CHARACTERS: Final = 80_000


@dataclass(
    frozen=True,
    slots=True,
)
class ReviewerSourceBatch:
    """One ordered subset of reviewer source chunks."""

    batch_index: int
    chunks: tuple[
        ReviewerSourceChunk,
        ...,
    ]
    source_character_count: int

    def __post_init__(
        self,
    ) -> None:
        """Validate one generated reviewer source batch."""

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
            raise ReviewerValidationError(
                "Reviewer source batch index is invalid.",
            )

        if not self.chunks:
            raise ReviewerValidationError(
                "Reviewer source batch must contain source chunks.",
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
            raise ReviewerValidationError(
                "Reviewer source batch character count "
                "does not match its chunks.",
            )

        if self.source_character_count < 1:
            raise ReviewerValidationError(
                "Reviewer source batch content is empty.",
            )


class ReviewerSourceBatcher:
    """Partition complete reviewer material into bounded batches."""

    def __init__(
        self,
        *,
        max_source_characters: int = (
            DEFAULT_REVIEWER_BATCH_SOURCE_CHARACTERS
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
                MIN_REVIEWER_BATCH_SOURCE_CHARACTERS
                <= max_source_characters
                <= MAX_REVIEWER_BATCH_SOURCE_CHARACTERS
            )
        ):
            raise ReviewerValidationError(
                "Reviewer batch source-character limit must "
                f"be between "
                f"{MIN_REVIEWER_BATCH_SOURCE_CHARACTERS} and "
                f"{MAX_REVIEWER_BATCH_SOURCE_CHARACTERS}.",
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
        source_bundle: ReviewerSourceBundle,
    ) -> tuple[
        ReviewerSourceBatch,
        ...,
    ]:
        """Split one complete source bundle at chunk boundaries."""

        if not isinstance(
            source_bundle,
            ReviewerSourceBundle,
        ):
            raise ReviewerValidationError(
                "source_bundle must be a ReviewerSourceBundle.",
            )

        batches: list[
            ReviewerSourceBatch
        ] = []

        current_chunks: list[
            ReviewerSourceChunk
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
                raise ReviewerValidationError(
                    "A reviewer source chunk exceeds the "
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
                    ReviewerSourceBatch(
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
                ReviewerSourceBatch(
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
            raise ReviewerValidationError(
                "Reviewer source batching produced no batches.",
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
        source_bundle: ReviewerSourceBundle,
        batches: list[
            ReviewerSourceBatch
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
            raise ReviewerValidationError(
                "Reviewer source batching changed or dropped "
                "source chunks.",
            )

        if any(
            batch.source_character_count
            > self._max_source_characters
            for batch in batches
        ):
            raise ReviewerValidationError(
                "Reviewer source batching exceeded the "
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
            raise ReviewerValidationError(
                "Reviewer source batch ordering is invalid.",
            )