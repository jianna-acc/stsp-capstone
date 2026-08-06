# File: /backend/tests/test_authenticated_user_dependency.py

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.authenticated_user_dependency import (
    AUTHENTICATION_REQUIRED_MESSAGE,
    INVALID_AUTHENTICATION_MESSAGE,
    AuthenticatedUser,
    require_authenticated_user,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)


class FakeSupabaseAuth:
    """Fake synchronous Supabase Auth client."""

    def __init__(
        self,
        *,
        response: object | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.received_tokens: list[str | None] = []

    def get_user(
        self,
        jwt: str | None = None,
    ) -> object | None:
        """Return a controlled authentication response."""

        self.received_tokens.append(
            jwt,
        )

        if self.error is not None:
            raise self.error

        return self.response


class FakeSupabaseClient:
    """Fake client exposing the Supabase Auth interface."""

    def __init__(
        self,
        auth: FakeSupabaseAuth,
    ) -> None:
        self.auth = auth


def make_credentials(
    *,
    scheme: str = "Bearer",
    token: str = "valid-access-token",
) -> HTTPAuthorizationCredentials:
    """Create controlled HTTP authorization credentials."""

    return HTTPAuthorizationCredentials(
        scheme=scheme,
        credentials=token,
    )


def make_user_response(
    *,
    user_id: object = USER_ID,
) -> object:
    """Create a response matching UserResponse.user.id."""

    return SimpleNamespace(
        user=SimpleNamespace(
            id=user_id,
        ),
    )


def test_dependency_returns_authenticated_user() -> None:
    auth = FakeSupabaseAuth(
        response=make_user_response(),
    )

    result = asyncio.run(
        require_authenticated_user(
            credentials=make_credentials(),
            supabase_client=FakeSupabaseClient(
                auth,
            ),
        )
    )

    assert result == AuthenticatedUser(
        user_id=USER_ID,
    )

    assert auth.received_tokens == [
        "valid-access-token",
    ]


def test_dependency_accepts_string_user_id() -> None:
    auth = FakeSupabaseAuth(
        response=make_user_response(
            user_id=str(
                USER_ID,
            ),
        ),
    )

    result = asyncio.run(
        require_authenticated_user(
            credentials=make_credentials(),
            supabase_client=FakeSupabaseClient(
                auth,
            ),
        )
    )

    assert result.user_id == USER_ID


def test_dependency_rejects_missing_credentials() -> None:
    auth = FakeSupabaseAuth(
        response=make_user_response(),
    )

    with pytest.raises(
        HTTPException,
    ) as error:
        asyncio.run(
            require_authenticated_user(
                credentials=None,
                supabase_client=FakeSupabaseClient(
                    auth,
                ),
            )
        )

    assert (
        error.value.status_code
        == status.HTTP_401_UNAUTHORIZED
    )

    assert (
        error.value.detail
        == AUTHENTICATION_REQUIRED_MESSAGE
    )

    assert error.value.headers == {
        "WWW-Authenticate": "Bearer",
    }

    assert auth.received_tokens == []


def test_dependency_rejects_non_bearer_scheme() -> None:
    auth = FakeSupabaseAuth(
        response=make_user_response(),
    )

    with pytest.raises(
        HTTPException,
    ) as error:
        asyncio.run(
            require_authenticated_user(
                credentials=make_credentials(
                    scheme="Basic",
                ),
                supabase_client=FakeSupabaseClient(
                    auth,
                ),
            )
        )

    assert (
        error.value.status_code
        == status.HTTP_401_UNAUTHORIZED
    )

    assert (
        error.value.detail
        == AUTHENTICATION_REQUIRED_MESSAGE
    )

    assert auth.received_tokens == []


def test_dependency_rejects_empty_token() -> None:
    auth = FakeSupabaseAuth(
        response=make_user_response(),
    )

    with pytest.raises(
        HTTPException,
    ) as error:
        asyncio.run(
            require_authenticated_user(
                credentials=make_credentials(
                    token="   ",
                ),
                supabase_client=FakeSupabaseClient(
                    auth,
                ),
            )
        )

    assert (
        error.value.status_code
        == status.HTTP_401_UNAUTHORIZED
    )

    assert (
        error.value.detail
        == AUTHENTICATION_REQUIRED_MESSAGE
    )

    assert auth.received_tokens == []


def test_dependency_rejects_auth_client_failure() -> None:
    auth = FakeSupabaseAuth(
        error=RuntimeError(
            "Controlled Supabase Auth failure.",
        ),
    )

    with pytest.raises(
        HTTPException,
    ) as error:
        asyncio.run(
            require_authenticated_user(
                credentials=make_credentials(),
                supabase_client=FakeSupabaseClient(
                    auth,
                ),
            )
        )

    assert (
        error.value.status_code
        == status.HTTP_401_UNAUTHORIZED
    )

    assert (
        error.value.detail
        == INVALID_AUTHENTICATION_MESSAGE
    )

    assert error.value.headers == {
        "WWW-Authenticate": "Bearer",
    }


@pytest.mark.parametrize(
    "response",
    [
        None,
        SimpleNamespace(
            user=None,
        ),
        SimpleNamespace(
            user=SimpleNamespace(
                id=None,
            ),
        ),
        SimpleNamespace(
            user=SimpleNamespace(
                id="not-a-uuid",
            ),
        ),
    ],
)
def test_dependency_rejects_invalid_user_response(
    response: object | None,
) -> None:
    auth = FakeSupabaseAuth(
        response=response,
    )

    with pytest.raises(
        HTTPException,
    ) as error:
        asyncio.run(
            require_authenticated_user(
                credentials=make_credentials(),
                supabase_client=FakeSupabaseClient(
                    auth,
                ),
            )
        )

    assert (
        error.value.status_code
        == status.HTTP_401_UNAUTHORIZED
    )

    assert (
        error.value.detail
        == INVALID_AUTHENTICATION_MESSAGE
    )


def test_authenticated_user_contains_no_token() -> None:
    authenticated_user = AuthenticatedUser(
        user_id=USER_ID,
    )

    assert authenticated_user.user_id == USER_ID
    assert not hasattr(
        authenticated_user,
        "access_token",
    )
    assert not hasattr(
        authenticated_user,
        "token",
    )
