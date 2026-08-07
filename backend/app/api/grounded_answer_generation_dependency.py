# File: /backend/app/api/grounded_answer_generation_dependency.py

from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.providers import GeminiProvider
from app.core.config import get_settings
from app.services.grounded_answer_generation import (
    GroundedAnswerGenerationService,
)


async def get_grounded_answer_generation_service(
) -> AsyncIterator[GroundedAnswerGenerationService]:
    """Provide a configured grounded-answer generation service."""

    settings = get_settings()

    provider = GeminiProvider(
        settings=settings,
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
        temperature=(
            settings.gemini_generation_temperature
        ),
        max_output_tokens=(
            settings.gemini_generation_max_output_tokens
        ),
    )

    try:
        yield service
    finally:
        await service.aclose()