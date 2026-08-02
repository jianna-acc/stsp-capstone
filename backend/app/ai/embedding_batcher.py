# File: /backend/app/ai/embedding_batcher.py
# Purpose: Converts deterministic study-material chunks into
# controlled embedding batches and provider-independent requests.

from app.ai.chunking import (
    ChunkingResult,
    EmbeddingBatch,
)
from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingTaskType,
)
from app.core.config import Settings, get_settings


class EmbeddingBatchPreparer:
    """Prepare ordered document chunks for embedding operations."""

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """Create a preparer using validated batch-size settings."""

        self._settings = settings or get_settings()

    def prepare(
        self,
        result: ChunkingResult,
    ) -> tuple[EmbeddingBatch, ...]:
        """Divide one chunking result into deterministic batches."""

        batch_size = self._settings.ai_embedding_batch_size
        batches: list[EmbeddingBatch] = []

        for start_index in range(
            0,
            len(result.chunks),
            batch_size,
        ):
            batch_chunks = result.chunks[
                start_index:start_index + batch_size
            ]

            batches.append(
                EmbeddingBatch(
                    batch_index=len(batches),
                    chunks=batch_chunks,
                ),
            )

        prepared_batches = tuple(batches)

        self._validate_prepared_batches(
            result=result,
            batches=prepared_batches,
        )

        return prepared_batches

    @staticmethod
    def build_request(
        batch: EmbeddingBatch,
    ) -> EmbeddingRequest:
        """Create one document-embedding request from a batch."""

        return EmbeddingRequest(
            texts=batch.texts,
            task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT,
        )

    def prepare_requests(
        self,
        result: ChunkingResult,
    ) -> tuple[EmbeddingRequest, ...]:
        """Prepare ordered embedding requests for all result batches."""

        return tuple(
            self.build_request(batch)
            for batch in self.prepare(result)
        )

    def _validate_prepared_batches(
        self,
        *,
        result: ChunkingResult,
        batches: tuple[EmbeddingBatch, ...],
    ) -> None:
        """Verify that batching preserved every chunk exactly once."""

        if not batches:
            raise RuntimeError(
                "Embedding preparation produced no batches.",
            )

        expected_batch_indices = tuple(
            range(len(batches)),
        )
        actual_batch_indices = tuple(
            batch.batch_index
            for batch in batches
        )

        if actual_batch_indices != expected_batch_indices:
            raise RuntimeError(
                "Embedding batch indices must be contiguous and "
                "start at zero.",
            )

        if any(
            len(batch.chunks)
            > self._settings.ai_embedding_batch_size
            for batch in batches
        ):
            raise RuntimeError(
                "An embedding batch exceeded the configured "
                "batch size.",
            )

        flattened_chunks = tuple(
            chunk
            for batch in batches
            for chunk in batch.chunks
        )

        if flattened_chunks != result.chunks:
            raise RuntimeError(
                "Embedding preparation did not preserve chunk order.",
            )