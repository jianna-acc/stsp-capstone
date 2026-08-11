# File: /backend/app/api/study_schedule_generation_dependency.py
# Purpose: Builds the independent Track D schedule-generation
# orchestration service using existing onboarding context.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.study_scheduler_context_repository import (
    StudySchedulerContextRepository,
)
from app.services.study_schedule_generation_service import (
    StudyScheduleGenerationService,
)
from app.services.study_scheduler import (
    StudyScheduler,
)
from app.services.study_scheduler_context_service import (
    StudySchedulerContextService,
)


def get_study_schedule_generation_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> StudyScheduleGenerationService:
    """Build the Track D schedule-generation service."""

    context_repository = (
        StudySchedulerContextRepository(
            supabase_client,
        )
    )

    context_service = (
        StudySchedulerContextService(
            context_repository,
        )
    )

    scheduler = StudyScheduler()

    return StudyScheduleGenerationService(
        context_service=context_service,
        scheduler=scheduler,
    )