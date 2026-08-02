# File: /backend/app/ai/__init__.py
# Purpose: Exposes the shared AI contracts and controlled exception
# types used by backend services and provider implementations.

from app.ai.chunking import (
    ChunkingRequest,
    ChunkingResult,
    EmbeddingBatch,
    StudyMaterialChunk,
)
from app.ai.contracts import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
)
from app.ai.embedding_batcher import EmbeddingBatchPreparer
from app.ai.errors import (
    AIChunkingError,
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.ai.preparation import StudyMaterialPreparation
from app.ai.text_chunker import TextChunker

__all__ = [
    "AIChunkingError",
    "AIProviderConfigurationError",
    "AIProviderError",
    "AIProviderRequestError",
    "AIProviderResponseError",
    "ChunkingRequest",
    "ChunkingResult",
    "EmbeddingBatch",
    "EmbeddingBatchPreparer",
    "EmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResult",
    "EmbeddingTaskType",
    "GenerationProvider",
    "GenerationRequest",
    "GenerationResult",
    "StudyMaterialChunk",
    "StudyMaterialPreparation",
    "TextChunker",
]
