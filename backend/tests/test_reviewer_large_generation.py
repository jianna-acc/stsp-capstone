# File: /backend/tests/test_reviewer_large_generation.py
# Purpose: Verifies large-material reviewer generation through
# ordered source batches and final reviewer synthesis.

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec
from uuid import uuid4

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.reviewer_prompt import (
    ReviewerPromptBuilder,
)
from app.schemas.reviewer import (
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerScopeType,
)
from app.services.reviewer_batching import (
    ReviewerSourceBatcher,
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
    """Return controlled responses and record provider requests."""

    provider_name = "fake"

    def __init__(
        self,
        results: list[
            GenerationResult,
        ],
    ) -> None:
        self.results = list(
            results,
        )

        self.requests: list[
            GenerationRequest
        ] = []

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Return the next configured generation result."""

        self.requests.append(
            request,
        )

        if not self.results:
            raise RuntimeError(
                "No fake generation result configured.",
            )

        return self.results.pop(
            0,
        )


def _reviewer_json(
    *,
    overview: str,
    topic_title: str,
) -> str:
    """Return one valid structured reviewer response."""

    return json.dumps(
        {
            "overview": overview,
            "topics": [
                {
                    "title": topic_title,
                    "summary": (
                        f"Summary for {topic_title}."
                    ),
                    "key_points": [
                        f"Important point for {topic_title}.",
                    ],
                    "definitions": [],
                }
            ],
        }
    )


def _provider_result(
    *,
    overview: str,
    topic_title: str,
) -> GenerationResult:
    """Return one valid fake provider result."""

    return GenerationResult(
        text=_reviewer_json(
            overview=overview,
            topic_title=topic_title,
        ),
        provider="fake",
        model="fake-model",
        input_tokens=100,
        output_tokens=200,
    )


def _small_request_and_bundle() -> tuple[
    ReviewerGenerateRequest,
    ReviewerSourceBundle,
]:
    """Return material that fits in one reviewer prompt."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        reviewer_length=ReviewerLength.MEDIUM,
    )

    bundle = ReviewerSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.FILE,
        study_file_id=file_id,
        chunks=(
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Small Lecture.pdf",
                chunk_index=0,
                content=(
                    "SMALL-"
                    + ("A" * 494)
                ),
            ),
        ),
    )

    return request, bundle


def _large_request_and_bundle() -> tuple[
    ReviewerGenerateRequest,
    ReviewerSourceBundle,
]:
    """Return material that requires three source batches."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        reviewer_length=ReviewerLength.LONG,
    )

    bundle = ReviewerSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.FILE,
        study_file_id=file_id,
        chunks=(
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Large Lecture.pdf",
                chunk_index=0,
                content=(
                    "FIRST-"
                    + ("A" * 594)
                ),
            ),
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Large Lecture.pdf",
                chunk_index=1,
                content=(
                    "SECOND-"
                    + ("B" * 593)
                ),
            ),
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Large Lecture.pdf",
                chunk_index=2,
                content=(
                    "THIRD-"
                    + ("C" * 594)
                ),
            ),
        ),
    )

    return request, bundle


@async_test
async def test_small_material_keeps_single_pass_generation() -> None:
    """Normal material must continue using the existing one-call flow."""

    provider = FakeGenerationProvider(
        [
            _provider_result(
                overview="Small reviewer.",
                topic_title="Small Topic",
            ),
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
        prompt_builder=ReviewerPromptBuilder(
            max_source_characters=1_000,
        ),
        source_batcher=ReviewerSourceBatcher(
            max_source_characters=1_000,
        ),
    )

    request, bundle = (
        _small_request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        provider.requests,
    ) == 1

    assert (
        "PARTIAL_SOURCE_BATCH"
        not in provider.requests[
            0
        ].prompt
    )

    assert (
        result.content.topics[
            0
        ].title
        == "Small Topic"
    )

    assert result.source_chunk_count == 1
    assert result.source_file_count == 1
    assert result.source_character_count == 500


@async_test
async def test_large_material_generates_batches_then_synthesizes() -> None:
    """Large material must generate partial reviewers then one final reviewer."""

    provider = FakeGenerationProvider(
        [
            _provider_result(
                overview="First batch.",
                topic_title="First Topic",
            ),
            _provider_result(
                overview="Second batch.",
                topic_title="Second Topic",
            ),
            _provider_result(
                overview="Third batch.",
                topic_title="Third Topic",
            ),
            _provider_result(
                overview="Combined reviewer.",
                topic_title="Combined Topic",
            ),
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
        prompt_builder=ReviewerPromptBuilder(
            max_source_characters=1_000,
        ),
        source_batcher=ReviewerSourceBatcher(
            max_source_characters=1_000,
        ),
    )

    request, bundle = (
        _large_request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        provider.requests,
    ) == 4

    assert (
        "PARTIAL_SOURCE_BATCH"
        in provider.requests[
            0
        ].prompt
    )

    assert (
        "PARTIAL_SOURCE_BATCH"
        in provider.requests[
            1
        ].prompt
    )

    assert (
        "PARTIAL_SOURCE_BATCH"
        in provider.requests[
            2
        ].prompt
    )

    assert (
        "FIRST-"
        in provider.requests[
            0
        ].prompt
    )

    assert (
        "SECOND-"
        in provider.requests[
            1
        ].prompt
    )

    assert (
        "THIRD-"
        in provider.requests[
            2
        ].prompt
    )

    assert (
        "SECOND-"
        not in provider.requests[
            0
        ].prompt
    )

    assert (
        "THIRD-"
        not in provider.requests[
            0
        ].prompt
    )

    final_prompt = provider.requests[
        3
    ].prompt

    assert (
        "PARTIAL_REVIEWERS_JSON"
        in final_prompt
    )

    assert "First Topic" in final_prompt
    assert "Second Topic" in final_prompt
    assert "Third Topic" in final_prompt

    assert (
        result.content.overview
        == "Combined reviewer."
    )

    assert (
        result.content.topics[
            0
        ].title
        == "Combined Topic"
    )

    assert result.provider == "fake"
    assert result.model == "fake-model"

    assert result.source_chunk_count == 3
    assert result.source_file_count == 1

    assert (
        result.source_character_count
        == 1_800
    )


@async_test
async def test_large_generation_result_describes_complete_bundle() -> None:
    """Final metadata must describe all original material, not one batch."""

    provider = FakeGenerationProvider(
        [
            _provider_result(
                overview="First.",
                topic_title="Topic One",
            ),
            _provider_result(
                overview="Second.",
                topic_title="Topic Two",
            ),
            _provider_result(
                overview="Third.",
                topic_title="Topic Three",
            ),
            _provider_result(
                overview="Final.",
                topic_title="Final Topic",
            ),
        ]
    )

    service = ReviewerGenerationService(
        provider=provider,
        prompt_builder=ReviewerPromptBuilder(
            max_source_characters=1_000,
        ),
        source_batcher=ReviewerSourceBatcher(
            max_source_characters=1_000,
        ),
    )

    request, bundle = (
        _large_request_and_bundle()
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    expected_character_count = sum(
        len(
            chunk.content,
        )
        for chunk in bundle.chunks
    )

    assert (
        result.source_character_count
        == expected_character_count
    )

    assert (
        result.source_chunk_count
        == bundle.chunk_count
    )

    assert (
        result.source_file_count
        == bundle.file_count
    )

    assert result.generation_attempt_count == 1