# File: /backend/app/services/study_material_embedder.py
# Purpose: Executes prepared embedding batches through the
# configured AI provider and validates returned vectors.

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Protocol

from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
)
from app.ai.preparation import (
    StudyMaterialPreparation,
)
from app.ai.providers.gemini import (
    GeminiProvider,
)
from app.core.config import Settings


class StudyMaterialEmbeddingError(
    RuntimeError,
):
    """Base error for study-material embedding execution."""


class StudyMaterialEmbeddingValidationError(
    StudyMaterialEmbeddingError,
):
    """Raised when prepared or returned embedding data is invalid."""


class EmbeddingProviderProtocol(
    Protocol,
):
    """Provider interface required by the embedding service."""

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Return embeddings for one prepared request."""

        ...


@dataclass(frozen=True)
class StudyMaterialEmbeddingResult:
    """Validated flattened embeddings for one study material."""

    embedding_model: str
    embedding_dimensions: int

    embeddings: tuple[
        tuple[float, ...],
        ...,
    ]

    batch_count: int

    @property
    def chunk_count(
        self,
    ) -> int:
        """Return the number of validated vectors."""

        return len(
            self.embeddings,
        )


class StudyMaterialEmbedder:
    """Executes and validates prepared embedding batches."""

    def __init__(
        self,
        settings: Settings,
        provider: EmbeddingProviderProtocol | None = None,
    ) -> None:
        self._embedding_model = settings.gemini_embedding_model

        self._embedding_dimensions = settings.gemini_embedding_dimensions

        self._provider = (
            provider
            if provider is not None
            else GeminiProvider(
                settings=settings,
            )
        )

    async def embed_preparation(
        self,
        preparation: StudyMaterialPreparation,
    ) -> StudyMaterialEmbeddingResult:
        """Execute all prepared requests in batch order."""

        batches = tuple(
            preparation.batches,
        )

        requests = tuple(
            preparation.embedding_requests,
        )

        if not batches:
            raise StudyMaterialEmbeddingValidationError(
                "At least one embedding batch is required.",
            )

        if len(batches) != len(requests):
            raise StudyMaterialEmbeddingValidationError(
                "Every embedding batch must have exactly one embedding request.",
            )

        validated_embeddings: list[tuple[float, ...]] = []

        for expected_batch_index, (
            batch,
            request,
        ) in enumerate(
            zip(
                batches,
                requests,
                strict=True,
            ),
        ):
            if batch.batch_index != expected_batch_index:
                raise StudyMaterialEmbeddingValidationError(
                    "Embedding batch indexes must be contiguous and begin at zero.",
                )

            expected_batch_size = len(
                batch.chunks,
            )

            if expected_batch_size < 1:
                raise StudyMaterialEmbeddingValidationError(
                    "Embedding batches cannot be empty.",
                )

            if (
                len(
                    request.texts,
                )
                != expected_batch_size
            ):
                raise StudyMaterialEmbeddingValidationError(
                    "The embedding request text count does not match its batch.",
                )

            provider_result = await self._provider.embed(
                request,
            )

            batch_embeddings = _get_result_embeddings(
                provider_result,
            )

            if (
                len(
                    batch_embeddings,
                )
                != expected_batch_size
            ):
                raise StudyMaterialEmbeddingValidationError(
                    "The provider returned an unexpected number of embeddings.",
                )

            for embedding in batch_embeddings:
                validated_embeddings.append(
                    _validate_embedding(
                        embedding=embedding,
                        expected_dimensions=(self._embedding_dimensions),
                    ),
                )

        expected_chunk_count = preparation.chunk_count

        if (
            len(
                validated_embeddings,
            )
            != expected_chunk_count
        ):
            raise StudyMaterialEmbeddingValidationError(
                "The final embedding count does not match the prepared chunk count.",
            )

        return StudyMaterialEmbeddingResult(
            embedding_model=(self._embedding_model),
            embedding_dimensions=(self._embedding_dimensions),
            embeddings=tuple(
                validated_embeddings,
            ),
            batch_count=len(
                batches,
            ),
        )


def _get_result_embeddings(
    result: EmbeddingResult,
) -> Sequence[Sequence[float]]:
    """Read embeddings from the provider-independent result."""

    embeddings = getattr(
        result,
        "embeddings",
        None,
    )

    if embeddings is None:
        embeddings = getattr(
            result,
            "vectors",
            None,
        )

    if isinstance(
        embeddings,
        (
            str,
            bytes,
            bytearray,
        ),
    ) or not isinstance(
        embeddings,
        Sequence,
    ):
        raise StudyMaterialEmbeddingValidationError(
            "The provider response does not contain a valid embedding sequence.",
        )

    return embeddings


def _validate_embedding(
    *,
    embedding: Sequence[float],
    expected_dimensions: int,
) -> tuple[float, ...]:
    """Validate one provider vector."""

    if isinstance(
        embedding,
        (
            str,
            bytes,
            bytearray,
        ),
    ) or not isinstance(
        embedding,
        Sequence,
    ):
        raise StudyMaterialEmbeddingValidationError(
            "Each embedding must be a numeric sequence.",
        )

    if len(embedding) != expected_dimensions:
        raise StudyMaterialEmbeddingValidationError(
            "A provider embedding has the wrong number of dimensions.",
        )

    normalized_values: list[float] = []

    for value in embedding:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            Real,
        ):
            raise StudyMaterialEmbeddingValidationError(
                "Provider embedding values must be real numbers.",
            )

        normalized_value = float(
            value,
        )

        if not isfinite(
            normalized_value,
        ):
            raise StudyMaterialEmbeddingValidationError(
                "Provider embedding values must be finite.",
            )

        normalized_values.append(
            normalized_value,
        )

    return tuple(
        normalized_values,
    )
