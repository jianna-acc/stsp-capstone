# File: /backend/tests/test_ai_provider_factory.py
# Purpose: Verifies generation-provider selection without creating
# real external AI clients.

from types import SimpleNamespace
from typing import Any

import pytest

from app.ai import provider_factory
from app.ai.errors import AIProviderConfigurationError


def _settings(
    provider: str,
) -> Any:
    """Return minimal settings for provider-selection tests."""

    return SimpleNamespace(
        ai_provider=provider,
    )


def test_factory_selects_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = object()

    monkeypatch.setattr(
        provider_factory,
        "GeminiProvider",
        lambda settings: marker,
    )

    result = provider_factory.create_generation_provider(
        settings=_settings("gemini"),
    )

    assert result is marker


def test_factory_selects_bedrock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = object()

    monkeypatch.setattr(
        provider_factory,
        "BedrockGenerationProvider",
        lambda settings: marker,
    )

    result = provider_factory.create_generation_provider(
        settings=_settings("bedrock"),
    )

    assert result is marker


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(
        AIProviderConfigurationError,
        match="Unsupported AI generation provider",
    ):
        provider_factory.create_generation_provider(
            settings=_settings("unsupported"),
        )