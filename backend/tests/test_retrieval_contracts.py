# File: /backend/tests/test_retrieval_contracts.py

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.ai.retrieval_contracts import (
    DEFAULT_RETRIEVAL_MATCH_COUNT,
    DEFAULT_RETRIEVAL_SIMILARITY_THRESHOLD,
    NO_CONTEXT_MESSAGE,
    RETRIEVAL_EMBEDDING_DIMENSIONS,
    RetrievalFailureCode,
    RetrievalOutcome,
    RetrievalRequest,
    RetrievalResponseError,
    RetrievalResult,
    RetrievalValidationError,
    RetrievedStudyChunk,
)

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
    values = [
        0.0
    ] * RETRIEVAL_EMBEDDING_DIMENSIONS

    values[-1] = 1.0

    return tuple(
        values,
    )


def make_request(
    **overrides: object,
) -> RetrievalRequest:
    values: dict[str, object] = {
        "user_id": USER_ID,
        "query_embedding": make_embedding(),
    }

    values.update(
        overrides,
    )

    return RetrievalRequest(
        **values,
    )


def make_row(
    **overrides: object,
) -> dict[str, object]:
    values: dict[str, object] = {
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

    values.update(
        overrides,
    )

    return values


def make_chunk(
    **overrides: object,
) -> RetrievedStudyChunk:
    return RetrievedStudyChunk.from_rpc_row(
        make_row(
            **overrides,
        )
    )


def test_request_uses_phase_5a_defaults() -> None:
    request = make_request()

    assert (
        request.match_count
        == DEFAULT_RETRIEVAL_MATCH_COUNT
    )
    assert (
        request.similarity_threshold
        == DEFAULT_RETRIEVAL_SIMILARITY_THRESHOLD
    )

    parameters = request.to_rpc_parameters()

    assert parameters["p_user_id"] == str(
        USER_ID,
    )
    assert parameters["p_match_count"] == 8
    assert parameters["p_similarity_threshold"] == 0.60
    assert parameters["p_study_file_id"] is None
    assert parameters["p_subject_id"] is None

    embedding = parameters["p_query_embedding"]

    assert isinstance(
        embedding,
        list,
    )
    assert len(
        embedding,
    ) == 768


def test_request_includes_optional_filters() -> None:
    request = make_request(
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
    )

    parameters = request.to_rpc_parameters()

    assert parameters["p_study_file_id"] == str(
        FILE_ID,
    )
    assert parameters["p_subject_id"] == str(
        SUBJECT_ID,
    )


def test_request_rejects_wrong_embedding_length() -> None:
    with pytest.raises(
        RetrievalValidationError,
    ) as error:
        make_request(
            query_embedding=tuple(
                0.1
                for _ in range(767)
            )
        )

    assert (
        error.value.error_code
        == RetrievalFailureCode.VALIDATION_FAILED
    )


@pytest.mark.parametrize(
    "invalid_embedding",
    [
        tuple(
            0.0
            for _ in range(768)
        ),
        (
            "invalid",
            *tuple(
                0.0
                for _ in range(766)
            ),
            1.0,
        ),
        (
            float("nan"),
            *tuple(
                0.0
                for _ in range(766)
            ),
            1.0,
        ),
    ],
)
def test_request_rejects_invalid_embedding_values(
    invalid_embedding: object,
) -> None:
    with pytest.raises(
        RetrievalValidationError,
    ):
        make_request(
            query_embedding=invalid_embedding,
        )


@pytest.mark.parametrize(
    "invalid_match_count",
    [
        0,
        21,
        True,
        1.5,
    ],
)
def test_request_rejects_invalid_match_count(
    invalid_match_count: object,
) -> None:
    with pytest.raises(
        RetrievalValidationError,
    ):
        make_request(
            match_count=invalid_match_count,
        )


@pytest.mark.parametrize(
    "invalid_threshold",
    [
        -0.01,
        1.01,
        float("nan"),
        True,
    ],
)
def test_request_rejects_invalid_similarity_threshold(
    invalid_threshold: object,
) -> None:
    with pytest.raises(
        RetrievalValidationError,
    ):
        make_request(
            similarity_threshold=invalid_threshold,
        )


def test_chunk_parses_exact_rpc_columns() -> None:
    chunk = make_chunk()

    assert chunk.chunk_id == CHUNK_ID
    assert chunk.study_file_id == FILE_ID
    assert chunk.subject_id == SUBJECT_ID
    assert chunk.source_name == "Biology Notes.pdf"
    assert chunk.chunk_index == 2
    assert chunk.similarity_score == 0.92
    assert chunk.chunk_metadata == {
        "page_number": 3,
    }


def test_chunk_rejects_missing_rpc_column() -> None:
    row = make_row()

    del row["content"]

    with pytest.raises(
        RetrievalResponseError,
    ) as error:
        RetrievedStudyChunk.from_rpc_row(
            row,
        )

    assert (
        error.value.error_code
        == RetrievalFailureCode.RESPONSE_FAILED
    )


def test_chunk_rejects_invalid_metadata() -> None:
    with pytest.raises(
        RetrievalResponseError,
    ):
        make_chunk(
            chunk_metadata=[
                "not",
                "an",
                "object",
            ]
        )


def test_chunk_rejects_invalid_similarity_score() -> None:
    with pytest.raises(
        RetrievalResponseError,
    ):
        make_chunk(
            similarity_score=1.5,
        )


def test_result_reports_available_context() -> None:
    request = make_request()

    result = RetrievalResult(
        request=request,
        chunks=(
            make_chunk(),
        ),
    )

    assert result.outcome == RetrievalOutcome.MATCHES
    assert result.context_available is True
    assert result.no_context_message is None


def test_result_reports_no_context_without_error() -> None:
    request = make_request()

    result = RetrievalResult(
        request=request,
        chunks=(),
    )

    assert result.outcome == RetrievalOutcome.NO_CONTEXT
    assert result.context_available is False
    assert result.no_context_message == NO_CONTEXT_MESSAGE


def test_result_rejects_duplicate_chunks() -> None:
    request = make_request()
    chunk = make_chunk()

    with pytest.raises(
        RetrievalResponseError,
    ):
        RetrievalResult(
            request=request,
            chunks=(
                chunk,
                chunk,
            ),
        )


def test_result_requires_descending_similarity() -> None:
    request = make_request()

    lower_score = make_chunk(
        chunk_id=str(
            uuid4(),
        ),
        similarity_score=0.70,
    )

    higher_score = make_chunk(
        chunk_id=str(
            uuid4(),
        ),
        similarity_score=0.90,
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        RetrievalResult(
            request=request,
            chunks=(
                lower_score,
                higher_score,
            ),
        )


def test_result_enforces_study_file_filter() -> None:
    request = make_request(
        study_file_id=uuid4(),
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        RetrievalResult(
            request=request,
            chunks=(
                make_chunk(),
            ),
        )


def test_result_enforces_subject_filter() -> None:
    request = make_request(
        subject_id=uuid4(),
    )

    with pytest.raises(
        RetrievalResponseError,
    ):
        RetrievalResult(
            request=request,
            chunks=(
                make_chunk(),
            ),
        )