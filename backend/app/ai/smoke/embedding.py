# File: /backend/app/ai/smoke/embedding.py
# Purpose: Performs one explicitly authorized live Gemini embedding
# smoke test without printing credentials or complete vectors.

import argparse
import asyncio
import math
import sys
from collections.abc import Sequence

from app.ai import (
    AIProviderError,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
)
from app.ai.providers import GeminiProvider
from app.core.config import Settings, get_settings

DOCUMENT_TEXT = (
    "Photosynthesis converts light energy into chemical energy that plants can store."
)
QUERY_TEXT = "How do plants convert sunlight into stored energy?"


def build_argument_parser() -> argparse.ArgumentParser:
    """Create command-line arguments for explicit live authorization."""

    parser = argparse.ArgumentParser(
        description=("Run one controlled live Gemini embedding smoke test."),
    )
    parser.add_argument(
        "--confirm-live-call",
        action="store_true",
        help=(
            "Confirm that one controlled live provider smoke test "
            "may consume quota or incur provider charges."
        ),
    )

    return parser


def validate_live_test_authorization(
    settings: Settings,
    *,
    confirmed: bool,
) -> list[str]:
    """Return all reasons why the live request must not run."""

    blockers: list[str] = []

    if not confirmed:
        blockers.append(
            "The --confirm-live-call option was not provided.",
        )

    if not settings.ai_live_smoke_tests_enabled:
        blockers.append(
            "AI_LIVE_SMOKE_TESTS_ENABLED is false.",
        )

    if not settings.gemini_api_key:
        blockers.append(
            "GEMINI_API_KEY is not configured.",
        )

    return blockers


def validate_embedding_result(
    result: EmbeddingResult,
    *,
    settings: Settings,
    label: str,
) -> tuple[float, ...]:
    """Validate one controlled embedding response."""

    if result.provider != "gemini":
        raise RuntimeError(
            f"{label} result used an unexpected provider.",
        )

    if result.model != settings.gemini_embedding_model:
        raise RuntimeError(
            f"{label} result used an unexpected model.",
        )

    if result.dimensions != settings.gemini_embedding_dimensions:
        raise RuntimeError(
            f"{label} result reported unexpected dimensions.",
        )

    if len(result.vectors) != 1:
        raise RuntimeError(
            f"{label} result must contain exactly one vector.",
        )

    vector = result.vectors[0]

    if len(vector) != settings.gemini_embedding_dimensions:
        raise RuntimeError(
            f"{label} vector has unexpected dimensions.",
        )

    return vector


def calculate_vector_norm(
    vector: Sequence[float],
) -> float:
    """Calculate the Euclidean norm of an embedding vector."""

    norm = math.sqrt(
        math.fsum(value * value for value in vector),
    )

    if not math.isfinite(norm) or norm <= 0:
        raise RuntimeError(
            "Gemini returned a zero or invalid embedding vector.",
        )

    return norm


def calculate_cosine_similarity(
    first: Sequence[float],
    second: Sequence[float],
) -> float:
    """Calculate cosine similarity without external dependencies."""

    if len(first) != len(second):
        raise RuntimeError(
            "Embedding vectors have different dimensions.",
        )

    first_norm = calculate_vector_norm(first)
    second_norm = calculate_vector_norm(second)

    dot_product = math.fsum(
        first_value * second_value
        for first_value, second_value in zip(
            first,
            second,
            strict=True,
        )
    )

    similarity = dot_product / (first_norm * second_norm)

    if not math.isfinite(similarity):
        raise RuntimeError(
            "Calculated cosine similarity is invalid.",
        )

    if similarity < -1.000001 or similarity > 1.000001:
        raise RuntimeError(
            "Calculated cosine similarity is outside its valid range.",
        )

    return max(
        -1.0,
        min(1.0, similarity),
    )


async def run_live_embedding_smoke(
    settings: Settings,
) -> None:
    """Perform one document and one query embedding request."""

    provider = GeminiProvider(
        settings=settings,
    )

    try:
        document_result = await provider.embed(
            EmbeddingRequest(
                texts=(DOCUMENT_TEXT,),
                task_type=(EmbeddingTaskType.RETRIEVAL_DOCUMENT),
            ),
        )

        query_result = await provider.embed(
            EmbeddingRequest(
                texts=(QUERY_TEXT,),
                task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
            ),
        )

        document_vector = validate_embedding_result(
            document_result,
            settings=settings,
            label="Document embedding",
        )
        query_vector = validate_embedding_result(
            query_result,
            settings=settings,
            label="Query embedding",
        )

        document_norm = calculate_vector_norm(
            document_vector,
        )
        query_norm = calculate_vector_norm(
            query_vector,
        )
        similarity = calculate_cosine_similarity(
            document_vector,
            query_vector,
        )

        print("Controlled Gemini embedding smoke test passed.")
        print(f"Provider: {document_result.provider}")
        print(f"Model: {document_result.model}")
        print(f"Dimensions: {document_result.dimensions}")
        print(f"Document vectors: {len(document_result.vectors)}")
        print(f"Query vectors: {len(query_result.vectors)}")
        print(f"Document norm: {document_norm:.6f}")
        print(f"Query norm: {query_norm:.6f}")
        print(f"Cosine similarity: {similarity:.6f}")
        print("Vector values were intentionally not printed.")
    finally:
        await provider.aclose()


def main() -> int:
    """Authorize and run the controlled live smoke test."""

    parser = build_argument_parser()
    arguments = parser.parse_args()
    settings = get_settings()

    blockers = validate_live_test_authorization(
        settings,
        confirmed=arguments.confirm_live_call,
    )

    if blockers:
        print(
            "Live Gemini embedding smoke test was not run.",
            file=sys.stderr,
        )

        for blocker in blockers:
            print(
                f"- {blocker}",
                file=sys.stderr,
            )

        return 2

    print(
        "Starting one controlled live Gemini embedding smoke test.",
    )
    print(
        "No credentials or complete vectors will be printed.",
    )

    try:
        asyncio.run(
            run_live_embedding_smoke(settings),
        )
    except AIProviderError as exc:
        print(
            f"Controlled provider failure: {exc}",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as exc:
        print(
            f"Smoke-test validation failure: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
