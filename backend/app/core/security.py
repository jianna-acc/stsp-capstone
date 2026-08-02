# File: /backend/app/core/security.py
# Purpose: Protects internal processing endpoints with a
# backend-only API key.

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

processor_key_header = APIKeyHeader(
    name="X-Processor-Key",
    auto_error=False,
)


async def require_processor_key(
    provided_key: Annotated[
        str | None,
        Depends(processor_key_header),
    ],
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> None:
    """Verify the backend-only processor credential."""

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Processor authentication is required.",
        )

    if not compare_digest(
        provided_key,
        settings.processor_internal_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid processor credentials.",
        )
