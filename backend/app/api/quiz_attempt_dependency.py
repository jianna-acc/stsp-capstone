# File: /backend/app/api/quiz_attempt_dependency.py

# Purpose: Builds the Quiz-attempt application service using the
# trusted backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.quiz_attempt_repository import (
    QuizAttemptRepository,
)
from app.services.quiz_attempt_service import (
    QuizAttemptService,
)


def get_quiz_attempt_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> QuizAttemptService:
    """Build the Quiz-attempt service dependency."""

    repository = QuizAttemptRepository(
        supabase_client,
    )

    return QuizAttemptService(
        repository,
    )