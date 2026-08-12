# File: /backend/tests/test_flashcard_quiz_provider_compatibility.py
# Purpose: Verifies Flashcard and Quiz generation use the shared
# AI provider factory for both Gemini and Amazon Bedrock.

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.api.flashcard_orchestration_dependency import (
    get_flashcard_orchestration_service,
)
from app.api.quiz_orchestration_dependency import (
    get_quiz_orchestration_service,
)
from app.core.config import Settings


class FakeClosableGenerationProvider:
    """Provide a controllable generation provider for dependency tests."""

    def __init__(
        self,
        provider_name: str,
    ) -> None:
        self._provider_name = provider_name
        self.closed = False

    @property
    def provider_name(self) -> str:
        """Return the configured fake provider name."""

        return self._provider_name

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Generation should never run in these wiring tests."""

        raise AssertionError(
            "Generation should not run in provider wiring tests."
        )

    async def aclose(self) -> None:
        """Record provider cleanup."""

        self.closed = True


async def _exercise_flashcard_dependency(
    settings: Settings,
) -> None:
    """Create and close one Flashcard orchestration dependency."""

    dependency = get_flashcard_orchestration_service(
        settings=settings,
        flashcard_service=object(),  # type: ignore[arg-type]
    )

    await anext(
        dependency,
    )

    await dependency.aclose()


async def _exercise_quiz_dependency(
    settings: Settings,
) -> None:
    """Create and close one Quiz orchestration dependency."""

    dependency = get_quiz_orchestration_service(
        settings=settings,
        quiz_service=object(),  # type: ignore[arg-type]
    )

    await anext(
        dependency,
    )

    await dependency.aclose()


@pytest.mark.parametrize(
    "provider_name",
    (
        "gemini",
        "bedrock",
    ),
)
def test_flashcard_dependency_supports_configured_generation_provider(
    provider_name: str,
) -> None:
    """Flashcards must select Gemini or Bedrock through the factory."""

    settings = Settings(
        ai_provider=provider_name,
    )

    provider = FakeClosableGenerationProvider(
        provider_name,
    )

    with (
        patch(
            "app.ai.provider_factory.GeminiProvider",
            return_value=provider,
        ) as gemini_provider,
        patch(
            "app.ai.provider_factory.BedrockGenerationProvider",
            return_value=provider,
        ) as bedrock_provider,
        patch(
            "app.api.flashcard_orchestration_dependency."
            "SupabaseAdminService"
        ),
        patch(
            "app.api.flashcard_orchestration_dependency."
            "FlashcardSourceLoader"
        ),
        patch(
            "app.api.flashcard_orchestration_dependency."
            "FlashcardOrchestrationService",
            return_value=object(),
        ),
    ):
        asyncio.run(
            _exercise_flashcard_dependency(
                settings,
            )
        )

    if provider_name == "gemini":
        gemini_provider.assert_called_once_with(
            settings=settings,
        )
        bedrock_provider.assert_not_called()

    else:
        bedrock_provider.assert_called_once_with(
            settings=settings,
        )
        gemini_provider.assert_not_called()

    assert provider.closed is True


@pytest.mark.parametrize(
    "provider_name",
    (
        "gemini",
        "bedrock",
    ),
)
def test_quiz_dependency_supports_configured_generation_provider(
    provider_name: str,
) -> None:
    """Quizzes must select Gemini or Bedrock through the factory."""

    settings = Settings(
        ai_provider=provider_name,
    )

    provider = FakeClosableGenerationProvider(
        provider_name,
    )

    with (
        patch(
            "app.ai.provider_factory.GeminiProvider",
            return_value=provider,
        ) as gemini_provider,
        patch(
            "app.ai.provider_factory.BedrockGenerationProvider",
            return_value=provider,
        ) as bedrock_provider,
        patch(
            "app.api.quiz_orchestration_dependency."
            "SupabaseAdminService"
        ),
        patch(
            "app.api.quiz_orchestration_dependency."
            "QuizSourceLoader"
        ),
        patch(
            "app.api.quiz_orchestration_dependency."
            "QuizOrchestrationService",
            return_value=object(),
        ),
    ):
        asyncio.run(
            _exercise_quiz_dependency(
                settings,
            )
        )

    if provider_name == "gemini":
        gemini_provider.assert_called_once_with(
            settings=settings,
        )
        bedrock_provider.assert_not_called()

    else:
        bedrock_provider.assert_called_once_with(
            settings=settings,
        )
        gemini_provider.assert_not_called()

    assert provider.closed is True