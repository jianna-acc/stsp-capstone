# File: /backend/app/ai/contracts.py
# Purpose: Defines provider-independent AI requests, results, task
# types, and asynchronous provider interfaces.

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Protocol, runtime_checkable


class EmbeddingTaskType(StrEnum):
    """Supported semantic purposes for generated embeddings."""

    RETRIEVAL_DOCUMENT = "retrieval_document"
    RETRIEVAL_QUERY = "retrieval_query"


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Provider-independent request for text generation."""

    prompt: str
    system_instruction: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None

    def __post_init__(self) -> None:
        """Normalize and validate generation request values."""

        normalized_prompt = self.prompt.strip()

        if not normalized_prompt:
            raise ValueError(
                "Generation prompt must not be empty.",
            )

        object.__setattr__(
            self,
            "prompt",
            normalized_prompt,
        )

        if self.system_instruction is not None:
            normalized_instruction = self.system_instruction.strip()

            object.__setattr__(
                self,
                "system_instruction",
                normalized_instruction or None,
            )

        if self.temperature is not None and not (0 <= self.temperature <= 2):
            raise ValueError(
                "Generation temperature must be between 0 and 2.",
            )

        if self.max_output_tokens is not None and not (
            1 <= self.max_output_tokens <= 8192
        ):
            raise ValueError(
                "Generation max output tokens must be between 1 and 8192.",
            )


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Provider-independent result returned by a generation model."""

    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None

    def __post_init__(self) -> None:
        """Normalize and validate generation result values."""

        normalized_text = self.text.strip()
        normalized_provider = self.provider.strip()
        normalized_model = self.model.strip()

        if not normalized_text:
            raise ValueError(
                "Generation result text must not be empty.",
            )

        if not normalized_provider:
            raise ValueError(
                "Generation result provider must not be empty.",
            )

        if not normalized_model:
            raise ValueError(
                "Generation result model must not be empty.",
            )

        for field_name, token_count in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
        ):
            if token_count is not None and token_count < 0:
                raise ValueError(
                    f"{field_name} must not be negative.",
                )

        object.__setattr__(
            self,
            "text",
            normalized_text,
        )
        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )
        object.__setattr__(
            self,
            "model",
            normalized_model,
        )


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    """Provider-independent request for one or more text vectors."""

    texts: tuple[str, ...]
    task_type: EmbeddingTaskType

    def __post_init__(self) -> None:
        """Normalize and validate embedding input texts."""

        if not self.texts:
            raise ValueError(
                "Embedding request must contain at least one text.",
            )

        normalized_texts = tuple(text.strip() for text in self.texts)

        if any(not text for text in normalized_texts):
            raise ValueError(
                "Embedding request texts must not be empty.",
            )

        object.__setattr__(
            self,
            "texts",
            normalized_texts,
        )


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    """Provider-independent vectors returned by an embedding model."""

    vectors: tuple[tuple[float, ...], ...]
    provider: str
    model: str
    dimensions: int

    def __post_init__(self) -> None:
        """Validate vector count, dimensions, and numeric values."""

        normalized_provider = self.provider.strip()
        normalized_model = self.model.strip()

        if not self.vectors:
            raise ValueError(
                "Embedding result must contain at least one vector.",
            )

        if not normalized_provider:
            raise ValueError(
                "Embedding result provider must not be empty.",
            )

        if not normalized_model:
            raise ValueError(
                "Embedding result model must not be empty.",
            )

        if self.dimensions <= 0:
            raise ValueError(
                "Embedding result dimensions must be positive.",
            )

        for vector in self.vectors:
            if len(vector) != self.dimensions:
                raise ValueError(
                    "Every embedding vector must match the declared dimensions.",
                )

            if any(not isfinite(value) for value in vector):
                raise ValueError(
                    "Embedding vectors must contain only finite numeric values.",
                )

        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )
        object.__setattr__(
            self,
            "model",
            normalized_model,
        )


@runtime_checkable
class GenerationProvider(Protocol):
    """Interface implemented by text-generation providers."""

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal name."""

        ...

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Generate text for a validated provider-independent request."""

        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Interface implemented by embedding providers."""

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal name."""

        ...

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Generate vectors for validated input texts."""

        ...
