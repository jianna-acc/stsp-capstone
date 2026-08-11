# File: /backend/app/api/study_plan_dependency.py
# Purpose: Builds the Track D study-plan persistence service
# using the trusted backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.study_plan_repository import (
    StudyPlanRepository,
)
from app.services.study_plan_service import (
    StudyPlanService,
)


def get_study_plan_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> StudyPlanService:
    """Build the study-plan persistence service dependency."""

    repository = StudyPlanRepository(
        supabase_client,
    )

    return StudyPlanService(
        repository,
    )