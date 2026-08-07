# File: /backend/tests/test_study_conversation_rag_dependency.py
# Purpose: Verifies conversation-aware RAG dependency construction
# without requiring live Supabase or AI provider calls.

from __future__ import annotations

from app.api.study_conversation_rag_dependency import (
    get_study_conversation_rag_service,
)
from app.repositories.study_conversation_repository import (
    StudyConversationRepository,
)
from app.services.study_conversation_rag import (
    StudyConversationRagService,
)


class FakeSupabaseClient:
    """Minimal client used for dependency construction."""


class FakeRagService:
    """Minimal RAG service used for dependency construction."""


def test_dependency_builds_conversation_aware_rag_service() -> None:
    supabase_client = FakeSupabaseClient()
    rag_service = FakeRagService()

    service = get_study_conversation_rag_service(
        supabase_client=supabase_client,
        rag_service=rag_service,
    )

    assert isinstance(
        service,
        StudyConversationRagService,
    )

    repository = service._repository

    assert isinstance(
        repository,
        StudyConversationRepository,
    )

    assert repository._client is supabase_client
    assert service._rag_service is rag_service