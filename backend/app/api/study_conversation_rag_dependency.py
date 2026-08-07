# File: /backend/app/api/study_conversation_rag_dependency.py
# Purpose: Builds the conversation-aware RAG service using the
# trusted backend Supabase client and existing RAG orchestration.

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from supabase import Client

from app.api.rag_orchestration_dependency import (
    get_rag_orchestration_service,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.study_conversation_repository import (
    StudyConversationRepository,
)
from app.services.rag_orchestration import (
    RagOrchestrationService,
)
from app.services.study_conversation_rag import (
    StudyConversationRagService,
)


def get_study_conversation_rag_service(
    supabase_client: Annotated[
        Client,
        Depends(
            get_supabase_client,
        ),
    ],
    rag_service: Annotated[
        RagOrchestrationService,
        Depends(
            get_rag_orchestration_service,
        ),
    ],
) -> StudyConversationRagService:
    """Build the conversation-aware grounded-answer service."""

    repository = StudyConversationRepository(
        supabase_client,
    )

    return StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )