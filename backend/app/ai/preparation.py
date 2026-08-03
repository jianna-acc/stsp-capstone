# File: /backend/app/ai/preparation.py
# Purpose: Defines the complete offline preparation result produced
# from chunking study-material text and creating embedding requests.

from dataclasses import dataclass

from app.ai.chunking import (
    ChunkingResult,
    EmbeddingBatch,
)
from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingTaskType,
)


@dataclass(frozen=True, slots=True)
class StudyMaterialPreparation:
    """Complete offline preparation output for one study material."""

    chunking_result: ChunkingResult
    batches: tuple[EmbeddingBatch, ...]
    embedding_requests: tuple[EmbeddingRequest, ...]

    def __post_init__(self) -> None:
        """Validate chunk, batch, and request alignment."""

        if not self.batches:
            raise ValueError(
                "Study-material preparation must contain at least "
                "one embedding batch.",
            )

        if not self.embedding_requests:
            raise ValueError(
                "Study-material preparation must contain at least "
                "one embedding request.",
            )

        if len(self.batches) != len(self.embedding_requests):
            raise ValueError(
                "Embedding batch and request counts must match.",
            )

        flattened_chunks = tuple(
            chunk
            for batch in self.batches
            for chunk in batch.chunks
        )

        if flattened_chunks != self.chunking_result.chunks:
            raise ValueError(
                "Prepared batches must preserve every chunk in order.",
            )

        for batch, request in zip(
            self.batches,
            self.embedding_requests,
            strict=True,
        ):
            if request.texts != batch.texts:
                raise ValueError(
                    "Embedding request texts must match their batch.",
                )

            if (
                request.task_type
                is not EmbeddingTaskType.RETRIEVAL_DOCUMENT
            ):
                raise ValueError(
                    "Study-material embedding requests must use the "
                    "retrieval-document task type.",
                )

    @property
    def material_id(self) -> str:
        """Return the prepared study-material identifier."""

        return self.chunking_result.material_id

    @property
    def chunk_count(self) -> int:
        """Return the total number of prepared chunks."""

        return len(self.chunking_result.chunks)

    @property
    def batch_count(self) -> int:
        """Return the total number of embedding batches."""

        return len(self.batches)