# File: /backend/app/api/study_conversation_dependency.py
# Purpose: Builds the Study Conversation service using the trusted
# backend Supabase client.

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.study_conversation_repository import (
    StudyConversationRepository,
)
from app.services.study_conversation_service import (
    StudyConversationService,
)


def get_study_conversation_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
) -> StudyConversationService:
    """Build the Study Conversation service dependency."""

    repository = StudyConversationRepository(
        supabase_client,
    )

    return StudyConversationService(
        repository,
    )