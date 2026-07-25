# File: /backend/app/database/supabase_client.py
# Purpose: Creates and caches the trusted server-side Supabase
# client used by FastAPI services and feature modules.

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


def create_supabase_client(
    url: str,
    secret_key: str,
) -> Client:
    """Create a trusted Supabase client from validated values."""

    normalized_url = url.strip().rstrip("/")
    normalized_key = secret_key.strip()

    if not normalized_url:
        raise RuntimeError(
            "SUPABASE_URL is not configured."
        )

    if not normalized_url.startswith("https://"):
        raise RuntimeError(
            "SUPABASE_URL must use HTTPS."
        )

    if ".supabase.co" not in normalized_url:
        raise RuntimeError(
            "SUPABASE_URL is not a valid hosted Supabase URL."
        )

    if not normalized_key:
        raise RuntimeError(
            "SUPABASE_SECRET_KEY is not configured."
        )

    if not normalized_key.startswith("sb_secret_"):
        raise RuntimeError(
            "The backend must use a Supabase secret key."
        )

    return create_client(
        normalized_url,
        normalized_key,
    )


@lru_cache
def get_supabase_client() -> Client:
    """Return one cached trusted Supabase client."""

    settings = get_settings()

    return create_supabase_client(
        url=settings.supabase_url,
        secret_key=settings.supabase_secret_key,
    )