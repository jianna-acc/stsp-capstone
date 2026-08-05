# File: /backend/app/ai/retrieval_persistence.py

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from httpx import HTTPError
from postgrest.exceptions import APIError as PostgrestAPIError

from app.ai.retrieval_contracts import (
    RetrievalRequest,
    RetrievalRequestError,
    RetrievalResponseError,
    RetrievalResult,
    RetrievalValidationError,
    RetrievedStudyChunk,
)

RETRIEVAL_RPC_NAME = "search_study_file_ai_chunks"

_MISSING = object()


class RetrievalRpcClient(Protocol):
    """Trusted client behavior needed for retrieval."""

    async def call_rpc_json(
        self,
        function_name: str,
        payload: dict[str, object],
    ) -> object:
        """Call a trusted RPC and return its decoded JSON response."""


class RetrievalPersistence(Protocol):
    """Persistence interface used by retrieval orchestration."""

    async def search(
        self,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        """Retrieve relevant study-material chunks."""


class SupabaseRetrievalPersistence:
    """Call the protected Supabase retrieval RPC."""

    def __init__(
        self,
        client: RetrievalRpcClient,
    ) -> None:
        self._client = client

    async def search(
        self,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        """Execute the retrieval RPC and validate its rows."""

        if not isinstance(
            request,
            RetrievalRequest,
        ):
            raise RetrievalValidationError(
                "request must be a RetrievalRequest."
            )

        try:
            response = await self._client.call_rpc_json(
                RETRIEVAL_RPC_NAME,
                request.to_rpc_parameters(),
            )
        except (
            HTTPError,
            PostgrestAPIError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as exc:
            raise RetrievalRequestError(
                "The study-material retrieval request failed."
            ) from exc

        rows = _extract_response_rows(
            response,
        )

        chunks = tuple(
            RetrievedStudyChunk.from_rpc_row(
                row,
            )
            for row in rows
        )

        return RetrievalResult(
            request=request,
            chunks=chunks,
        )


def _extract_response_rows(
    response: object,
) -> tuple[Mapping[str, object], ...]:
    """Extract and validate retrieval rows from decoded JSON."""

    data = _unwrap_response_data(
        response,
    )

    if data is None:
        return ()

    if (
        isinstance(data, (str, bytes))
        or not isinstance(data, Sequence)
    ):
        raise RetrievalResponseError(
            "The retrieval RPC data must be a sequence."
        )

    normalized_rows: list[Mapping[str, object]] = []

    for row in data:
        if not isinstance(
            row,
            Mapping,
        ):
            raise RetrievalResponseError(
                "Every retrieval RPC row must be a mapping."
            )

        normalized_rows.append(
            row,
        )

    return tuple(
        normalized_rows,
    )


def _unwrap_response_data(
    response: object,
) -> object:
    """Support raw JSON lists and wrapped response objects."""

    if isinstance(
        response,
        Mapping,
    ):
        error = response.get(
            "error",
        )

        if error:
            raise RetrievalResponseError(
                "The retrieval RPC returned an error response."
            )

        if "data" not in response:
            raise RetrievalResponseError(
                "The retrieval RPC response is missing data."
            )

        return response["data"]

    wrapped_data = getattr(
        response,
        "data",
        _MISSING,
    )

    if wrapped_data is not _MISSING:
        error = getattr(
            response,
            "error",
            None,
        )

        if error:
            raise RetrievalResponseError(
                "The retrieval RPC returned an error response."
            )

        return wrapped_data

    if response is None or isinstance(
        response,
        Sequence,
    ):
        return response

    raise RetrievalResponseError(
        "The retrieval RPC returned an unsupported response."
    )