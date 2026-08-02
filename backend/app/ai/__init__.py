# File: /backend/app/ai/__init__.py
# Purpose: Exposes the shared AI contracts and controlled exception
# types used by backend services and provider implementations.

from app.ai.contracts import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderRequestError,
    AIProviderResponseError,
)

__all__ = [
    "AIProviderConfigurationError",
    "AIProviderError",
    "AIProviderRequestError",
    "AIProviderResponseError",
    "EmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResult",
    "EmbeddingTaskType",
    "GenerationProvider",
    "GenerationRequest",
    "GenerationResult",
]
