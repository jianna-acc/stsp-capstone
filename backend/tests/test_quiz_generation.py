# File: /backend/tests/test_quiz_generation.py

# Purpose: Verifies structured Quiz generation, repair behavior,
# provider failures, requested type enforcement, and duplicates.

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec
from uuid import uuid4

import pytest

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderRequestError,
)
from app.schemas.quiz import (
    QuizDifficulty,
    QuizGenerateRequest,
    QuizScopeType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizGenerationError,
    QuizGenerationResponseError,
)
from app.services.quiz_generation import (
    LARGE_QUIZ_OUTPUT_TOKENS,
    STANDARD_QUIZ_OUTPUT_TOKENS,
    QuizGenerationService,
)
from app.services.quiz_source_loader import (
    QuizSourceBundle,
    QuizSourceChunk,
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
    """Run one async test using the standard library."""

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


class FakeProvider:
    """Controlled generation provider."""

    provider_name = "fake-provider"

    def __init__(
        self,
        results: list[
            GenerationResult | Exception
        ],
    ) -> None:
        self.results = list(
            results,
        )

        self.requests: list[
            GenerationRequest
        ] = []

        self.closed = False

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        self.requests.append(
            request,
        )

        result = self.results.pop(
            0,
        )

        if isinstance(
            result,
            Exception,
        ):
            raise result

        return result

    async def aclose(
        self,
    ) -> None:
        self.closed = True


def _source_bundle(
    *,
    subject_id,
) -> QuizSourceBundle:
    """Return one complete subject source bundle."""

    file_id = uuid4()

    return QuizSourceBundle(
        user_id=uuid4(),
        subject_id=subject_id,
        scope_type=QuizScopeType.SUBJECT,
        study_file_id=None,
        chunks=(
            QuizSourceChunk(
                study_file_id=file_id,
                source_name="Lecture.pdf",
                chunk_index=0,
                content=(
                    "Jose Rizal wrote Noli Me Tangere. "
                    "The novel criticized abuses under "
                    "Spanish colonial society."
                ),
                locator_type="page",
                locator_label="Page 1",
            ),
        ),
    )


def _mcq(
    *,
    position: int,
    question: str,
) -> dict[
    str,
    object,
]:
    """Return one valid multiple-choice payload."""

    return {
        "position": position,
        "question_type": "multiple_choice",
        "topic": "Rizal",
        "question": question,
        "choices": [
            "Jose Rizal",
            "Andres Bonifacio",
            "Emilio Aguinaldo",
            "Apolinario Mabini",
        ],
        "correct_answer": "Jose Rizal",
        "accepted_answers": [],
        "explanation": (
            "The supplied material identifies Jose Rizal."
        ),
    }


def _true_false(
    *,
    position: int,
    question: str,
) -> dict[
    str,
    object,
]:
    """Return one valid true-or-false payload."""

    return {
        "position": position,
        "question_type": "true_false",
        "topic": "Rizal",
        "question": question,
        "choices": [
            "True",
            "False",
        ],
        "correct_answer": "True",
        "accepted_answers": [],
        "explanation": (
            "The statement is supported by the supplied material."
        ),
    }


def _identification(
    *,
    position: int,
    question: str,
) -> dict[
    str,
    object,
]:
    """Return one valid identification payload."""

    return {
        "position": position,
        "question_type": "identification",
        "topic": "Rizal",
        "question": question,
        "choices": [],
        "correct_answer": "Jose Rizal",
        "accepted_answers": [
            "José Rizal",
        ],
        "explanation": (
            "The supplied material names Jose Rizal."
        ),
    }


def _result(
    payload: object,
    *,
    provider: str = "fake-provider",
) -> GenerationResult:
    """Return one fake AI generation result."""

    return GenerationResult(
        text=json.dumps(
            payload,
        ),
        provider=provider,
        model="fake-model",
        input_tokens=100,
        output_tokens=200,
    )


def _request(
    *,
    quiz_type: QuizType = QuizType.MULTIPLE_CHOICE,
    question_count: int = 1,
) -> QuizGenerateRequest:
    """Return one valid subject Quiz request."""

    return QuizGenerateRequest(
        scope_type=QuizScopeType.SUBJECT,
        subject_id=uuid4(),
        quiz_type=quiz_type,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=question_count,
    )


@async_test
async def test_generation_returns_valid_quiz() -> None:
    """Valid provider JSON must become structured Quiz content."""

    request = _request()

    provider = FakeProvider(
        [
            _result(
                {
                    "title": "Rizal Quiz",
                    "questions": [
                        _mcq(
                            position=1,
                            question=(
                                "Who wrote Noli Me Tangere?"
                            ),
                        ),
                    ],
                }
            )
        ]
    )

    result = await QuizGenerationService(
        provider=provider,
    ).generate(
        request=request,
        source_bundle=_source_bundle(
            subject_id=request.subject_id,
        ),
    )

    assert result.content.title == "Rizal Quiz"
    assert len(
        result.content.questions,
    ) == 1

    assert result.provider == "fake-provider"
    assert result.model == "fake-model"
    assert result.generation_attempt_count == 1

    assert len(
        provider.requests,
    ) == 1


@async_test
async def test_invalid_first_response_is_repaired_once() -> None:
    """Malformed output must receive one repair attempt."""

    request = _request()

    provider = FakeProvider(
        [
            GenerationResult(
                text="{invalid json",
                provider="fake-provider",
                model="fake-model",
            ),
            _result(
                {
                    "title": "Repaired Quiz",
                    "questions": [
                        _mcq(
                            position=1,
                            question="Who wrote the novel?",
                        ),
                    ],
                }
            ),
        ]
    )

    result = await QuizGenerationService(
        provider=provider,
    ).generate(
        request=request,
        source_bundle=_source_bundle(
            subject_id=request.subject_id,
        ),
    )

    assert result.content.title == "Repaired Quiz"
    assert result.generation_attempt_count == 2
    assert len(
        provider.requests,
    ) == 2

    assert (
        "REPAIR_REQUEST"
        in provider.requests[
            1
        ].prompt
    )


@async_test
async def test_invalid_repair_response_is_rejected() -> None:
    """A second invalid response must fail in a controlled way."""

    request = _request()

    provider = FakeProvider(
        [
            GenerationResult(
                text="{invalid",
                provider="fake-provider",
                model="fake-model",
            ),
            GenerationResult(
                text="{still invalid",
                provider="fake-provider",
                model="fake-model",
            ),
        ]
    )

    with pytest.raises(
        QuizGenerationResponseError,
    ):
        await QuizGenerationService(
            provider=provider,
        ).generate(
            request=request,
            source_bundle=_source_bundle(
                subject_id=request.subject_id,
            ),
        )


@async_test
async def test_requested_question_count_is_enforced() -> None:
    """AI output must contain exactly the requested count."""

    request = _request(
        question_count=2,
    )

    valid_repair = {
        "title": "Two Questions",
        "questions": [
            _mcq(
                position=1,
                question="Who wrote Noli Me Tangere?",
            ),
            _mcq(
                position=2,
                question="Who is identified as the novelist?",
            ),
        ],
    }

    provider = FakeProvider(
        [
            _result(
                {
                    "title": "Too Short",
                    "questions": [
                        _mcq(
                            position=1,
                            question="Who wrote the novel?",
                        ),
                    ],
                }
            ),
            _result(
                valid_repair,
            ),
        ]
    )

    result = await QuizGenerationService(
        provider=provider,
    ).generate(
        request=request,
        source_bundle=_source_bundle(
            subject_id=request.subject_id,
        ),
    )

    assert len(
        result.content.questions,
    ) == 2

    assert result.generation_attempt_count == 2


@async_test
async def test_non_mixed_quiz_enforces_requested_type() -> None:
    """MCQ requests must not silently become true-or-false."""

    request = _request(
        quiz_type=QuizType.MULTIPLE_CHOICE,
    )

    invalid_payload = {
        "title": "Wrong Type",
        "questions": [
            _true_false(
                position=1,
                question="Rizal wrote Noli Me Tangere.",
            ),
        ],
    }

    provider = FakeProvider(
        [
            _result(
                invalid_payload,
            ),
            _result(
                invalid_payload,
            ),
        ]
    )

    with pytest.raises(
        QuizGenerationResponseError,
    ):
        await QuizGenerationService(
            provider=provider,
        ).generate(
            request=request,
            source_bundle=_source_bundle(
                subject_id=request.subject_id,
            ),
        )


@async_test
async def test_mixed_quiz_requires_all_types() -> None:
    """Normal mixed Quiz output must contain all three types."""

    request = _request(
        quiz_type=QuizType.MIXED,
        question_count=3,
    )

    valid_payload = {
        "title": "Mixed Quiz",
        "questions": [
            _mcq(
                position=1,
                question="Who wrote Noli Me Tangere?",
            ),
            _true_false(
                position=2,
                question="Rizal wrote Noli Me Tangere.",
            ),
            _identification(
                position=3,
                question="Identify the author of the novel.",
            ),
        ],
    }

    provider = FakeProvider(
        [
            _result(
                valid_payload,
            ),
        ]
    )

    result = await QuizGenerationService(
        provider=provider,
    ).generate(
        request=request,
        source_bundle=_source_bundle(
            subject_id=request.subject_id,
        ),
    )

    assert len(
        {
            question.question_type
            for question in result.content.questions
        },
    ) == 3


@async_test
async def test_duplicate_questions_are_repaired() -> None:
    """Case/whitespace-equivalent duplicates must be rejected."""

    request = _request(
        question_count=2,
    )

    invalid_payload = {
        "title": "Duplicate Quiz",
        "questions": [
            _mcq(
                position=1,
                question="Who wrote Noli Me Tangere?",
            ),
            _mcq(
                position=2,
                question="  WHO wrote   Noli Me Tangere? ",
            ),
        ],
    }

    repaired_payload = {
        "title": "Repaired Quiz",
        "questions": [
            _mcq(
                position=1,
                question="Who wrote Noli Me Tangere?",
            ),
            _mcq(
                position=2,
                question=(
                    "Which person is identified as the author?"
                ),
            ),
        ],
    }

    provider = FakeProvider(
        [
            _result(
                invalid_payload,
            ),
            _result(
                repaired_payload,
            ),
        ]
    )

    result = await QuizGenerationService(
        provider=provider,
    ).generate(
        request=request,
        source_bundle=_source_bundle(
            subject_id=request.subject_id,
        ),
    )

    assert result.generation_attempt_count == 2


@async_test
async def test_provider_failure_becomes_generation_error() -> None:
    """External provider failures must remain controlled."""

    request = _request()

    provider = FakeProvider(
        [
            AIProviderRequestError(
                "provider unavailable",
            ),
        ]
    )

    with pytest.raises(
        QuizGenerationError,
    ):
        await QuizGenerationService(
            provider=provider,
        ).generate(
            request=request,
            source_bundle=_source_bundle(
                subject_id=request.subject_id,
            ),
        )


@async_test
async def test_provider_identity_must_match() -> None:
    """Configured and returned provider identities must agree."""

    request = _request()

    provider = FakeProvider(
        [
            _result(
                {
                    "title": "Quiz",
                    "questions": [
                        _mcq(
                            position=1,
                            question="Who wrote the novel?",
                        ),
                    ],
                },
                provider="different-provider",
            ),
        ]
    )

    with pytest.raises(
        QuizGenerationResponseError,
    ):
        await QuizGenerationService(
            provider=provider,
        ).generate(
            request=request,
            source_bundle=_source_bundle(
                subject_id=request.subject_id,
            ),
        )


@async_test
async def test_small_quiz_uses_standard_token_budget() -> None:
    """Small Quizzes should use the standard output budget."""

    request = _request()

    provider = FakeProvider(
        [
            _result(
                {
                    "title": "Quiz",
                    "questions": [
                        _mcq(
                            position=1,
                            question="Who wrote the novel?",
                        ),
                    ],
                }
            )
        ]
    )

    await QuizGenerationService(
        provider=provider,
    ).generate(
        request=request,
        source_bundle=_source_bundle(
            subject_id=request.subject_id,
        ),
    )

    assert (
        provider.requests[
            0
        ].max_output_tokens
        == STANDARD_QUIZ_OUTPUT_TOKENS
    )


def test_large_quiz_token_budget_is_supported() -> None:
    """Large question sets should receive the larger output budget."""

    service = QuizGenerationService(
        provider=FakeProvider(
            [],
        ),
    )

    assert (
        service._output_token_budget(
            11,
        )
        == LARGE_QUIZ_OUTPUT_TOKENS
    )