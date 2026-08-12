# File: /backend/app/api/reviewer_orchestration_dependency.py
# Purpose: Assembles reviewer source loading, AI generation,
# and persistence into one FastAPI dependency.

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.ai.provider_factory import create_generation_provider
from app.api.reviewer_dependency import (
    get_reviewer_service,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.services.reviewer_generation import (
    ReviewerGenerationService,
)
from app.services.reviewer_orchestration import (
    ReviewerOrchestrationService,
)
from app.services.reviewer_service import (
    ReviewerService,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceLoader,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)


async def get_reviewer_orchestration_service(
    settings: Annotated[
        Settings,
        Depends(
            get_settings,
        ),
    ],
    reviewer_service: Annotated[
        ReviewerService,
        Depends(
            get_reviewer_service,
        ),
    ],
) -> AsyncIterator[
    ReviewerOrchestrationService
]:
    """Build the complete reviewer-generation workflow."""

    provider = create_generation_provider(
        settings=settings,
    )

    generation_service = ReviewerGenerationService(
        provider=provider,
    )

    admin_service = SupabaseAdminService(
        settings=settings,
    )

    source_loader = ReviewerSourceLoader(
        admin_service,
    )

    orchestration_service = (
        ReviewerOrchestrationService(
            source_loader=source_loader,
            generation_service=generation_service,
            reviewer_service=reviewer_service,
        )
    )

    try:
        yield orchestration_service

    finally:
        await generation_service.aclose()