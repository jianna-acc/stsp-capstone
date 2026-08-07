# File: /backend/tests/test_study_conversation_dependency.py
# Purpose: Verifies construction of the Study Conversation service
# dependency without requiring a live Supabase connection.

from app.api.study_conversation_dependency import (
    get_study_conversation_service,
)
from app.repositories.study_conversation_repository import (
    StudyConversationRepository,
)
from app.services.study_conversation_service import (
    StudyConversationService,
)


class FakeSupabaseClient:
    """Minimal client used only for dependency construction."""


def test_dependency_builds_conversation_service() -> None:
    client = FakeSupabaseClient()

    service = get_study_conversation_service(
        client,
    )

    assert isinstance(
        service,
        StudyConversationService,
    )

    repository = service._repository

    assert isinstance(
        repository,
        StudyConversationRepository,
    )

    assert repository._client is client