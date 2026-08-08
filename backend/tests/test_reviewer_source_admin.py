# File: /backend/tests/test_reviewer_source_admin.py
# Purpose: Verifies trusted Supabase reads used for
# reviewer source-material loading.

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, Self
from uuid import uuid4

import pytest

import app.services.supabase_admin as supabase_admin_module
from app.services.supabase_admin import (
    SupabaseAdminError,
    SupabaseAdminService,
)

P = ParamSpec("P")


def async_test(
    function: Callable[
        P,
        Coroutine[Any, Any, None],
    ],
) -> Callable[
    P,
    None,
]:
    """Run an async test without an external pytest plugin."""

    @wraps(
        function,
    )
    def wrapper(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        asyncio.run(
            function(
                *args,
                **kwargs,
            )
        )

    return wrapper


class FakeSettings:
    """Minimum settings required by SupabaseAdminService."""

    supabase_url = "https://example.supabase.co"
    supabase_secret_key = "backend-test-secret"
    request_timeout_seconds = 30


class FakeResponse:
    """Minimal HTTP response used by trusted-read tests."""

    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: object = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(
        self,
    ) -> object:
        return self._payload


def _install_http_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    response: FakeResponse,
) -> dict[str, object]:
    """Install a recording async HTTP client."""

    recorded: dict[
        str,
        object,
    ] = {}

    class FakeAsyncClient:
        def __init__(
            self,
            *,
            timeout: object,
            **_: object,
        ) -> None:
            recorded[
                "timeout"
            ] = timeout

        async def __aenter__(
            self,
        ) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: object,
            exc: object,
            traceback: object,
        ) -> None:
            return None

        async def get(
            self,
            endpoint: str,
            *,
            params: object,
            headers: object,
        ) -> FakeResponse:
            recorded[
                "endpoint"
            ] = endpoint

            recorded[
                "params"
            ] = params

            recorded[
                "headers"
            ] = headers

            return response

    monkeypatch.setattr(
        supabase_admin_module.httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    return recorded


@async_test
async def test_list_ready_subject_files_filters_scope_and_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Subject loading must filter owner, subject, and ready state."""

    user_id = uuid4()
    subject_id = uuid4()

    payload = [
        {
            "id": str(
                uuid4(),
            ),
            "user_id": str(
                user_id,
            ),
            "subject_id": str(
                subject_id,
            ),
            "original_filename": "Week 1.pdf",
            "processing_status": "ready",
            "created_at": "2026-08-01T00:00:00+00:00",
        }
    ]

    recorded = _install_http_client(
        monkeypatch,
        response=FakeResponse(
            payload=payload,
        ),
    )

    service = SupabaseAdminService(
        settings=FakeSettings(),
    )

    result = (
        await service.list_ready_study_files_for_subject(
            user_id=user_id,
            subject_id=subject_id,
        )
    )

    assert result == payload

    assert recorded[
        "endpoint"
    ] == (
        "https://example.supabase.co"
        "/rest/v1/study_files"
    )

    params = recorded[
        "params"
    ]

    assert isinstance(
        params,
        dict,
    )

    assert params[
        "user_id"
    ] == f"eq.{user_id}"

    assert params[
        "subject_id"
    ] == f"eq.{subject_id}"

    assert params[
        "processing_status"
    ] == "eq.ready"

    assert params[
        "order"
    ] == "created_at.asc,id.asc"


@async_test
async def test_list_study_file_chunks_filters_owner_and_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chunk loading must be user scoped and ordered."""

    user_id = uuid4()
    study_file_id = uuid4()

    payload = [
        {
            "study_file_id": str(
                study_file_id,
            ),
            "chunk_index": 0,
            "content": "First section",
            "locator_type": "page",
            "locator_label": "Page 1",
        },
        {
            "study_file_id": str(
                study_file_id,
            ),
            "chunk_index": 1,
            "content": "Second section",
            "locator_type": "page",
            "locator_label": "Page 2",
        },
    ]

    recorded = _install_http_client(
        monkeypatch,
        response=FakeResponse(
            payload=payload,
        ),
    )

    service = SupabaseAdminService(
        settings=FakeSettings(),
    )

    result = await service.list_study_file_chunks(
        user_id=user_id,
        study_file_id=study_file_id,
    )

    assert result == payload

    assert recorded[
        "endpoint"
    ] == (
        "https://example.supabase.co"
        "/rest/v1/study_file_chunks"
    )

    params = recorded[
        "params"
    ]

    assert isinstance(
        params,
        dict,
    )

    assert params[
        "user_id"
    ] == f"eq.{user_id}"

    assert params[
        "study_file_id"
    ] == f"eq.{study_file_id}"

    assert params[
        "order"
    ] == "chunk_index.asc"


@async_test
async def test_subject_file_lookup_rejects_invalid_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed PostgREST data must fail safely."""

    _install_http_client(
        monkeypatch,
        response=FakeResponse(
            payload={
                "unexpected": "object",
            },
        ),
    )

    service = SupabaseAdminService(
        settings=FakeSettings(),
    )

    with pytest.raises(
        SupabaseAdminError,
    ):
        await service.list_ready_study_files_for_subject(
            user_id=uuid4(),
            subject_id=uuid4(),
        )


@async_test
async def test_chunk_lookup_rejects_invalid_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every returned chunk must be a mapping row."""

    _install_http_client(
        monkeypatch,
        response=FakeResponse(
            payload=[
                "invalid-row",
            ],
        ),
    )

    service = SupabaseAdminService(
        settings=FakeSettings(),
    )

    with pytest.raises(
        SupabaseAdminError,
    ):
        await service.list_study_file_chunks(
            user_id=uuid4(),
            study_file_id=uuid4(),
        )


@async_test
async def test_chunk_lookup_handles_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-success Supabase responses must become controlled errors."""

    _install_http_client(
        monkeypatch,
        response=FakeResponse(
            status_code=500,
            payload=None,
            text="internal error",
        ),
    )

    service = SupabaseAdminService(
        settings=FakeSettings(),
    )

    with pytest.raises(
        SupabaseAdminError,
    ):
        await service.list_study_file_chunks(
            user_id=uuid4(),
            study_file_id=uuid4(),
        )