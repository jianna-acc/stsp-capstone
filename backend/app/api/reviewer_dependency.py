# File: /backend/app/api/reviewer_dependency.py
# Purpose: Builds the reviewer persistence service using the trusted
# backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.reviewer_repository import (
    ReviewerRepository,
)
from app.services.reviewer_service import (
    ReviewerService,
)


def get_reviewer_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> ReviewerService:
    """Build the reviewer persistence service dependency."""

    repository = ReviewerRepository(
        supabase_client,
    )

    return ReviewerService(
        repository,
    )