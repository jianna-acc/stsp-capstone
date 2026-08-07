# File: /backend/tests/test_grounded_answer_generation.py

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderRequestError,
)
from app.ai.grounded_answer_contracts import (
    NO_CONTEXT_ANSWER,
    GroundedAnswerFailureCode,
    GroundedAnswerGenerationError,
    GroundedAnswerOutcome,
    GroundedAnswerRequest,
    GroundedAnswerResponseError,
    GroundedAnswerValidationError,
)
from app.ai.grounded_prompt import (
    GroundedPromptBuilder,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.services.grounded_answer_generation import (
    GroundedAnswerGenerationService,
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)


def make_chunk(
    *,
    content: str,
    similarity_score: float,
    chunk_index: int,
) -> RetrievedStudyChunk:
    """Create one valid retrieved study chunk."""

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                uuid4(),
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": chunk_index,
            "content": content,
            "start_offset": chunk_index * 100,
            "end_offset": (
                chunk_index * 100
                + len(content)
            ),
            "chunk_metadata": {
                "page_number": chunk_index + 1,
            },
            "embedding_model": "gemini-embedding-2",
            "similarity_score": similarity_score,
        }
    )


class FakeGenerationProvider:
    """Return controlled generation results."""

    def __init__(
        self,
        *,
        result: GenerationResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = (
            result
            if result is not None
            else GenerationResult(
                text=(
                    "Photosynthesis converts light "
                    "energy into chemical energy. "
                    "[Source 1]"
                ),
                provider="fake",
                model="fake-model",
                input_tokens=100,
                output_tokens=20,
            )
        )
        self.error = error
        self.requests: list[
            GenerationRequest
        ] = []
        self.closed = False

    @property
    def provider_name(
        self,
    ) -> str:
        """Return the fake provider name."""

        return "fake"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Record and return one controlled result."""

        self.requests.append(
            request,
        )

        if self.error is not None:
            raise self.error

        return self.result

    async def aclose(
        self,
    ) -> None:
        """Record provider cleanup."""

        self.closed = True

class SequentialGenerationProvider:
    """Return generation results in a controlled sequence."""

    def __init__(
        self,
        *,
        results: list[GenerationResult],
    ) -> None:
        self.results = list(
            results,
        )
        self.requests: list[GenerationRequest] = []
        self.closed = False

    @property
    def provider_name(
        self,
    ) -> str:
        """Return the fake provider name."""

        return "fake"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Return the next configured result."""

        self.requests.append(
            request,
        )

        if not self.results:
            raise RuntimeError(
                "No configured generation result remains."
            )

        return self.results.pop(
            0,
        )

    async def aclose(
        self,
    ) -> None:
        """Record provider cleanup."""

        self.closed = True


def test_no_context_does_not_call_provider() -> None:
    provider = FakeGenerationProvider()

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(),
    )

    result = asyncio.run(
        service.generate(
            request,
        )
    )

    assert result.outcome == (
        GroundedAnswerOutcome.NO_CONTEXT
    )
    assert result.answer == NO_CONTEXT_ANSWER
    assert result.sources == ()
    assert provider.requests == []


def test_service_generates_grounded_answer() -> None:
    provider = FakeGenerationProvider()

    service = GroundedAnswerGenerationService(
        provider=provider,
        temperature=0.1,
        max_output_tokens=200,
    )

    chunk = make_chunk(
        content=(
            "Photosynthesis converts light energy "
            "into chemical energy."
        ),
        similarity_score=0.95,
        chunk_index=1,
    )

    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(
            chunk,
        ),
    )

    result = asyncio.run(
        service.generate(
            request,
        )
    )

    assert result.outcome == (
        GroundedAnswerOutcome.ANSWERED
    )
    assert result.source_count == 1
    assert result.sources[0].chunk_id == (
        chunk.chunk_id
    )
    assert result.provider == "fake"
    assert result.model == "fake-model"
    assert "[Source 1]" in result.answer

    assert len(
        provider.requests,
    ) == 1

    generation_request = provider.requests[0]

    assert generation_request.temperature == 0.1
    assert generation_request.max_output_tokens == 200
    assert generation_request.system_instruction
    assert "REQUEST_JSON" in (
        generation_request.prompt
    )
    assert str(
        chunk.chunk_id,
    ) not in generation_request.prompt


def test_service_preserves_only_included_chunks() -> None:
    first = make_chunk(
        content="First relevant study source.",
        similarity_score=0.95,
        chunk_index=1,
    )

    second = make_chunk(
        content="Second relevant study source.",
        similarity_score=0.85,
        chunk_index=2,
    )

    provider = FakeGenerationProvider(
        result=GenerationResult(
            text="The first source supports this. [Source 1]",
            provider="fake",
            model="fake-model",
        )
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
        prompt_builder=GroundedPromptBuilder(
            max_context_chunks=1,
        ),
    )

    result = asyncio.run(
        service.generate(
            GroundedAnswerRequest(
                question="Explain the material.",
                chunks=(
                    first,
                    second,
                ),
            )
        )
    )

    assert result.source_count == 1
    assert result.request.chunks == (
        first,
    )
    assert result.sources[0].chunk_id == (
        first.chunk_id
    )


def test_service_adds_source_footer_after_retry() -> None:
    provider = FakeGenerationProvider(
        result=GenerationResult(
            text="This answer has no citation.",
            provider="fake",
            model="fake-model",
        )
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="Explain the source.",
        chunks=(
            make_chunk(
                content="Valid source content.",
                similarity_score=0.90,
                chunk_index=1,
            ),
        ),
    )

    result = asyncio.run(
        service.generate(
            request,
        )
    )

    assert result.outcome == (
        GroundedAnswerOutcome.ANSWERED
    )

    assert result.answer.startswith(
        "This answer has no citation."
    )

    assert (
        "Sources consulted: [Source 1]"
        in result.answer
    )

    assert result.source_count == 1

    assert len(
        provider.requests,
    ) == 2


def test_service_rejects_unknown_source_number() -> None:
    provider = FakeGenerationProvider(
        result=GenerationResult(
            text="Unsupported citation. [Source 2]",
            provider="fake",
            model="fake-model",
        )
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="Explain the source.",
        chunks=(
            make_chunk(
                content="Only one source exists.",
                similarity_score=0.90,
                chunk_index=1,
            ),
        ),
    )

    with pytest.raises(
        GroundedAnswerResponseError,
    ):
        asyncio.run(
            service.generate(
                request,
            )
        )


@pytest.mark.parametrize(
    "answer",
    [
        "Malformed source. [Source one]",
        "Malformed source. [Source 01]",
        "Malformed source. [Source 1, 2]",
    ],
)
def test_service_rejects_malformed_citations(
    answer: str,
) -> None:
    provider = FakeGenerationProvider(
        result=GenerationResult(
            text=answer,
            provider="fake",
            model="fake-model",
        )
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="Explain the source.",
        chunks=(
            make_chunk(
                content="Valid source content.",
                similarity_score=0.90,
                chunk_index=1,
            ),
        ),
    )

    with pytest.raises(
        GroundedAnswerResponseError,
    ):
        asyncio.run(
            service.generate(
                request,
            )
        )


def test_service_rejects_provider_mismatch() -> None:
    provider = FakeGenerationProvider(
        result=GenerationResult(
            text="Grounded answer. [Source 1]",
            provider="different-provider",
            model="fake-model",
        )
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="Explain the source.",
        chunks=(
            make_chunk(
                content="Valid source content.",
                similarity_score=0.90,
                chunk_index=1,
            ),
        ),
    )

    with pytest.raises(
        GroundedAnswerResponseError,
    ):
        asyncio.run(
            service.generate(
                request,
            )
        )


def test_provider_failure_uses_stable_code() -> None:
    provider = FakeGenerationProvider(
        error=AIProviderRequestError(
            "Controlled provider failure."
        ),
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="Explain the source.",
        chunks=(
            make_chunk(
                content="Valid source content.",
                similarity_score=0.90,
                chunk_index=1,
            ),
        ),
    )

    with pytest.raises(
        GroundedAnswerGenerationError,
    ) as error:
        asyncio.run(
            service.generate(
                request,
            )
        )

    assert (
        error.value.error_code
        == GroundedAnswerFailureCode.GENERATION_FAILED
    )


def test_unexpected_provider_failure_is_wrapped() -> None:
    provider = FakeGenerationProvider(
        error=RuntimeError(
            "Unexpected controlled failure."
        ),
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="Explain the source.",
        chunks=(
            make_chunk(
                content="Valid source content.",
                similarity_score=0.90,
                chunk_index=1,
            ),
        ),
    )

    with pytest.raises(
        GroundedAnswerGenerationError,
    ):
        asyncio.run(
            service.generate(
                request,
            )
        )


def test_service_closes_provider() -> None:
    provider = FakeGenerationProvider()

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    asyncio.run(
        service.aclose()
    )

    assert provider.closed is True

def test_service_retries_once_to_repair_missing_citation() -> None:
    provider = SequentialGenerationProvider(
        results=[
            GenerationResult(
                text=(
                    "Photosynthesis converts light energy "
                    "into chemical energy."
                ),
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text=(
                    "Photosynthesis converts light energy "
                    "into chemical energy. [Source 1]"
                ),
                provider="fake",
                model="fake-model",
            ),
        ],
    )

    service = GroundedAnswerGenerationService(
        provider=provider,
    )

    request = GroundedAnswerRequest(
        question="What is photosynthesis?",
        chunks=(
            make_chunk(
                content=(
                    "Photosynthesis converts light energy "
                    "into chemical energy."
                ),
                similarity_score=0.95,
                chunk_index=1,
            ),
        ),
    )

    result = asyncio.run(
        service.generate(
            request,
        )
    )

    assert result.outcome == (
        GroundedAnswerOutcome.ANSWERED
    )

    assert "[Source 1]" in result.answer

    assert len(
        provider.requests,
    ) == 2

    assert (
        "CITATION_CORRECTION"
        in provider.requests[1].prompt
    )

@pytest.mark.parametrize(
    (
        "temperature",
        "max_output_tokens",
    ),
    [
        (
            -0.1,
            None,
        ),
        (
            2.1,
            None,
        ),
        (
            None,
            0,
        ),
        (
            None,
            8_193,
        ),
    ],
)
def test_service_rejects_invalid_generation_settings(
    temperature: float | None,
    max_output_tokens: int | None,
) -> None:
    with pytest.raises(
        GroundedAnswerValidationError,
    ):
        GroundedAnswerGenerationService(
            provider=FakeGenerationProvider(),
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )