# File: /backend/tests/test_study_material_embedder.py
# Purpose: Tests study-material embedding execution and vector
# validation with mocked providers and no external calls.

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any, cast

import pytest

from app.ai.preparation import (
    StudyMaterialPreparation,
)
from app.core.config import Settings
from app.services.study_material_embedder import (
    StudyMaterialEmbedder,
    StudyMaterialEmbeddingValidationError,
)

EMBEDDING_DIMENSIONS = 768


class StubEmbeddingProvider:
    """Returns predefined provider results in request order."""

    def __init__(
        self,
        results: Sequence[Any],
    ) -> None:
        self.results = list(
            results,
        )

        self.requests: list[Any] = []

    async def embed(
        self,
        request: Any,
    ) -> Any:
        """Return the next configured result."""

        self.requests.append(
            request,
        )

        if not self.results:
            raise AssertionError(
                "No stub embedding result remains.",
            )

        result = self.results.pop(
            0,
        )

        if isinstance(
            result,
            Exception,
        ):
            raise result

        return result


def make_settings() -> Settings:
    """Create the settings needed by the embedder."""

    return cast(
        Settings,
        SimpleNamespace(
            gemini_embedding_model=("gemini-embedding-2"),
            gemini_embedding_dimensions=(EMBEDDING_DIMENSIONS),
        ),
    )


def make_vector(
    value: float = 0.125,
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> tuple[float, ...]:
    """Create one embedding vector."""

    return tuple(
        value
        for _ in range(
            dimensions,
        )
    )


def make_batch(
    *,
    batch_index: int,
    chunk_count: int,
) -> Any:
    """Create one batch-shaped test object."""

    return SimpleNamespace(
        batch_index=batch_index,
        chunks=tuple(
            object()
            for _ in range(
                chunk_count,
            )
        ),
    )


def make_request(
    *,
    text_count: int,
) -> Any:
    """Create one request-shaped test object."""

    return SimpleNamespace(
        texts=tuple(
            f"Text {index}"
            for index in range(
                text_count,
            )
        ),
    )


def make_preparation(
    *,
    batches: Sequence[Any] | None = None,
    requests: Sequence[Any] | None = None,
    chunk_count: int | None = None,
) -> StudyMaterialPreparation:
    """Create a preparation-shaped test object."""

    resolved_batches = tuple(
        batches
        if batches is not None
        else (
            make_batch(
                batch_index=0,
                chunk_count=2,
            ),
            make_batch(
                batch_index=1,
                chunk_count=1,
            ),
        )
    )

    resolved_requests = tuple(
        requests
        if requests is not None
        else (
            make_request(
                text_count=2,
            ),
            make_request(
                text_count=1,
            ),
        )
    )

    resolved_chunk_count = (
        chunk_count
        if chunk_count is not None
        else sum(len(batch.chunks) for batch in resolved_batches)
    )

    return cast(
        StudyMaterialPreparation,
        SimpleNamespace(
            batches=resolved_batches,
            embedding_requests=(resolved_requests),
            chunk_count=(resolved_chunk_count),
        ),
    )


def test_embeds_batches_and_preserves_order() -> None:
    """Vectors are flattened in batch and chunk order."""

    first_vector = make_vector(
        0.1,
    )

    second_vector = make_vector(
        0.2,
    )

    third_vector = make_vector(
        0.3,
    )

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(
                    first_vector,
                    second_vector,
                ),
            ),
            SimpleNamespace(
                embeddings=(third_vector,),
            ),
        ),
    )

    preparation = make_preparation()

    embedder = StudyMaterialEmbedder(
        settings=make_settings(),
        provider=provider,
    )

    result = asyncio.run(
        embedder.embed_preparation(
            preparation,
        ),
    )

    assert result.embedding_model == ("gemini-embedding-2")

    assert result.embedding_dimensions == 768
    assert result.batch_count == 2
    assert result.chunk_count == 3

    assert result.embeddings == (
        first_vector,
        second_vector,
        third_vector,
    )

    assert provider.requests == list(
        preparation.embedding_requests,
    )


def test_accepts_vectors_result_alias() -> None:
    """The compatibility vector field is also accepted."""

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                vectors=(make_vector(),),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    result = asyncio.run(
        StudyMaterialEmbedder(
            settings=make_settings(),
            provider=provider,
        ).embed_preparation(
            preparation,
        ),
    )

    assert result.chunk_count == 1


def test_rejects_empty_batches() -> None:
    """A preparation must contain embedding work."""

    preparation = make_preparation(
        batches=(),
        requests=(),
        chunk_count=0,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="At least one embedding batch",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=StubEmbeddingProvider(
                    results=(),
                ),
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_batch_request_count_mismatch() -> None:
    """Every batch must have one request."""

    preparation = make_preparation(
        requests=(
            make_request(
                text_count=2,
            ),
        ),
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="exactly one embedding request",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=StubEmbeddingProvider(
                    results=(),
                ),
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_noncontiguous_batch_indexes() -> None:
    """Batch indexes must begin at zero."""

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=1,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="batch indexes",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=StubEmbeddingProvider(
                    results=(),
                ),
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_empty_batch() -> None:
    """One embedding batch cannot contain zero chunks."""

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=0,
            ),
        ),
        requests=(
            make_request(
                text_count=0,
            ),
        ),
        chunk_count=0,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="cannot be empty",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=StubEmbeddingProvider(
                    results=(),
                ),
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_request_text_count_mismatch() -> None:
    """Request text count must match its batch."""

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=2,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=2,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="text count",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=StubEmbeddingProvider(
                    results=(),
                ),
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_missing_result_embeddings() -> None:
    """The provider result must expose vectors."""

    provider = StubEmbeddingProvider(
        results=(SimpleNamespace(),),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="valid embedding sequence",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_provider_vector_count_mismatch() -> None:
    """The provider must return one vector per chunk."""

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(make_vector(),),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=2,
            ),
        ),
        requests=(
            make_request(
                text_count=2,
            ),
        ),
        chunk_count=2,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="unexpected number",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_wrong_vector_dimensions() -> None:
    """Provider vectors must match vector(768)."""

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(
                    make_vector(
                        dimensions=767,
                    ),
                ),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="wrong number of dimensions",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_nonnumeric_vector_value() -> None:
    """Provider vectors must contain real numbers."""

    invalid_vector: list[Any] = list(
        make_vector(),
    )

    invalid_vector[5] = "invalid"

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(invalid_vector,),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="real numbers",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_boolean_vector_value() -> None:
    """Boolean values are not numeric embeddings."""

    invalid_vector: list[Any] = list(
        make_vector(),
    )

    invalid_vector[5] = True

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(invalid_vector,),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="real numbers",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )


@pytest.mark.parametrize(
    "invalid_value",
    (
        float("nan"),
        float("inf"),
        float("-inf"),
    ),
)
def test_rejects_nonfinite_vector_value(
    invalid_value: float,
) -> None:
    """NaN and infinite values cannot be persisted."""

    invalid_vector = list(
        make_vector(),
    )

    invalid_vector[5] = invalid_value

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(invalid_vector,),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=1,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="must be finite",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )


def test_rejects_final_chunk_count_mismatch() -> None:
    """Flattened vectors must match preparation.chunk_count."""

    provider = StubEmbeddingProvider(
        results=(
            SimpleNamespace(
                embeddings=(make_vector(),),
            ),
        ),
    )

    preparation = make_preparation(
        batches=(
            make_batch(
                batch_index=0,
                chunk_count=1,
            ),
        ),
        requests=(
            make_request(
                text_count=1,
            ),
        ),
        chunk_count=2,
    )

    with pytest.raises(
        StudyMaterialEmbeddingValidationError,
        match="prepared chunk count",
    ):
        asyncio.run(
            StudyMaterialEmbedder(
                settings=make_settings(),
                provider=provider,
            ).embed_preparation(
                preparation,
            ),
        )
