# File: /backend/tests/test_grounded_answer_contracts.py

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.ai.grounded_answer_contracts import (
    NO_CONTEXT_ANSWER,
    GroundedAnswerFailureCode,
    GroundedAnswerGenerationError,
    GroundedAnswerOutcome,
    GroundedAnswerRequest,
    GroundedAnswerResponseError,
    GroundedAnswerResult,
    GroundedAnswerValidationError,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
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


def make_chunk(
    *,
    chunk_id: UUID = CHUNK_ID,
    similarity_score: float = 0.92,
    chunk_index: int = 2,
) -> RetrievedStudyChunk:
    """Return one valid retrieved study chunk."""

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                chunk_id,
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": chunk_index,
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
            "similarity_score": similarity_score,
        }
    )


def test_request_normalizes_question_and_chunks() -> None:
    chunk = make_chunk()

    request = GroundedAnswerRequest(
        question="  What is photosynthesis?  ",
        chunks=[
            chunk,
        ],
    )

    assert request.question == "What is photosynthesis?"
    assert request.chunks == (
        chunk,
    )
    assert request.context_available is True
    assert request.retrieved_count == 1


@pytest.mark.parametrize(
    "invalid_question",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_request_rejects_invalid_question(
    invalid_question: object,
) -> None:
    with pytest.raises(
        GroundedAnswerValidationError,
    ) as error:
        GroundedAnswerRequest(
            question=invalid_question,
            chunks=(),
        )

    assert (
        error.value.error_code
        == GroundedAnswerFailureCode.VALIDATION_FAILED
    )


def test_request_rejects_invalid_chunks_container() -> None:
    with pytest.raises(
        GroundedAnswerValidationError,
    ):
        GroundedAnswerRequest(
            question="What is photosynthesis?",
            chunks="not a chunk sequence",
        )


def test_request_rejects_invalid_chunk_item() -> None:
    with pytest.raises(
        GroundedAnswerValidationError,
    ):
        GroundedAnswerRequest(
            question="What is photosynthesis?",
            chunks=(
                object(),
            ),
        )


def test_request_rejects_duplicate_chunks() -> None:
    chunk = make_chunk()

    with pytest.raises(
        GroundedAnswerValidationError,
    ):
        GroundedAnswerRequest(
            question="What is photosynthesis?",
            chunks=(
                chunk,
                chunk,
            ),
        )


def test_request_requires_descending_similarity() -> None:
    lower = make_chunk(
        chunk_id=uuid4(),
        similarity_score=0.70,
        chunk_index=1,
    )

    higher = make_chunk(
        chunk_id=uuid4(),
        similarity_score=0.90,
        chunk_index=2,
    )

    with pytest.raises(
        GroundedAnswerValidationError,
    ):
        GroundedAnswerRequest(
            question="What is photosynthesis?",
            chunks=(
                lower,
                higher,
            ),
        )


def test_source_references_are_deterministic() -> None:
    first_chunk = make_chunk(
        chunk_id=uuid4(),
        similarity_score=0.92,
        chunk_index=1,
    )

    second_chunk = make_chunk(
        chunk_id=uuid4(),
        similarity_score=0.81,
        chunk_index=2,
    )

    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(
            first_chunk,
            second_chunk,
        ),
    )

    sources = request.build_source_references()

    assert len(
        sources,
    ) == 2

    assert sources[0].source_number == 1
    assert sources[0].chunk_id == first_chunk.chunk_id
    assert sources[0].citation_marker == "[Source 1]"

    assert sources[1].source_number == 2
    assert sources[1].chunk_id == second_chunk.chunk_id
    assert sources[1].citation_marker == "[Source 2]"


def test_no_context_result_is_normal_success() -> None:
    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(),
    )

    result = GroundedAnswerResult.no_context(
        request,
    )

    assert result.outcome == GroundedAnswerOutcome.NO_CONTEXT
    assert result.answer == NO_CONTEXT_ANSWER
    assert result.sources == ()
    assert result.provider is None
    assert result.model is None
    assert result.context_available is False
    assert result.source_count == 0


def test_no_context_rejects_request_with_chunks() -> None:
    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(
            make_chunk(),
        ),
    )

    with pytest.raises(
        GroundedAnswerResponseError,
    ):
        GroundedAnswerResult.no_context(
            request,
        )


def test_generated_result_preserves_sources() -> None:
    chunk = make_chunk()

    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(
            chunk,
        ),
    )

    result = GroundedAnswerResult.generated(
        request=request,
        answer=(
            "Photosynthesis converts light energy into "
            "chemical energy. [Source 1]"
        ),
        provider="  gemini  ",
        model="  gemini-3.6-flash  ",
    )

    assert result.outcome == GroundedAnswerOutcome.ANSWERED
    assert result.context_available is True
    assert result.source_count == 1
    assert result.sources[0].chunk_id == chunk.chunk_id
    assert result.provider == "gemini"
    assert result.model == "gemini-3.6-flash"


def test_generated_result_rejects_empty_context() -> None:
    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(),
    )

    with pytest.raises(
        GroundedAnswerResponseError,
    ):
        GroundedAnswerResult.generated(
            request=request,
            answer="Unsupported answer.",
            provider="gemini",
            model="gemini-3.6-flash",
        )


@pytest.mark.parametrize(
    (
        "provider",
        "model",
    ),
    [
        (
            "",
            "gemini-3.6-flash",
        ),
        (
            "gemini",
            "",
        ),
        (
            None,
            "gemini-3.6-flash",
        ),
        (
            "gemini",
            None,
        ),
    ],
)
def test_generated_result_rejects_invalid_metadata(
    provider: object,
    model: object,
) -> None:
    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(
            make_chunk(),
        ),
    )

    with pytest.raises(
        GroundedAnswerResponseError,
    ):
        GroundedAnswerResult.generated(
            request=request,
            answer="Grounded answer. [Source 1]",
            provider=provider,
            model=model,
        )


def test_generation_error_uses_stable_code() -> None:
    error = GroundedAnswerGenerationError(
        "Controlled generation failure."
    )

    assert (
        error.error_code
        == GroundedAnswerFailureCode.GENERATION_FAILED
    )