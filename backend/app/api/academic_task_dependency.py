# File: /backend/app/api/academic_task_dependency.py
# Purpose: Builds the academic-task repository and service used
# by protected FastAPI academic-task endpoints.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.academic_task_repository import (
    AcademicTaskRepository,
)
from app.services.academic_task_service import (
    AcademicTaskService,
)


def get_academic_task_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> AcademicTaskService:
    """Create the academic-task service for one API request."""

    repository = AcademicTaskRepository(
        supabase_client,
    )

    return AcademicTaskService(
        repository,
    )