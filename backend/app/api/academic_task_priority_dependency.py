# File: /backend/app/api/academic_task_priority_dependency.py
# Purpose: Builds the priority-context repository and deterministic
# academic-task priority service used by protected API endpoints.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.academic_task_priority_context_repository import (
    AcademicTaskPriorityContextRepository,
)
from app.services.academic_task_priority_service import (
    AcademicTaskPriorityService,
)


def get_academic_task_priority_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> AcademicTaskPriorityService:
    """Create the academic-task priority service for one request."""

    context_repository = (
        AcademicTaskPriorityContextRepository(
            supabase_client,
        )
    )

    return AcademicTaskPriorityService(
        context_repository,
    )