# File: /backend/tests/test_gemini_provider.py
# Purpose: Verifies the Gemini provider with deterministic fake
# clients and without making external API requests.

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai import (
    AIProviderConfigurationError,
    AIProviderRequestError,
    AIProviderResponseError,
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingTaskType,
    GenerationProvider,
    GenerationRequest,
)
from app.ai.providers import GeminiProvider
from app.ai.providers import gemini as gemini_module
from app.core.config import Settings

EMBEDDING_DIMENSIONS = 128


def build_settings(
    **overrides: Any,
) -> Settings:
    """Create isolated valid Gemini settings for provider tests."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "gemini_api_key": "test-gemini-key",
        "gemini_generation_model": "test-generation-model",
        "gemini_embedding_model": "test-embedding-model",
        "gemini_embedding_dimensions": EMBEDDING_DIMENSIONS,
        "gemini_generation_temperature": 0.2,
        "gemini_generation_max_output_tokens": 256,
        "gemini_request_timeout_seconds": 30,
        "_env_file": None,
    }
    values.update(overrides)

    return Settings(**values)


def build_vector(
    value: float,
) -> list[float]:
    """Create one valid deterministic test vector."""

    return [value for _ in range(EMBEDDING_DIMENSIONS)]


class FakeModels:
    """Record model calls and return controlled fake responses."""

    def __init__(
        self,
        *,
        generation_response: Any | None = None,
        embedding_response: Any | None = None,
        generation_error: Exception | None = None,
        embedding_error: Exception | None = None,
    ) -> None:
        """Store responses and errors used by test requests."""

        self.generation_response = (
            generation_response
            if generation_response is not None
            else SimpleNamespace(
                text="Generated answer.",
                usage_metadata=None,
            )
        )
        self.embedding_response = (
            embedding_response
            if embedding_response is not None
            else SimpleNamespace(
                embeddings=[
                    SimpleNamespace(
                        values=build_vector(0.1),
                    ),
                ],
            )
        )
        self.generation_error = generation_error
        self.embedding_error = embedding_error

        self.generation_call: dict[str, Any] | None = None
        self.embedding_call: dict[str, Any] | None = None

    async def generate_content(
        self,
        **kwargs: Any,
    ) -> Any:
        """Return a fake generation response or controlled error."""

        self.generation_call = kwargs

        if self.generation_error is not None:
            raise self.generation_error

        return self.generation_response

    async def embed_content(
        self,
        **kwargs: Any,
    ) -> Any:
        """Return a fake embedding response or controlled error."""

        self.embedding_call = kwargs

        if self.embedding_error is not None:
            raise self.embedding_error

        return self.embedding_response


class FakeAsyncClient:
    """Expose fake async SDK models and close-state tracking."""

    def __init__(
        self,
        models: FakeModels,
    ) -> None:
        """Store the model service used by the fake client."""

        self.models = models
        self.closed = False

    async def aclose(self) -> None:
        """Record that the async client was closed."""

        self.closed = True


class FakeClient:
    """Provide the SDK-compatible aio attribute used by the provider."""

    def __init__(
        self,
        models: FakeModels,
    ) -> None:
        """Create the fake asynchronous SDK surface."""

        self.aio = FakeAsyncClient(models)


def test_provider_satisfies_shared_contracts() -> None:
    """Gemini must implement both provider protocols."""

    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(FakeModels()),
    )

    assert provider.provider_name == "gemini"
    assert isinstance(provider, GenerationProvider)
    assert isinstance(provider, EmbeddingProvider)


def test_provider_requires_api_key() -> None:
    """The provider must fail safely when no Gemini key exists."""

    with pytest.raises(
        AIProviderConfigurationError,
        match="GEMINI_API_KEY",
    ):
        GeminiProvider(
            settings=build_settings(
                gemini_api_key="",
            ),
            client=FakeClient(FakeModels()),
        )


def test_provider_builds_and_closes_owned_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider-created clients must receive safe options and close."""

    captured_options: dict[str, Any] = {}
    fake_client = FakeClient(FakeModels())

    def fake_client_factory(
        **kwargs: Any,
    ) -> FakeClient:
        captured_options.update(kwargs)
        return fake_client

    monkeypatch.setattr(
        gemini_module.genai,
        "Client",
        fake_client_factory,
    )

    provider = GeminiProvider(
        settings=build_settings(),
    )

    assert captured_options["api_key"] == "test-gemini-key"
    assert captured_options["http_options"].timeout == 30_000

    asyncio.run(provider.aclose())

    assert fake_client.aio.closed is True


def test_generation_uses_configured_defaults() -> None:
    """Generation must use controlled defaults and return metadata."""

    response = SimpleNamespace(
        text="  Photosynthesis converts light into energy.  ",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
    )
    models = FakeModels(
        generation_response=response,
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    result = asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="  Explain photosynthesis.  ",
                system_instruction="Use simple language.",
            ),
        ),
    )

    assert result.text == "Photosynthesis converts light into energy."
    assert result.provider == "gemini"
    assert result.model == "test-generation-model"
    assert result.input_tokens == 12
    assert result.output_tokens == 7

    assert models.generation_call is not None
    assert models.generation_call["model"] == "test-generation-model"
    assert models.generation_call["contents"] == "Explain photosynthesis."

    config = models.generation_call["config"]

    assert config.system_instruction == "Use simple language."
    assert config.temperature == 0.2
    assert config.max_output_tokens == 256


def test_generation_honors_request_overrides() -> None:
    """Request values must override configured generation defaults."""

    models = FakeModels()
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Create a short quiz.",
                temperature=0.7,
                max_output_tokens=64,
            ),
        ),
    )

    assert models.generation_call is not None

    config = models.generation_call["config"]

    assert config.temperature == 0.7
    assert config.max_output_tokens == 64


def test_generation_rejects_empty_response() -> None:
    """The provider must reject responses without usable text."""

    models = FakeModels(
        generation_response=SimpleNamespace(
            text="   ",
            usage_metadata=None,
        ),
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    with pytest.raises(
        AIProviderResponseError,
        match="no usable generated text",
    ):
        asyncio.run(
            provider.generate(
                GenerationRequest(
                    prompt="Valid prompt",
                ),
            ),
        )


def test_generation_wraps_request_errors() -> None:
    """External generation failures must become controlled errors."""

    models = FakeModels(
        generation_error=RuntimeError(
            "External SDK failure",
        ),
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    with pytest.raises(
        AIProviderRequestError,
        match="generation request failed",
    ):
        asyncio.run(
            provider.generate(
                GenerationRequest(
                    prompt="Valid prompt",
                ),
            ),
        )


def test_embedding_formats_document_inputs() -> None:
    """Document embeddings must use separate document-prefixed inputs."""

    response = SimpleNamespace(
        embeddings=[
            SimpleNamespace(
                values=build_vector(0.1),
            ),
            SimpleNamespace(
                values=build_vector(0.2),
            ),
        ],
    )
    models = FakeModels(
        embedding_response=response,
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    result = asyncio.run(
        provider.embed(
            EmbeddingRequest(
                texts=(
                    "Photosynthesis uses sunlight.",
                    "Plants contain chlorophyll.",
                ),
                task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
            ),
        ),
    )

    assert len(result.vectors) == 2
    assert result.dimensions == EMBEDDING_DIMENSIONS
    assert result.provider == "gemini"
    assert result.model == "test-embedding-model"

    assert models.embedding_call is not None
    assert models.embedding_call["model"] == "test-embedding-model"

    contents = models.embedding_call["contents"]

    assert len(contents) == 2
    assert contents[0].parts[0].text == (
        "title: none | text: Photosynthesis uses sunlight."
    )
    assert contents[1].parts[0].text == (
        "title: none | text: Plants contain chlorophyll."
    )

    config = models.embedding_call["config"]

    assert config.output_dimensionality == EMBEDDING_DIMENSIONS


def test_embedding_formats_query_inputs() -> None:
    """Query embeddings must use the question-answering prefix."""

    models = FakeModels()
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    asyncio.run(
        provider.embed(
            EmbeddingRequest(
                texts=("How do plants produce energy?",),
                task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
            ),
        ),
    )

    assert models.embedding_call is not None

    contents = models.embedding_call["contents"]

    assert contents[0].parts[0].text == (
        "task: question answering | query: How do plants produce energy?"
    )


def test_embedding_rejects_wrong_vector_count() -> None:
    """Returned vector count must match the number of inputs."""

    models = FakeModels(
        embedding_response=SimpleNamespace(
            embeddings=[
                SimpleNamespace(
                    values=build_vector(0.1),
                ),
            ],
        ),
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    with pytest.raises(
        AIProviderResponseError,
        match="unexpected number",
    ):
        asyncio.run(
            provider.embed(
                EmbeddingRequest(
                    texts=(
                        "First text",
                        "Second text",
                    ),
                    task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
                ),
            ),
        )


def test_embedding_rejects_missing_values() -> None:
    """Every returned embedding must contain vector values."""

    models = FakeModels(
        embedding_response=SimpleNamespace(
            embeddings=[
                SimpleNamespace(
                    values=None,
                ),
            ],
        ),
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    with pytest.raises(
        AIProviderResponseError,
        match="without vector values",
    ):
        asyncio.run(
            provider.embed(
                EmbeddingRequest(
                    texts=("Valid text",),
                    task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
                ),
            ),
        )


def test_embedding_wraps_request_errors() -> None:
    """External embedding failures must become controlled errors."""

    models = FakeModels(
        embedding_error=RuntimeError(
            "External SDK failure",
        ),
    )
    provider = GeminiProvider(
        settings=build_settings(),
        client=FakeClient(models),
    )

    with pytest.raises(
        AIProviderRequestError,
        match="embedding request failed",
    ):
        asyncio.run(
            provider.embed(
                EmbeddingRequest(
                    texts=("Valid text",),
                    task_type=(EmbeddingTaskType.RETRIEVAL_QUERY),
                ),
            ),
        )
