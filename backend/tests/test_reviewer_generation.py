# File: /backend/tests/test_reviewer_generation.py
# Purpose: Verifies structured reviewer generation,
# validation, retry behavior, and provider error handling.

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
from app.schemas.reviewer import (
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerLocatorType,
    ReviewerScopeType,
)
from app.services.reviewer_errors import (
    ReviewerGenerationError,
    ReviewerGenerationResponseError,
)
from app.services.reviewer_generation import (
    ReviewerGenerationService,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
    ReviewerSourceChunk,
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
    """Run async tests with the Python standard library."""

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


class FakeGenerationProvider:
    """Controlled provider used by reviewer generation tests."""

    provider_name = "fake"

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

        if not self.results:
            raise RuntimeError(
                "No fake provider result configured.",
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


def _valid_json() -> str:
    """Return one valid reviewer JSON response."""

    return json.dumps(
        {
            "overview": "Overview of the lesson.",
            "topics": [
                {
                    "title": "Topic One",
                    "summary": "Topic summary.",
                    "key_points": [
                        "Important point.",
                    ],
                    "definitions": [
                        {
                            "term": "Concept",
                            "definition": (
                                "Meaning of the concept."
                            ),
                        }
                    ],
                }
            ],
        }
    )


def _request_and_bundle(
    *,
    reviewer_length: ReviewerLength = (
        ReviewerLength.MEDIUM
    ),
) -> tuple[
    ReviewerGenerateRequest,
    ReviewerSourceBundle,
]:
    """Return matching reviewer input objects."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        reviewer_length=reviewer_length,
    )

    bundle = ReviewerSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.FILE,
        study_file_id=file_id,
        chunks=(
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Lecture.pdf",
                chunk_index=0,
                content="Lesson material.",
                locator_type=ReviewerLocatorType.PAGE,
                locator_label="Page 1",
            ),
        ),
    )

    return request, bundle


@async_test
async def test_valid_json_generates_reviewer() -> None:
    """Valid provider JSON must become ReviewerContent."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
                input_tokens=100,
                output_tokens=200,
            )
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert result.content.overview == (
        "Overview of the lesson."
    )

    assert len(
        result.content.topics,
    ) == 1

    assert result.provider == "fake"
    assert result.model == "fake-model"

    assert result.generation_attempt_count == 1
    assert len(provider.requests) == 1

@async_test
async def test_markdown_fenced_json_generates_reviewer() -> None:
    """Markdown-fenced JSON must be accepted as reviewer content."""

    fenced_json = (
        "```json\n"
        f"{_valid_json()}\n"
        "```"
    )

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=fenced_json,
                provider="fake",
                model="fake-model",
            )
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert result.content.overview == (
        "Overview of the lesson."
    )

    assert result.generation_attempt_count == 1
    assert len(provider.requests) == 1

@async_test
async def test_invalid_json_is_repaired_once() -> None:
    """Malformed first response must receive one repair attempt."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text="not json",
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert result.generation_attempt_count == 2
    assert len(provider.requests) == 2

    assert (
        "REPAIR_REQUEST"
        in provider.requests[
            1
        ].prompt
    )

    assert (
        "not json"
        in provider.requests[
            1
        ].prompt
    )


@async_test
async def test_invalid_repair_response_fails() -> None:
    """A second malformed response must fail without further retries."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text="first invalid response",
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text="second invalid response",
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    with pytest.raises(
        ReviewerGenerationResponseError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )

    assert len(provider.requests) == 2


@async_test
async def test_structurally_invalid_json_is_repaired() -> None:
    """Valid JSON with wrong structure must also be repaired."""

    invalid_structure = json.dumps(
        {
            "overview": "Overview",
            "topics": [],
        }
    )

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=invalid_structure,
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert result.generation_attempt_count == 2


@pytest.mark.parametrize(
    (
        "reviewer_length",
        "expected_tokens",
    ),
    (
        (
            ReviewerLength.SHORT,
            4_096,
        ),
        (
            ReviewerLength.MEDIUM,
            8_192,
        ),
        (
            ReviewerLength.LONG,
            8_192,
        ),
    ),
)
@async_test
async def test_reviewer_length_controls_output_budget(
    reviewer_length: ReviewerLength,
    expected_tokens: int,
) -> None:
    """Reviewer detail level must control generation budget."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
            )
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle(
            reviewer_length=reviewer_length,
        )
    )

    await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert (
        provider.requests[
            0
        ].max_output_tokens
        == expected_tokens
    )


@async_test
async def test_provider_failure_becomes_controlled_error() -> None:
    """Provider request failures must not escape directly."""

    provider = FakeGenerationProvider(
        [
            AIProviderRequestError(
                "provider unavailable",
            )
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    with pytest.raises(
        ReviewerGenerationError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )


@async_test
async def test_provider_identity_must_match_result() -> None:
    """Generation result must come from the configured provider."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(),
                provider="different-provider",
                model="fake-model",
            )
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    request, bundle = (
        _request_and_bundle()
    )

    with pytest.raises(
        ReviewerGenerationResponseError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )


@async_test
async def test_close_closes_supported_provider() -> None:
    """Generation service must release provider resources."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
            )
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    await service.aclose()

    assert provider.closed is True