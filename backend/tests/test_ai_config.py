# File: /backend/tests/test_ai_config.py
# Purpose: Verifies AI configuration defaults and validation without
# making external Gemini API requests.

from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(
    **overrides: Any,
) -> Settings:
    """Create isolated valid settings without loading the private .env."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "_env_file": None,
    }
    values.update(overrides)

    return Settings(**values)


def test_ai_settings_have_safe_defaults() -> None:
    """AI defaults must not enable paid live requests."""

    settings = build_settings()

    assert settings.ai_provider == "gemini"
    assert settings.gemini_api_key == ""
    assert settings.gemini_generation_model == "gemini-3.6-flash"
    assert settings.gemini_embedding_model == "gemini-embedding-2"
    assert settings.gemini_embedding_dimensions == 768
    assert settings.gemini_generation_temperature == 0.2
    assert settings.gemini_generation_max_output_tokens == 256
    assert settings.gemini_request_timeout_seconds == 30.0
    assert settings.ai_live_smoke_tests_enabled is False


def test_ai_string_settings_are_trimmed() -> None:
    """Accidental spaces must not become part of API configuration."""

    settings = build_settings(
        gemini_api_key="  test-key  ",
        gemini_generation_model="  gemini-3.6-flash  ",
        gemini_embedding_model="  gemini-embedding-2  ",
    )

    assert settings.gemini_api_key == "test-key"
    assert settings.gemini_generation_model == "gemini-3.6-flash"
    assert settings.gemini_embedding_model == "gemini-embedding-2"


@pytest.mark.parametrize(
    "dimensions",
    [
        0,
        127,
        3073,
    ],
)
def test_invalid_embedding_dimensions_are_rejected(
    dimensions: int,
) -> None:
    """Embedding dimensions must remain within the accepted range."""

    with pytest.raises(
        ValidationError,
        match="GEMINI_EMBEDDING_DIMENSIONS",
    ):
        build_settings(
            gemini_embedding_dimensions=dimensions,
        )


@pytest.mark.parametrize(
    "temperature",
    [
        -0.1,
        2.1,
    ],
)
def test_invalid_generation_temperature_is_rejected(
    temperature: float,
) -> None:
    """Generation temperature must remain within its valid range."""

    with pytest.raises(
        ValidationError,
        match="GEMINI_GENERATION_TEMPERATURE",
    ):
        build_settings(
            gemini_generation_temperature=temperature,
        )


@pytest.mark.parametrize(
    "max_output_tokens",
    [
        0,
        8193,
    ],
)
def test_invalid_generation_token_limit_is_rejected(
    max_output_tokens: int,
) -> None:
    """Generation output limits must be positive and controlled."""

    with pytest.raises(
        ValidationError,
        match="GEMINI_GENERATION_MAX_OUTPUT_TOKENS",
    ):
        build_settings(
            gemini_generation_max_output_tokens=max_output_tokens,
        )


@pytest.mark.parametrize(
    "timeout_seconds",
    [
        0,
        120.1,
    ],
)
def test_invalid_gemini_timeout_is_rejected(
    timeout_seconds: float,
) -> None:
    """Gemini requests must use a bounded positive timeout."""

    with pytest.raises(
        ValidationError,
        match="GEMINI_REQUEST_TIMEOUT_SECONDS",
    ):
        build_settings(
            gemini_request_timeout_seconds=timeout_seconds,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "gemini_generation_model",
        "gemini_embedding_model",
    ],
)
def test_empty_ai_model_names_are_rejected(
    field_name: str,
) -> None:
    """Configured Gemini model identifiers must not be empty."""

    with pytest.raises(
        ValidationError,
        match="Gemini model names must not be empty",
    ):
        build_settings(
            **{field_name: "   "},
        )
