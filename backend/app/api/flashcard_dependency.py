# File: /backend/app/api/flashcard_dependency.py
# Purpose: Builds the Flashcard persistence service using the
# trusted backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.flashcard_repository import (
    FlashcardRepository,
)
from app.services.flashcard_service import (
    FlashcardService,
)


def get_flashcard_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> FlashcardService:
    """Build the Flashcard persistence service dependency."""

    repository = FlashcardRepository(
        supabase_client,
    )

    return FlashcardService(
        repository,
    )