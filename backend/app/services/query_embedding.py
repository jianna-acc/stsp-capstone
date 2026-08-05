# File: /backend/app/services/query_embedding.py
# Purpose: Converts one validated student question into a
# retrieval-query embedding for study-material similarity search.

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from inspect import isawaitable
from math import isfinite
from numbers import Real
from typing import Protocol

from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
)
from app.ai.errors import AIProviderError
from app.ai.providers.gemini import GeminiProvider
from app.core.config import Settings


class QueryEmbeddingFailureCode(StrEnum):
    """Stable failure codes used by future RAG API responses."""

    QUERY_VALIDATION_FAILED = (
        "QUERY_VALIDATION_FAILED"
    )

    QUERY_EMBEDDING_FAILED = (
        "QUERY_EMBEDDING_FAILED"
    )


class QueryEmbeddingError(
    RuntimeError,
):
    """Base error for student-query embedding operations."""

    def __init__(
        self,
        message: str,
        *,
        error_code: QueryEmbeddingFailureCode,
    ) -> None:
        """Create an error with a stable application failure code."""

        super().__init__(
            message,
        )

        self.error_code = error_code


class QueryEmbeddingValidationError(
    QueryEmbeddingError,
):
    """Raised when a query or returned vector is invalid."""

    def __init__(
        self,
        message: str,
    ) -> None:
        """Create a query-validation failure."""

        super().__init__(
            message,
            error_code=(
                QueryEmbeddingFailureCode
                .QUERY_VALIDATION_FAILED
            ),
        )


class QueryEmbeddingProviderError(
    QueryEmbeddingError,
):
    """Raised when the configured embedding provider fails."""

    def __init__(
        self,
        message: str,
    ) -> None:
        """Create a controlled query-embedding failure."""

        super().__init__(
            message,
            error_code=(
                QueryEmbeddingFailureCode
                .QUERY_EMBEDDING_FAILED
            ),
        )


class QueryEmbeddingProviderProtocol(
    Protocol,
):
    """Provider behavior required by the query service."""

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Return embeddings for one validated request."""

        ...


@dataclass(
    frozen=True,
    slots=True,
)
class QueryEmbeddingResult:
    """One validated embedding for a normalized student question."""

    question: str
    embedding: tuple[float, ...]
    provider: str
    embedding_model: str
    embedding_dimensions: int
    task_type: EmbeddingTaskType


class QueryEmbeddingService:
    """Generate and validate one retrieval-query embedding."""

    def __init__(
        self,
        settings: Settings,
        provider: QueryEmbeddingProviderProtocol | None = None,
    ) -> None:
        """Create the service with controlled embedding settings."""

        self._embedding_model = (
            settings.gemini_embedding_model
        )

        self._embedding_dimensions = (
            settings.gemini_embedding_dimensions
        )

        self._provider = (
            provider
            if provider is not None
            else GeminiProvider(
                settings=settings,
            )
        )

    async def embed_query(
        self,
        question: str,
    ) -> QueryEmbeddingResult:
        """Create one validated retrieval-query vector."""

        normalized_question = _normalize_question(
            question,
        )

        request = EmbeddingRequest(
            texts=(
                normalized_question,
            ),
            task_type=(
                EmbeddingTaskType.RETRIEVAL_QUERY
            ),
        )

        try:
            provider_result = await self._provider.embed(
                request,
            )
        except AIProviderError as exc:
            raise QueryEmbeddingProviderError(
                "The query embedding provider failed.",
            ) from exc

        (
            embedding,
            provider_name,
            embedding_model,
        ) = _validate_provider_result(
            result=provider_result,
            expected_model=self._embedding_model,
            expected_dimensions=(
                self._embedding_dimensions
            ),
        )

        return QueryEmbeddingResult(
            question=normalized_question,
            embedding=embedding,
            provider=provider_name,
            embedding_model=embedding_model,
            embedding_dimensions=(
                self._embedding_dimensions
            ),
            task_type=(
                EmbeddingTaskType.RETRIEVAL_QUERY
            ),
        )

    async def aclose(
        self,
    ) -> None:
        """Close provider-owned resources when supported."""

        close_method = getattr(
            self._provider,
            "aclose",
            None,
        )

        if not callable(
            close_method,
        ):
            return

        close_result = close_method()

        if isawaitable(
            close_result,
        ):
            await close_result


def _normalize_question(
    question: str,
) -> str:
    """Normalize and validate one student question."""

    if not isinstance(
        question,
        str,
    ):
        raise QueryEmbeddingValidationError(
            "The query must be a string.",
        )

    normalized_question = question.strip()

    if not normalized_question:
        raise QueryEmbeddingValidationError(
            "The query must not be empty.",
        )

    return normalized_question


def _validate_provider_result(
    *,
    result: EmbeddingResult,
    expected_model: str,
    expected_dimensions: int,
) -> tuple[
    tuple[float, ...],
    str,
    str,
]:
    """Validate provider metadata and the single returned vector."""

    vectors = getattr(
        result,
        "vectors",
        None,
    )

    if isinstance(
        vectors,
        (
            str,
            bytes,
            bytearray,
        ),
    ) or not isinstance(
        vectors,
        Sequence,
    ):
        raise QueryEmbeddingValidationError(
            "The provider response does not contain "
            "a valid vector sequence.",
        )

    if len(vectors) != 1:
        raise QueryEmbeddingValidationError(
            "The provider must return exactly one "
            "query embedding.",
        )

    declared_dimensions = getattr(
        result,
        "dimensions",
        None,
    )

    if isinstance(
        declared_dimensions,
        bool,
    ) or not isinstance(
        declared_dimensions,
        int,
    ):
        raise QueryEmbeddingValidationError(
            "The provider returned invalid embedding dimensions.",
        )

    if declared_dimensions != expected_dimensions:
        raise QueryEmbeddingValidationError(
            "The provider query embedding dimensions "
            "do not match configuration.",
        )

    provider_name = _read_non_empty_text(
        value=getattr(
            result,
            "provider",
            None,
        ),
        error_message=(
            "The provider returned an invalid provider name."
        ),
    )

    embedding_model = _read_non_empty_text(
        value=getattr(
            result,
            "model",
            None,
        ),
        error_message=(
            "The provider returned an invalid embedding model."
        ),
    )

    if embedding_model != expected_model:
        raise QueryEmbeddingValidationError(
            "The provider embedding model "
            "does not match configuration.",
        )

    embedding = _validate_embedding(
        embedding=vectors[0],
        expected_dimensions=expected_dimensions,
    )

    return (
        embedding,
        provider_name,
        embedding_model,
    )


def _read_non_empty_text(
    *,
    value: object,
    error_message: str,
) -> str:
    """Return normalized provider metadata text."""

    if not isinstance(
        value,
        str,
    ):
        raise QueryEmbeddingValidationError(
            error_message,
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise QueryEmbeddingValidationError(
            error_message,
        )

    return normalized_value


def _validate_embedding(
    *,
    embedding: object,
    expected_dimensions: int,
) -> tuple[float, ...]:
    """Validate one finite, nonzero query vector."""

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
        raise QueryEmbeddingValidationError(
            "The query embedding must be a numeric sequence.",
        )

    if len(embedding) != expected_dimensions:
        raise QueryEmbeddingValidationError(
            "The query embedding has the wrong "
            "number of dimensions.",
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
            raise QueryEmbeddingValidationError(
                "Query embedding values must be real numbers.",
            )

        normalized_value = float(
            value,
        )

        if not isfinite(
            normalized_value,
        ):
            raise QueryEmbeddingValidationError(
                "Query embedding values must be finite.",
            )

        normalized_values.append(
            normalized_value,
        )

    if not any(
        value != 0.0
        for value in normalized_values
    ):
        raise QueryEmbeddingValidationError(
            "The query embedding cannot be a zero vector.",
        )

    return tuple(
        normalized_values,
    )