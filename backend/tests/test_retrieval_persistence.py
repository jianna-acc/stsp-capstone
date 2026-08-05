# File: /backend/tests/test_retrieval_persistence.py

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.ai.retrieval_contracts import (
    RETRIEVAL_EMBEDDING_DIMENSIONS,
    RetrievalFailureCode,
    RetrievalOutcome,
    RetrievalRequest,
    RetrievalRequestError,
    RetrievalResponseError,
)
from app.ai.retrieval_persistence import (
    RETRIEVAL_RPC_NAME,
    SupabaseRetrievalPersistence,
)
from app.services.supabase_admin import SupabaseAdminService

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

CHUNK_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_embedding() -> tuple[float, ...]:
    values = [0.0] * RETRIEVAL_EMBEDDING_DIMENSIONS
    values[-1] = 1.0

    return tuple(
        values,
    )


def make_request() -> RetrievalRequest:
    return RetrievalRequest(
        user_id=USER_ID,
        query_embedding=make_embedding(),
        match_count=5,
        similarity_threshold=0.65,
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
    )


def make_row() -> dict[str, object]:
    return {
        "chunk_id": str(
            CHUNK_ID,
        ),
        "study_file_id": str(
            FILE_ID,
        ),
        "subject_id": str(
            SUBJECT_ID,
        ),
        "source_name": "Biology Notes.pdf",
        "chunk_index": 2,
        "content": (
            "Photosynthesis converts light energy "
            "into chemical energy."
        ),
        "start_offset": 100,
        "end_offset": 165,
        "chunk_metadata": {
            "page_number": 3,
        },
        "embedding_model": "gemini-embedding-2",
        "similarity_score": 0.92,
    }


class FakeRpcClient:
    """Fake trusted RPC client."""

    def __init__(
        self,
        *,
        response: object = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[
            tuple[str, dict[str, object]]
        ] = []

    async def call_rpc_json(
        self,
        function_name: str,
        payload: dict[str, object],
    ) -> object:
        self.calls.append(
            (
                function_name,
                payload,
            )
        )

        if self.error is not None:
            raise self.error

        return self.response


class RecordingSupabaseAdminService(
    SupabaseAdminService,
):
    """Record calls made through the new public RPC wrapper."""

    def __init__(self) -> None:
        self.calls: list[
            tuple[str, dict[str, object]]
        ] = []

    async def _call_rpc_json(
        self,
        function_name: str,
        payload: dict[str, object],
    ) -> object:
        self.calls.append(
            (
                function_name,
                payload,
            )
        )

        return [
            make_row(),
        ]


def test_search_calls_exact_rpc_and_parses_rows() -> None:
    client = FakeRpcClient(
        response=[
            make_row(),
        ],
    )

    persistence = SupabaseRetrievalPersistence(
        client,
    )

    request = make_request()

    result = asyncio.run(
        persistence.search(
            request,
        )
    )

    assert client.calls == [
        (
            RETRIEVAL_RPC_NAME,
            request.to_rpc_parameters(),
        )
    ]

    assert result.outcome == RetrievalOutcome.MATCHES
    assert result.context_available is True
    assert len(
        result.chunks,
    ) == 1
    assert result.chunks[0].chunk_id == CHUNK_ID
    assert result.chunks[0].similarity_score == 0.92


def test_search_treats_empty_list_as_no_context() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response=[],
        )
    )

    result = asyncio.run(
        persistence.search(
            make_request(),
        )
    )

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.context_available is False
    assert result.chunks == ()


def test_search_treats_none_as_no_context() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response=None,
        )
    )

    result = asyncio.run(
        persistence.search(
            make_request(),
        )
    )

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.chunks == ()


def test_search_supports_object_wrapped_data() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response=SimpleNamespace(
                data=[
                    make_row(),
                ],
            )
        )
    )

    result = asyncio.run(
        persistence.search(
            make_request(),
        )
    )

    assert result.outcome == RetrievalOutcome.MATCHES


def test_search_supports_mapping_wrapped_data() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response={
                "data": [
                    make_row(),
                ],
            }
        )
    )

    result = asyncio.run(
        persistence.search(
            make_request(),
        )
    )

    assert result.outcome == RetrievalOutcome.MATCHES


def test_search_wraps_rpc_failure() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            error=RuntimeError(
                "Controlled RPC failure."
            )
        )
    )

    with pytest.raises(
        RetrievalRequestError,
    ) as error:
        asyncio.run(
            persistence.search(
                make_request(),
            )
        )

    assert (
        error.value.error_code
        == RetrievalFailureCode.REQUEST_FAILED
    )


def test_search_rejects_mapping_without_data() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response={
                "unexpected": "value",
            }
        )
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            persistence.search(
                make_request(),
            )
        )


def test_search_rejects_non_sequence_data() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response={
                "data": {
                    "unexpected": "mapping",
                },
            }
        )
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            persistence.search(
                make_request(),
            )
        )


def test_search_rejects_non_mapping_row() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response=[
                "not a row",
            ]
        )
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            persistence.search(
                make_request(),
            )
        )


def test_search_rejects_response_error_field() -> None:
    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response={
                "data": [],
                "error": {
                    "message": "Controlled RPC error.",
                },
            }
        )
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            persistence.search(
                make_request(),
            )
        )


def test_search_rejects_invalid_rpc_row() -> None:
    invalid_row = make_row()

    del invalid_row["content"]

    persistence = SupabaseRetrievalPersistence(
        FakeRpcClient(
            response=[
                invalid_row,
            ]
        )
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        asyncio.run(
            persistence.search(
                make_request(),
            )
        )


def test_supabase_admin_public_rpc_wrapper_delegates() -> None:
    client = RecordingSupabaseAdminService()

    response = asyncio.run(
        client.call_rpc_json(
            RETRIEVAL_RPC_NAME,
            {
                "p_user_id": str(
                    USER_ID,
                ),
            },
        )
    )

    assert client.calls == [
        (
            RETRIEVAL_RPC_NAME,
            {
                "p_user_id": str(
                    USER_ID,
                ),
            },
        )
    ]

    assert response == [
        make_row(),
    ]