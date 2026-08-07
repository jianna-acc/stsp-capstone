# File: /backend/app/api/authenticated_user_dependency.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from starlette.concurrency import run_in_threadpool
from supabase import Client

from app.database.supabase_client import (
    get_supabase_client,
)

AUTHENTICATION_REQUIRED_MESSAGE = (
    "Student authentication is required."
)

INVALID_AUTHENTICATION_MESSAGE = (
    "The authentication token is invalid or expired."
)


student_bearer_scheme = HTTPBearer(
    auto_error=False,
)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Safe identity resolved from a Supabase access token."""

    user_id: UUID


async def require_authenticated_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(student_bearer_scheme),
    ],
    supabase_client: Annotated[
        Client,
        Depends(get_supabase_client),
    ],
) -> AuthenticatedUser:
    """Validate a student bearer token through Supabase Auth."""

    if credentials is None:
        raise _unauthorized(
            AUTHENTICATION_REQUIRED_MESSAGE,
        )

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized(
            AUTHENTICATION_REQUIRED_MESSAGE,
        )

    access_token = credentials.credentials.strip()

    if not access_token:
        raise _unauthorized(
            AUTHENTICATION_REQUIRED_MESSAGE,
        )

    try:
        auth_response = await run_in_threadpool(
            supabase_client.auth.get_user,
            access_token,
        )
    except Exception as exc:
        raise _unauthorized(
            INVALID_AUTHENTICATION_MESSAGE,
        ) from exc

    authenticated_user = getattr(
        auth_response,
        "user",
        None,
    )

    raw_user_id = getattr(
        authenticated_user,
        "id",
        None,
    )

    try:
        user_id = UUID(
            str(
                raw_user_id,
            )
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        raise _unauthorized(
            INVALID_AUTHENTICATION_MESSAGE,
        ) from exc

    return AuthenticatedUser(
        user_id=user_id,
    )


def _unauthorized(
    message: str,
) -> HTTPException:
    """Create a consistent bearer-authentication failure."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )
