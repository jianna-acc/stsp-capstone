# File: /backend/app/ai/provider_factory.py
# Purpose: Selects the configured text-generation provider while keeping
# feature services independent from concrete AI vendors.

from app.ai.contracts import GenerationProvider
from app.ai.errors import AIProviderConfigurationError
from app.ai.providers import (
    BedrockGenerationProvider,
    GeminiProvider,
)
from app.core.config import Settings, get_settings


def create_generation_provider(
    settings: Settings | None = None,
) -> GenerationProvider:
    """Create the configured text-generation provider."""

    resolved_settings = settings or get_settings()

    if resolved_settings.ai_provider == "gemini":
        return GeminiProvider(
            settings=resolved_settings,
        )

    if resolved_settings.ai_provider == "bedrock":
        return BedrockGenerationProvider(
            settings=resolved_settings,
        )

    raise AIProviderConfigurationError(
        "Unsupported AI generation provider: "
        f"{resolved_settings.ai_provider}",
    )