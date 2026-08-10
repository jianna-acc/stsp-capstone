# File: /backend/app/api/quiz_orchestration_dependency.py

# Purpose: Assembles Quiz source loading, AI generation,
# and atomic persistence into one FastAPI dependency.

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.ai.providers import (
    GeminiProvider,
)
from app.api.quiz_dependency import (
    get_quiz_service,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.services.quiz_generation import (
    QuizGenerationService,
)
from app.services.quiz_orchestration import (
    QuizOrchestrationService,
)
from app.services.quiz_service import (
    QuizService,
)
from app.services.quiz_source_loader import (
    QuizSourceLoader,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)


async def get_quiz_orchestration_service(
    settings: Annotated[
        Settings,
        Depends(
            get_settings,
        ),
    ],
    quiz_service: Annotated[
        QuizService,
        Depends(
            get_quiz_service,
        ),
    ],
) -> AsyncIterator[
    QuizOrchestrationService
]:
    """Build the complete Quiz-generation workflow."""

    provider = GeminiProvider(
        settings=settings,
    )

    generation_service = QuizGenerationService(
        provider=provider,
    )

    admin_service = SupabaseAdminService(
        settings=settings,
    )

    source_loader = QuizSourceLoader(
        admin_service,
    )

    orchestration_service = QuizOrchestrationService(
        source_loader=source_loader,
        generation_service=generation_service,
        quiz_service=quiz_service,
    )

    try:
        yield orchestration_service

    finally:
        await generation_service.aclose()