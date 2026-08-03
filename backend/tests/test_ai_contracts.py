# File: /backend/tests/test_ai_contracts.py
# Purpose: Verifies provider-independent AI requests, results,
# interfaces, validation, and controlled exception types.

import pytest

from app.ai import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderRequestError,
    AIProviderResponseError,
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
)


def test_generation_request_normalizes_text() -> None:
    """Generation text inputs must be normalized."""

    request = GenerationRequest(
        prompt="  Explain photosynthesis.  ",
        system_instruction="  Use simple language.  ",
        temperature=0.2,
        max_output_tokens=256,
    )

    assert request.prompt == "Explain photosynthesis."
    assert request.system_instruction == "Use simple language."
    assert request.temperature == 0.2
    assert request.max_output_tokens == 256


def test_blank_generation_prompt_is_rejected() -> None:
    """A generation request must contain a usable prompt."""

    with pytest.raises(
        ValueError,
        match="Generation prompt must not be empty",
    ):
        GenerationRequest(
            prompt="   ",
        )


@pytest.mark.parametrize(
    "temperature",
    [
        -0.1,
        2.1,
    ],
)
def test_invalid_generation_temperature_is_rejected(
    temperature: float,
) -> None:
    """Request-level generation temperature must be bounded."""

    with pytest.raises(
        ValueError,
        match="Generation temperature",
    ):
        GenerationRequest(
            prompt="Valid prompt",
            temperature=temperature,
        )


@pytest.mark.parametrize(
    "max_output_tokens",
    [
        0,
        8193,
    ],
)
def test_invalid_generation_output_limit_is_rejected(
    max_output_tokens: int,
) -> None:
    """Request-level output limits must remain controlled."""

    with pytest.raises(
        ValueError,
        match="Generation max output tokens",
    ):
        GenerationRequest(
            prompt="Valid prompt",
            max_output_tokens=max_output_tokens,
        )


def test_embedding_request_normalizes_texts() -> None:
    """Embedding inputs must be stored without surrounding spaces."""

    request = EmbeddingRequest(
        texts=(
            "  First study note. ",
            "Second study note.  ",
        ),
        task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT,
    )

    assert request.texts == (
        "First study note.",
        "Second study note.",
    )
    assert request.task_type is EmbeddingTaskType.RETRIEVAL_DOCUMENT


def test_embedding_request_requires_texts() -> None:
    """An embedding request must contain at least one text."""

    with pytest.raises(
        ValueError,
        match="at least one text",
    ):
        EmbeddingRequest(
            texts=(),
            task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
        )


def test_embedding_request_rejects_blank_text() -> None:
    """Every embedding input must contain usable text."""

    with pytest.raises(
        ValueError,
        match="texts must not be empty",
    ):
        EmbeddingRequest(
            texts=(
                "Valid text",
                "   ",
            ),
            task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT,
        )


def test_generation_result_normalizes_metadata() -> None:
    """Generation result fields must be usable and normalized."""

    result = GenerationResult(
        text="  Generated answer.  ",
        provider="  gemini  ",
        model="  test-model  ",
        input_tokens=10,
        output_tokens=5,
    )

    assert result.text == "Generated answer."
    assert result.provider == "gemini"
    assert result.model == "test-model"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


def test_embedding_result_accepts_consistent_vectors() -> None:
    """Consistent finite vectors must create a valid result."""

    result = EmbeddingResult(
        vectors=(
            (0.1, 0.2, 0.3),
            (0.4, 0.5, 0.6),
        ),
        provider="gemini",
        model="test-embedding-model",
        dimensions=3,
    )

    assert len(result.vectors) == 2
    assert result.dimensions == 3


def test_embedding_result_rejects_empty_vectors() -> None:
    """An embedding result must contain at least one vector."""

    with pytest.raises(
        ValueError,
        match="at least one vector",
    ):
        EmbeddingResult(
            vectors=(),
            provider="gemini",
            model="test-model",
            dimensions=3,
        )


def test_embedding_result_rejects_wrong_dimensions() -> None:
    """Every vector must match the declared output dimensions."""

    with pytest.raises(
        ValueError,
        match="declared dimensions",
    ):
        EmbeddingResult(
            vectors=((0.1, 0.2),),
            provider="gemini",
            model="test-model",
            dimensions=3,
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        float("nan"),
        float("inf"),
    ],
)
def test_embedding_result_rejects_non_finite_values(
    invalid_value: float,
) -> None:
    """NaN and infinite vector values must be rejected."""

    with pytest.raises(
        ValueError,
        match="finite numeric values",
    ):
        EmbeddingResult(
            vectors=((0.1, invalid_value),),
            provider="gemini",
            model="test-model",
            dimensions=2,
        )


class FakeGenerationProvider:
    """Minimal implementation used for protocol validation."""

    @property
    def provider_name(self) -> str:
        """Return the fake provider name."""

        return "fake"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Return a deterministic fake result."""

        return GenerationResult(
            text=request.prompt,
            provider=self.provider_name,
            model="fake-generation-model",
        )


class FakeEmbeddingProvider:
    """Minimal implementation used for protocol validation."""

    @property
    def provider_name(self) -> str:
        """Return the fake provider name."""

        return "fake"

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Return deterministic fake vectors."""

        vectors = tuple((0.1, 0.2) for _ in request.texts)

        return EmbeddingResult(
            vectors=vectors,
            provider=self.provider_name,
            model="fake-embedding-model",
            dimensions=2,
        )


def test_protocols_accept_matching_implementations() -> None:
    """Structurally compatible providers must satisfy protocols."""

    assert isinstance(
        FakeGenerationProvider(),
        GenerationProvider,
    )
    assert isinstance(
        FakeEmbeddingProvider(),
        EmbeddingProvider,
    )


def test_provider_errors_share_base_type() -> None:
    """Specific controlled errors must inherit from one base type."""

    assert issubclass(
        AIProviderConfigurationError,
        AIProviderError,
    )
    assert issubclass(
        AIProviderRequestError,
        AIProviderError,
    )
    assert issubclass(
        AIProviderResponseError,
        AIProviderError,
    )
