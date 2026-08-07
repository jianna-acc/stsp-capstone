# File: /backend/tests/test_query_embedding.py
# Purpose: Tests query embedding creation and validation without
# calling Gemini, Supabase, or any external service.

from __future__ import annotations

import asyncio
from math import inf
from types import SimpleNamespace
from typing import Any, cast

import pytest

from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
)
from app.ai.errors import AIProviderRequestError
from app.core.config import Settings
from app.services.query_embedding import (
    QueryEmbeddingProviderError,
    QueryEmbeddingService,
    QueryEmbeddingValidationError,
)

EMBEDDING_DIMENSIONS = 768
EMBEDDING_MODEL = "gemini-embedding-2"


class StubEmbeddingProvider:
    """Record requests and return one controlled result or error."""

    def __init__(
        self,
        *,
        result: Any | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.requests: list[EmbeddingRequest] = []

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Return the configured provider result."""

        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        if self.result is None:
            raise AssertionError(
                "No stub provider result was configured.",
            )

        return cast(
            EmbeddingResult,
            self.result,
        )


def make_settings() -> Settings:
    """Create the settings required by the query service."""

    return cast(
        Settings,
        SimpleNamespace(
            gemini_embedding_model=EMBEDDING_MODEL,
            gemini_embedding_dimensions=(
                EMBEDDING_DIMENSIONS
            ),
        ),
    )


def make_vector(
    value: float = 0.125,
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> tuple[float, ...]:
    """Create one deterministic embedding vector."""

    return tuple(
        value
        for _ in range(
            dimensions,
        )
    )


def make_result(
    *,
    vectors: tuple[
        tuple[float, ...],
        ...,
    ] | None = None,
    provider: str = "gemini",
    model: str = EMBEDDING_MODEL,
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> EmbeddingResult:
    """Create one valid provider-independent result."""

    return EmbeddingResult(
        vectors=(
            vectors
            if vectors is not None
            else (
                make_vector(),
            )
        ),
        provider=provider,
        model=model,
        dimensions=dimensions,
    )


def test_embeds_normalized_retrieval_query() -> None:
    """One normalized question should produce one query vector."""

    provider = StubEmbeddingProvider(
        result=make_result(),
    )

    result = asyncio.run(
        QueryEmbeddingService(
            settings=make_settings(),
            provider=provider,
        ).embed_query(
            "  How do plants produce energy?  ",
        ),
    )

    assert result.question == (
        "How do plants produce energy?"
    )

    assert result.embedding == make_vector()
    assert result.provider == "gemini"
    assert result.embedding_model == EMBEDDING_MODEL
    assert result.embedding_dimensions == 768

    assert result.task_type is (
        EmbeddingTaskType.RETRIEVAL_QUERY
    )

    assert len(provider.requests) == 1

    request = provider.requests[0]

    assert request.texts == (
        "How do plants produce energy?",
    )

    assert request.task_type is (
        EmbeddingTaskType.RETRIEVAL_QUERY
    )


def test_rejects_non_string_query() -> None:
    """A query must be provided as text."""

    provider = StubEmbeddingProvider(
        result=make_result(),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="must be a string",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                cast(
                    str,
                    123,
                ),
            ),
        )

    assert provider.requests == []


def test_rejects_empty_query() -> None:
    """Whitespace-only questions must not reach the provider."""

    provider = StubEmbeddingProvider(
        result=make_result(),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="must not be empty",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "   ",
            ),
        )

    assert provider.requests == []


def test_wraps_provider_failure() -> None:
    """Controlled AI provider errors should become service errors."""

    provider_error = AIProviderRequestError(
        "External embedding request failed.",
    )

    provider = StubEmbeddingProvider(
        error=provider_error,
    )

    with pytest.raises(
        QueryEmbeddingProviderError,
        match="provider failed",
    ) as error_info:
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "What is photosynthesis?",
            ),
        )

    assert error_info.value.__cause__ is provider_error


def test_rejects_missing_vector_sequence() -> None:
    """The provider result must expose a vector sequence."""

    provider = StubEmbeddingProvider(
        result=SimpleNamespace(
            provider="gemini",
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="valid vector sequence",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_multiple_vectors() -> None:
    """One question must return exactly one vector."""

    provider = StubEmbeddingProvider(
        result=make_result(
            vectors=(
                make_vector(
                    0.1,
                ),
                make_vector(
                    0.2,
                ),
            ),
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="exactly one",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_wrong_declared_dimensions() -> None:
    """Provider dimensions must match application configuration."""

    provider = StubEmbeddingProvider(
        result=SimpleNamespace(
            vectors=(
                make_vector(),
            ),
            provider="gemini",
            model=EMBEDDING_MODEL,
            dimensions=512,
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="do not match configuration",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_wrong_embedding_model() -> None:
    """Returned model metadata must match configuration."""

    provider = StubEmbeddingProvider(
        result=make_result(
            model="unexpected-model",
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="model does not match",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_blank_provider_name() -> None:
    """Returned provider metadata must not be blank."""

    provider = StubEmbeddingProvider(
        result=SimpleNamespace(
            vectors=(
                make_vector(),
            ),
            provider="   ",
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="invalid provider name",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_wrong_vector_length() -> None:
    """The vector itself must contain exactly 768 values."""

    provider = StubEmbeddingProvider(
        result=SimpleNamespace(
            vectors=(
                make_vector(
                    dimensions=767,
                ),
            ),
            provider="gemini",
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="wrong number of dimensions",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_non_real_vector_values() -> None:
    """Booleans and other non-real values must be rejected."""

    invalid_vector = (
        True,
        *make_vector(
            dimensions=767,
        ),
    )

    provider = StubEmbeddingProvider(
        result=SimpleNamespace(
            vectors=(
                invalid_vector,
            ),
            provider="gemini",
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="must be real numbers",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_non_finite_vector_values() -> None:
    """Infinite and NaN-like values must not reach retrieval."""

    invalid_vector = (
        inf,
        *make_vector(
            dimensions=767,
        ),
    )

    provider = StubEmbeddingProvider(
        result=SimpleNamespace(
            vectors=(
                invalid_vector,
            ),
            provider="gemini",
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="must be finite",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )


def test_rejects_zero_vector() -> None:
    """A zero query vector is invalid for cosine retrieval."""

    provider = StubEmbeddingProvider(
        result=make_result(
            vectors=(
                make_vector(
                    value=0.0,
                ),
            ),
        ),
    )

    with pytest.raises(
        QueryEmbeddingValidationError,
        match="zero vector",
    ):
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=provider,
            ).embed_query(
                "Valid question",
            ),
        )