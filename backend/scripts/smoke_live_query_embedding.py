# File: /backend/scripts/smoke_live_query_embedding.py
# Purpose: Runs an explicitly enabled live Gemini query-embedding
# smoke test without printing credentials or raw vector values.

from __future__ import annotations

import asyncio
from math import isfinite

from app.ai.contracts import EmbeddingTaskType
from app.core.config import (
    Settings,
    get_settings,
)
from app.services.query_embedding import (
    QueryEmbeddingError,
    QueryEmbeddingResult,
    QueryEmbeddingService,
)

EXPECTED_EMBEDDING_DIMENSIONS = 768

SMOKE_QUESTION = "How does photosynthesis convert light energy into chemical energy?"


class LiveQueryEmbeddingSmokeValidationError(
    RuntimeError,
):
    """Raised when a live query-embedding result is invalid."""


async def _execute_live_smoke(
    settings: Settings,
) -> QueryEmbeddingResult:
    """Run one live query embedding and guarantee cleanup."""

    service = QueryEmbeddingService(
        settings=settings,
    )

    try:
        result = await service.embed_query(
            SMOKE_QUESTION,
        )

        _validate_result(
            result=result,
            settings=settings,
        )

        return result
    finally:
        await service.aclose()


def _validate_result(
    *,
    result: QueryEmbeddingResult,
    settings: Settings,
) -> None:
    """Validate the live result without exposing vector values."""

    if settings.gemini_embedding_dimensions != EXPECTED_EMBEDDING_DIMENSIONS:
        raise LiveQueryEmbeddingSmokeValidationError(
            "The configured embedding dimensions must be 768.",
        )

    if result.question != SMOKE_QUESTION:
        raise LiveQueryEmbeddingSmokeValidationError(
            "The returned normalized question is unexpected.",
        )

    if result.provider != "gemini":
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live embedding provider must be Gemini.",
        )

    if result.embedding_model != settings.gemini_embedding_model:
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live embedding model does not match configuration.",
        )

    if result.embedding_dimensions != EXPECTED_EMBEDDING_DIMENSIONS:
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live result must declare 768 dimensions.",
        )

    if result.task_type is not EmbeddingTaskType.RETRIEVAL_QUERY:
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live request must use retrieval_query.",
        )

    if (
        len(
            result.embedding,
        )
        != EXPECTED_EMBEDDING_DIMENSIONS
    ):
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live vector must contain exactly 768 values.",
        )

    if any(
        not isfinite(
            value,
        )
        for value in result.embedding
    ):
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live vector must contain only finite values.",
        )

    if not any(value != 0.0 for value in result.embedding):
        raise LiveQueryEmbeddingSmokeValidationError(
            "The live vector must not be a zero vector.",
        )


def main() -> int:
    """Run the guarded live smoke test and return an exit code."""

    settings = get_settings()

    if not settings.ai_live_smoke_tests_enabled:
        print(
            "LIVE QUERY EMBEDDING SMOKE=SKIPPED",
        )

        print(
            "Reason: AI_LIVE_SMOKE_TESTS_ENABLED is false.",
        )

        return 0

    if not settings.gemini_api_key:
        print(
            "LIVE QUERY EMBEDDING SMOKE=FAIL",
        )

        print(
            "Reason: GEMINI_API_KEY is not configured.",
        )

        return 1

    try:
        result = asyncio.run(
            _execute_live_smoke(
                settings,
            ),
        )
    except (
        QueryEmbeddingError,
        LiveQueryEmbeddingSmokeValidationError,
    ) as exc:
        print(
            "LIVE QUERY EMBEDDING SMOKE=FAIL",
        )

        print(
            f"Error type: {type(exc).__name__}",
        )

        return 1

    print(
        "LIVE QUERY EMBEDDING SMOKE=PASS",
    )

    print(
        f"Provider: {result.provider}",
    )

    print(
        f"Model: {result.embedding_model}",
    )

    print(
        f"Task type: {result.task_type.value}",
    )

    print(
        f"Embedding dimensions: {result.embedding_dimensions}",
    )

    print(
        f"Question characters: {len(result.question)}",
    )

    print(
        "Vector finite: True",
    )

    print(
        "Vector nonzero: True",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(),
    )
