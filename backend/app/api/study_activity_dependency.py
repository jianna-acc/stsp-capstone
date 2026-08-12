# File: /backend/app/api/study_activity_dependency.py
# Purpose: Builds the Study Activity timer service using the
# trusted backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.study_activity_repository import (
    StudyActivityRepository,
)
from app.services.study_activity_service import (
    StudyActivityService,
)


def get_study_activity_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> StudyActivityService:
    """Build the actual Study Activity timer service dependency."""

    repository = StudyActivityRepository(
        supabase_client,
    )

    return StudyActivityService(
        repository,
    )