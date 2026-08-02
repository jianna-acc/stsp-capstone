# File: /backend/app/core/config.py
# Purpose: Loads and validates typed backend settings from
# environment variables and the backend's private .env file.

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BACKEND_DIRECTORY / ".env"


class Settings(BaseSettings):
    """Shared configuration used throughout the FastAPI backend."""

    app_name: str = "STS Capstone API"
    app_version: str = "0.1.0"

    environment: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    api_prefix: str = "/api"
    frontend_url: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_secret_key: str = ""

    processor_internal_key: str = ""

    study_materials_bucket: str = "study-materials"

    request_timeout_seconds: float = 30.0
    max_processing_file_bytes: int = 20 * 1024 * 1024

    ai_provider: Literal["gemini"] = "gemini"

    gemini_api_key: str = ""
    gemini_generation_model: str = "gemini-3.6-flash"
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_embedding_dimensions: int = 768

    gemini_generation_temperature: float = 0.2
    gemini_generation_max_output_tokens: int = 256
    gemini_request_timeout_seconds: float = 30.0

    ai_live_smoke_tests_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(
        cls,
        value: str,
    ) -> str:
        """Normalize and validate the Supabase project URL."""

        normalized = value.strip().rstrip("/")

        if not normalized:
            raise ValueError(
                "SUPABASE_URL is required.",
            )

        if not normalized.startswith(
            ("https://", "http://"),
        ):
            raise ValueError(
                "SUPABASE_URL must start with http:// or https://.",
            )

        return normalized

    @field_validator("supabase_secret_key")
    @classmethod
    def validate_supabase_secret_key(
        cls,
        value: str,
    ) -> str:
        """Ensure a backend-only Supabase secret was provided."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "SUPABASE_SECRET_KEY is required.",
            )

        if not normalized.startswith(
            ("sb_secret_", "eyJ"),
        ):
            raise ValueError(
                "SUPABASE_SECRET_KEY must be a Supabase secret "
                "key or legacy service-role key.",
            )

        return normalized

    @field_validator("processor_internal_key")
    @classmethod
    def validate_processor_internal_key(
        cls,
        value: str,
    ) -> str:
        """Ensure the private processor endpoint has a strong key."""

        normalized = value.strip()

        if len(normalized) < 32:
            raise ValueError(
                "PROCESSOR_INTERNAL_KEY must contain at least 32 characters.",
            )

        return normalized

    @field_validator("request_timeout_seconds")
    @classmethod
    def validate_request_timeout(
        cls,
        value: float,
    ) -> float:
        """Prevent invalid or excessive HTTP timeouts."""

        if value <= 0 or value > 120:
            raise ValueError(
                "REQUEST_TIMEOUT_SECONDS must be between 0 and 120.",
            )

        return value

    @field_validator("max_processing_file_bytes")
    @classmethod
    def validate_processing_limit(
        cls,
        value: int,
    ) -> int:
        """Ensure the backend processing limit is positive."""

        if value <= 0:
            raise ValueError(
                "MAX_PROCESSING_FILE_BYTES must be greater than 0.",
            )

        return value

    @field_validator(
        "gemini_api_key",
        "gemini_generation_model",
        "gemini_embedding_model",
    )
    @classmethod
    def strip_ai_string_settings(
        cls,
        value: str,
    ) -> str:
        """Remove accidental surrounding spaces from AI settings."""

        return value.strip()

    @field_validator(
        "gemini_generation_model",
        "gemini_embedding_model",
    )
    @classmethod
    def validate_ai_model_name(
        cls,
        value: str,
    ) -> str:
        """Ensure configured Gemini model names are not empty."""

        if not value:
            raise ValueError(
                "Gemini model names must not be empty.",
            )

        return value

    @field_validator("gemini_embedding_dimensions")
    @classmethod
    def validate_embedding_dimensions(
        cls,
        value: int,
    ) -> int:
        """Limit embedding vectors to supported practical sizes."""

        if value < 128 or value > 3072:
            raise ValueError(
                "GEMINI_EMBEDDING_DIMENSIONS must be between 128 and 3072.",
            )

        return value

    @field_validator("gemini_generation_temperature")
    @classmethod
    def validate_generation_temperature(
        cls,
        value: float,
    ) -> float:
        """Prevent invalid generation temperature values."""

        if value < 0 or value > 2:
            raise ValueError(
                "GEMINI_GENERATION_TEMPERATURE must be between 0 and 2.",
            )

        return value

    @field_validator("gemini_generation_max_output_tokens")
    @classmethod
    def validate_generation_token_limit(
        cls,
        value: int,
    ) -> int:
        """Keep generated smoke-test responses intentionally small."""

        if value < 1 or value > 8192:
            raise ValueError(
                "GEMINI_GENERATION_MAX_OUTPUT_TOKENS must be between 1 and 8192.",
            )

        return value

    @field_validator("gemini_request_timeout_seconds")
    @classmethod
    def validate_gemini_request_timeout(
        cls,
        value: float,
    ) -> float:
        """Prevent invalid or excessive Gemini request timeouts."""

        if value <= 0 or value > 120:
            raise ValueError(
                "GEMINI_REQUEST_TIMEOUT_SECONDS must be between 0 and 120.",
            )

        return value


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings instance for the application."""

    return Settings()
