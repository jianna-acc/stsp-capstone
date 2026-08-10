# File: /backend/app/api/study_plan_generation_dependency.py
# Purpose: Builds the complete Track D generate-and-save
# orchestration dependency without shared-router registration.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.generated_study_plan_repository import (
    GeneratedStudyPlanRepository,
)
from app.repositories.study_scheduler_context_repository import (
    StudySchedulerContextRepository,
)
from app.services.generated_study_plan_service import (
    GeneratedStudyPlanService,
)
from app.services.study_plan_generation_orchestrator import (
    StudyPlanGenerationOrchestrator,
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


def get_study_plan_generation_orchestrator(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> StudyPlanGenerationOrchestrator:
    """Build Track D generation and persistence orchestration."""

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

    generation_service = (
        StudyScheduleGenerationService(
            context_service=context_service,
            scheduler=StudyScheduler(),
        )
    )

    persistence_service = (
        GeneratedStudyPlanService(
            GeneratedStudyPlanRepository(
                supabase_client,
            )
        )
    )

    return StudyPlanGenerationOrchestrator(
        generation_service=generation_service,
        persistence_service=persistence_service,
    )