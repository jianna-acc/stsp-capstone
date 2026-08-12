# File: /backend/app/api/grounded_answer_generation_dependency.py

from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.provider_factory import create_generation_provider
from app.core.config import get_settings
from app.services.grounded_answer_generation import (
    GroundedAnswerGenerationService,
)


async def get_grounded_answer_generation_service(
) -> AsyncIterator[GroundedAnswerGenerationService]:
    """Provide a configured grounded-answer generation service."""

    settings = get_settings()

    provider = create_generation_provider(
        settings=settings,
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    try:
        yield service
    finally:
        await service.aclose()