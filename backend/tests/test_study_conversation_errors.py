# File: /backend/tests/test_study_conversation_errors.py
# Purpose: Verifies the Study Conversation domain-error hierarchy.

import pytest

from app.services.study_conversation_errors import (
    StudyConversationError,
    StudyConversationNotFoundError,
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
)


@pytest.mark.parametrize(
    "error_type",
    (
        StudyConversationValidationError,
        StudyConversationNotFoundError,
        StudyConversationPersistenceError,
        StudyConversationResponseError,
    ),
)
def test_conversation_errors_share_base_type(
    error_type: type[
        StudyConversationError
    ],
) -> None:
    error = error_type(
        "Controlled conversation error.",
    )

    assert isinstance(
        error,
        StudyConversationError,
    )

    assert str(
        error,
    ) == "Controlled conversation error."