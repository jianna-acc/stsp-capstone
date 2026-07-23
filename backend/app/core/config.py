# File: /backend/app/core/config.py
# Purpose: Loads typed backend settings from environment variables
# and the backend's private .env file.

from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings instance for the application."""

    return Settings()