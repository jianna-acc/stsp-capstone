# File: /backend/app/api/quiz_dependency.py

# Purpose: Builds the Quiz persistence service using the trusted
# backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.quiz_repository import (
    QuizRepository,
)
from app.services.quiz_service import (
    QuizService,
)


def get_quiz_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> QuizService:
    """Build the Quiz persistence service dependency."""

    repository = QuizRepository(
        supabase_client,
    )

    return QuizService(
        repository,
    )