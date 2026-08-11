# File: /backend/app/api/flashcard_orchestration_dependency.py
# Purpose: Assembles Flashcard source loading, AI generation,
# orchestration, and persistence for FastAPI.

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.ai.providers import GeminiProvider
from app.api.flashcard_dependency import (
    get_flashcard_service,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.services.flashcard_generation import (
    FlashcardGenerationService,
)
from app.services.flashcard_orchestration import (
    FlashcardOrchestrationService,
)
from app.services.flashcard_service import (
    FlashcardService,
)
from app.services.flashcard_source_loader import (
    FlashcardSourceLoader,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)


async def get_flashcard_orchestration_service(
    settings: Annotated[
        Settings,
        Depends(
            get_settings,
        ),
    ],
    flashcard_service: Annotated[
        FlashcardService,
        Depends(
            get_flashcard_service,
        ),
    ],
) -> AsyncIterator[
    FlashcardOrchestrationService
]:
    """Build the complete Flashcard generation workflow."""

    provider = GeminiProvider(
        settings=settings,
    )

    generation_service = FlashcardGenerationService(
        provider=provider,
    )

    admin_service = SupabaseAdminService(
        settings=settings,
    )

    source_loader = FlashcardSourceLoader(
        admin_service,
    )

    orchestration_service = (
        FlashcardOrchestrationService(
            source_loader=source_loader,
            generation_service=generation_service,
            flashcard_service=flashcard_service,
        )
    )

    try:
        yield orchestration_service

    finally:
        await generation_service.aclose()