# File: /backend/tests/test_supabase_ai_chunk_persistence.py
# Purpose: Tests trusted AI-chunk RPC persistence and return-count
# validation without making live Supabase database requests.

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.ai.vector_persistence import (
    AI_VECTOR_DIMENSIONS,
    AIChunkEmbeddingRecord,
    AIChunkPersistencePayload,
)
from app.core.config import Settings
from app.services.supabase_admin import (
    SupabaseAdminError,
    SupabaseAdminService,
)

STUDY_FILE_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)


def make_service() -> SupabaseAdminService:
    """Create a service without reading private environment data."""

    settings = cast(
        Settings,
        SimpleNamespace(
            supabase_url=("https://example.supabase.co"),
            supabase_secret_key=("test-secret-key"),
            request_timeout_seconds=8.0,
        ),
    )

    return SupabaseAdminService(
        settings=settings,
    )


def make_payload(
    *,
    chunk_count: int = 2,
) -> AIChunkPersistencePayload:
    """Create one already-validated persistence payload."""

    records: list[AIChunkEmbeddingRecord] = []

    current_offset = 0

    for chunk_index in range(
        chunk_count,
    ):
        content = f"Chunk {chunk_index}"

        record = AIChunkEmbeddingRecord(
            chunk_index=chunk_index,
            content=content,
            start_offset=current_offset,
            end_offset=(current_offset + len(content)),
            source_name="lecture.txt",
            embedding=tuple(
                0.125
                for _ in range(
                    AI_VECTOR_DIMENSIONS,
                )
            ),
            metadata={
                "chunk_key": (f"{STUDY_FILE_ID}:{chunk_index}"),
                "material_id": str(
                    STUDY_FILE_ID,
                ),
            },
        )

        records.append(
            record,
        )

        current_offset = record.end_offset

    return AIChunkPersistencePayload(
        study_file_id=STUDY_FILE_ID,
        embedding_model=("gemini-embedding-2"),
        embedding_dimensions=(AI_VECTOR_DIMENSIONS),
        original_character_count=(current_offset),
        records=tuple(
            records,
        ),
    )


def test_persists_ai_chunks_through_expected_rpc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The service must send the validated RPC payload."""

    service = make_service()
    payload = make_payload()

    rpc_mock = AsyncMock(
        return_value=payload.chunk_count,
    )

    monkeypatch.setattr(
        service,
        "_call_rpc_json",
        rpc_mock,
    )

    stored_count = asyncio.run(
        service.persist_ai_chunks(
            payload=payload,
        ),
    )

    assert stored_count == 2

    rpc_mock.assert_awaited_once_with(
        function_name=("replace_study_file_ai_chunks"),
        payload=payload.to_rpc_payload(),
    )


def test_rejects_missing_rpc_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty RPC response cannot confirm persistence."""

    service = make_service()
    payload = make_payload()

    monkeypatch.setattr(
        service,
        "_call_rpc_json",
        AsyncMock(
            return_value=None,
        ),
    )

    with pytest.raises(
        SupabaseAdminError,
        match=("invalid AI-chunk persistence count"),
    ):
        asyncio.run(
            service.persist_ai_chunks(
                payload=payload,
            ),
        )


@pytest.mark.parametrize(
    "response_data",
    [
        True,
        "2",
        2.0,
        [2],
        {
            "count": 2,
        },
    ],
)
def test_rejects_noninteger_rpc_count(
    monkeypatch: pytest.MonkeyPatch,
    response_data: Any,
) -> None:
    """The scalar database result must be a JSON integer."""

    service = make_service()
    payload = make_payload()

    monkeypatch.setattr(
        service,
        "_call_rpc_json",
        AsyncMock(
            return_value=response_data,
        ),
    )

    with pytest.raises(
        SupabaseAdminError,
        match=("invalid AI-chunk persistence count"),
    ):
        asyncio.run(
            service.persist_ai_chunks(
                payload=payload,
            ),
        )


def test_rejects_negative_rpc_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The database cannot report a negative stored count."""

    service = make_service()
    payload = make_payload()

    monkeypatch.setattr(
        service,
        "_call_rpc_json",
        AsyncMock(
            return_value=-1,
        ),
    )

    with pytest.raises(
        SupabaseAdminError,
        match=("negative AI-chunk persistence count"),
    ):
        asyncio.run(
            service.persist_ai_chunks(
                payload=payload,
            ),
        )


def test_rejects_unexpected_rpc_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stored count must match the requested chunks."""

    service = make_service()
    payload = make_payload(
        chunk_count=2,
    )

    monkeypatch.setattr(
        service,
        "_call_rpc_json",
        AsyncMock(
            return_value=1,
        ),
    )

    with pytest.raises(
        SupabaseAdminError,
        match=("Expected 2, received 1"),
    ):
        asyncio.run(
            service.persist_ai_chunks(
                payload=payload,
            ),
        )
