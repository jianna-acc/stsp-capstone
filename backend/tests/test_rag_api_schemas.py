# File: /backend/tests/test_rag_api_schemas.py

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.rag import (
    DEFAULT_RAG_MATCH_COUNT,
    DEFAULT_RAG_SIMILARITY_THRESHOLD,
    RagAnswerOutcome,
    RagAnswerRequest,
    RagAnswerResponse,
    RagApiErrorResponse,
    RagSourceResponse,
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)


def make_source(
    *,
    source_number: int = 1,
    source_name: str = "Biology Notes.pdf",
    chunk_index: int = 2,
    similarity_score: float = 0.92,
) -> RagSourceResponse:
    """Create one valid public source response."""

    return RagSourceResponse(
        source_number=source_number,
        source_name=source_name,
        chunk_index=chunk_index,
        similarity_score=similarity_score,
    )


def test_request_normalizes_question_and_defaults() -> None:
    request = RagAnswerRequest(
        question="  What is photosynthesis?  ",
    )

    assert request.question == "What is photosynthesis?"
    assert request.study_file_id is None
    assert request.subject_id is None
    assert request.match_count == DEFAULT_RAG_MATCH_COUNT
    assert request.similarity_threshold == (
        DEFAULT_RAG_SIMILARITY_THRESHOLD
    )


def test_request_accepts_optional_filters() -> None:
    request = RagAnswerRequest(
        question="Explain cellular respiration.",
        study_file_id=FILE_ID,
        subject_id=SUBJECT_ID,
        match_count=5,
        similarity_threshold=0.75,
    )

    assert request.study_file_id == FILE_ID
    assert request.subject_id == SUBJECT_ID
    assert request.match_count == 5
    assert request.similarity_threshold == 0.75


@pytest.mark.parametrize(
    "question",
    [
        "",
        "   ",
    ],
)
def test_request_rejects_empty_question(
    question: str,
) -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerRequest(
            question=question,
        )


@pytest.mark.parametrize(
    "match_count",
    [
        0,
        21,
    ],
)
def test_request_rejects_invalid_match_count(
    match_count: int,
) -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerRequest(
            question="Valid question.",
            match_count=match_count,
        )


@pytest.mark.parametrize(
    "threshold",
    [
        -0.01,
        1.01,
    ],
)
def test_request_rejects_invalid_similarity_threshold(
    threshold: float,
) -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerRequest(
            question="Valid question.",
            similarity_threshold=threshold,
        )


def test_request_rejects_unknown_fields() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerRequest.model_validate(
            {
                "question": "Valid question.",
                "unknown_field": "not allowed",
            }
        )


def test_source_normalizes_display_name() -> None:
    source = make_source(
        source_name="  Biology Notes.pdf  ",
    )

    assert source.source_name == "Biology Notes.pdf"


def test_answered_response_is_valid() -> None:
    source = make_source()

    response = RagAnswerResponse(
        conversation_id=(
            "55555555-5555-4555-8555-555555555555"
        ),
        outcome=RagAnswerOutcome.ANSWERED,
        answer=(
            "Photosynthesis converts light energy "
            "into chemical energy. [Source 1]"
        ),
        sources=(
            source,
        ),
        retrieved_count=1,
        source_count=1,
        context_available=True,
    )

    assert response.outcome == RagAnswerOutcome.ANSWERED
    assert response.source_count == 1
    assert response.context_available is True
    assert response.sources == (
        source,
    )


def test_no_context_response_is_valid() -> None:
    response = RagAnswerResponse(
        conversation_id=(
            "55555555-5555-4555-8555-555555555555"
        ),
        outcome=RagAnswerOutcome.NO_CONTEXT,
        answer=(
            "I could not find enough relevant information "
            "in your uploaded study materials."
        ),
        sources=(),
        retrieved_count=0,
        source_count=0,
        context_available=False,
    )

    assert response.outcome == RagAnswerOutcome.NO_CONTEXT
    assert response.sources == ()
    assert response.source_count == 0
    assert response.context_available is False


def test_answered_response_requires_sources() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerResponse(
            outcome=RagAnswerOutcome.ANSWERED,
            answer="Unsupported answer.",
            sources=(),
            retrieved_count=1,
            source_count=0,
            context_available=True,
        )


def test_answered_response_requires_context_flag() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerResponse(
            outcome=RagAnswerOutcome.ANSWERED,
            answer="Grounded answer. [Source 1]",
            sources=(
                make_source(),
            ),
            retrieved_count=1,
            source_count=1,
            context_available=False,
        )


def test_response_requires_consecutive_source_numbers() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerResponse(
            outcome=RagAnswerOutcome.ANSWERED,
            answer="Grounded answer. [Source 2]",
            sources=(
                make_source(
                    source_number=2,
                ),
            ),
            retrieved_count=1,
            source_count=1,
            context_available=True,
        )


def test_response_rejects_source_count_mismatch() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerResponse(
            outcome=RagAnswerOutcome.ANSWERED,
            answer="Grounded answer. [Source 1]",
            sources=(
                make_source(),
            ),
            retrieved_count=1,
            source_count=0,
            context_available=True,
        )


def test_no_context_response_rejects_sources() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagAnswerResponse(
            outcome=RagAnswerOutcome.NO_CONTEXT,
            answer="No context.",
            sources=(
                make_source(),
            ),
            retrieved_count=1,
            source_count=1,
            context_available=False,
        )


def test_error_response_normalizes_fields() -> None:
    response = RagApiErrorResponse(
        error_code="  RAG_GENERATION_FAILED  ",
        message="  The answer could not be generated.  ",
    )

    assert response.error_code == "RAG_GENERATION_FAILED"
    assert response.message == (
        "The answer could not be generated."
    )


def test_error_response_rejects_unknown_fields() -> None:
    with pytest.raises(
        ValidationError,
    ):
        RagApiErrorResponse.model_validate(
            {
                "error_code": "RAG_REQUEST_FAILED",
                "message": "Controlled failure.",
                "details": {
                    "secret": "not allowed",
                },
            }
        )
