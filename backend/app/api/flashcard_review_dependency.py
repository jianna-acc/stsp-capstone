# File: /backend/app/api/flashcard_review_dependency.py
# Purpose: Builds Flashcard review persistence dependencies.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.flashcard_review_repository import (
    FlashcardReviewRepository,
)
from app.services.flashcard_review_service import (
    FlashcardReviewService,
)


def get_flashcard_review_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> FlashcardReviewService:
    """Build the Flashcard review service."""

    repository = FlashcardReviewRepository(
        supabase_client,
    )

    return FlashcardReviewService(
        repository,
    )