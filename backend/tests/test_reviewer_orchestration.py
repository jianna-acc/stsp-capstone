# File: /backend/tests/test_reviewer_orchestration.py
# Purpose: Verifies reviewer source loading, generation,
# source tracking, title creation, and persistence orchestration.

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Sequence
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec
from uuid import UUID, uuid4

import pytest

from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerDefinition,
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerLocatorType,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
    ReviewerTopic,
)
from app.services.reviewer_errors import (
    ReviewerGenerationResponseError,
    ReviewerValidationError,
)
from app.services.reviewer_generation import (
    ReviewerGenerationResult,
)
from app.services.reviewer_orchestration import (
    ReviewerOrchestrationService,
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
    """Run async tests without an external pytest plugin."""

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


def _content() -> ReviewerContent:
    """Return valid reviewer content."""

    return ReviewerContent(
        overview="Lesson overview.",
        topics=(
            ReviewerTopic(
                title="Core Topic",
                summary="Core topic summary.",
                key_points=(
                    "Important point.",
                ),
                definitions=(
                    ReviewerDefinition(
                        term="Concept",
                        definition="Concept definition.",
                    ),
                ),
            ),
        ),
    )


def _file_request_and_bundle(
    *,
    user_id: UUID | None = None,
) -> tuple[
    UUID,
    ReviewerGenerateRequest,
    ReviewerSourceBundle,
]:
    """Return matching file-scoped reviewer inputs."""

    resolved_user_id = (
        user_id
        if user_id is not None
        else uuid4()
    )

    subject_id = uuid4()
    file_id = uuid4()

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        reviewer_length=ReviewerLength.MEDIUM,
    )

    bundle = ReviewerSourceBundle(
        user_id=resolved_user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.FILE,
        study_file_id=file_id,
        chunks=(
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Financial Management.pdf",
                chunk_index=0,
                content="First lesson section.",
                locator_type=ReviewerLocatorType.PAGE,
                locator_label="Page 1",
            ),
            ReviewerSourceChunk(
                study_file_id=file_id,
                source_name="Financial Management.pdf",
                chunk_index=1,
                content="Second lesson section.",
                locator_type=ReviewerLocatorType.PAGE,
                locator_label="Page 2",
            ),
        ),
    )

    return (
        resolved_user_id,
        request,
        bundle,
    )


class FakeSourceLoader:
    """Return one controlled source bundle."""

    def __init__(
        self,
        bundle: ReviewerSourceBundle,
    ) -> None:
        self.bundle = bundle

        self.user_id: UUID | None = None
        self.request: ReviewerGenerateRequest | None = None

    async def load(
        self,
        *,
        user_id: UUID,
        request: ReviewerGenerateRequest,
    ) -> ReviewerSourceBundle:
        self.user_id = user_id
        self.request = request

        return self.bundle


class FakeGenerationService:
    """Return one controlled generation result."""

    def __init__(
        self,
        result: ReviewerGenerationResult,
    ) -> None:
        self.result = result

        self.request: ReviewerGenerateRequest | None = None
        self.bundle: ReviewerSourceBundle | None = None

    async def generate(
        self,
        *,
        request: ReviewerGenerateRequest,
        source_bundle: ReviewerSourceBundle,
    ) -> ReviewerGenerationResult:
        self.request = request
        self.bundle = source_bundle

        return self.result


class FakeReviewerService:
    """Record generated reviewer persistence."""

    def __init__(
        self,
    ) -> None:
        self.arguments: dict[
            str,
            object,
        ] | None = None

    def save_generated_reviewer(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: ReviewerScopeType,
        title: str,
        reviewer_length: ReviewerLength,
        content: ReviewerContent,
        sources: Sequence[
            ReviewerSource
        ],
        generation_model: str,
    ) -> ReviewerResponse:
        self.arguments = {
            "user_id": user_id,
            "subject_id": subject_id,
            "study_file_id": study_file_id,
            "scope_type": scope_type,
            "title": title,
            "reviewer_length": reviewer_length,
            "content": content,
            "sources": tuple(
                sources,
            ),
            "generation_model": generation_model,
        }

        now = datetime.now(
            UTC,
        )

        return ReviewerResponse(
            id=uuid4(),
            subject_id=subject_id,
            study_file_id=study_file_id,
            scope_type=scope_type,
            title=title,
            reviewer_length=reviewer_length,
            content=content,
            sources=tuple(
                sources,
            ),
            generation_model=generation_model,
            generation_count=1,
            generated_at=now,
            created_at=now,
            updated_at=now,
        )


def _generation_result(
    bundle: ReviewerSourceBundle,
) -> ReviewerGenerationResult:
    """Return generation metadata matching a bundle."""

    return ReviewerGenerationResult(
        content=_content(),
        provider="fake",
        model="fake-model",
        input_tokens=100,
        output_tokens=200,
        generation_attempt_count=1,
        source_character_count=sum(
            len(
                chunk.content,
            )
            for chunk in bundle.chunks
        ),
        source_chunk_count=bundle.chunk_count,
        source_file_count=bundle.file_count,
    )


@async_test
async def test_file_reviewer_is_generated_and_saved() -> None:
    """File scope must run the complete reviewer workflow."""

    user_id, request, bundle = (
        _file_request_and_bundle()
    )

    source_loader = FakeSourceLoader(
        bundle,
    )

    generation_service = FakeGenerationService(
        _generation_result(
            bundle,
        ),
    )

    reviewer_service = FakeReviewerService()

    orchestration = ReviewerOrchestrationService(
        source_loader=source_loader,
        generation_service=generation_service,
        reviewer_service=reviewer_service,
    )

    result = await orchestration.generate_reviewer(
        user_id=user_id,
        request=request,
    )

    assert (
        result.title
        == "Financial Management Reviewer"
    )

    assert result.generation_model == "fake-model"
    assert result.study_file_id == request.study_file_id

    assert source_loader.user_id == user_id

    assert (
        generation_service.bundle
        is bundle
    )


@async_test
async def test_saved_sources_preserve_chunk_locations() -> None:
    """Saved reviewer must expose all source locations used."""

    user_id, request, bundle = (
        _file_request_and_bundle()
    )

    reviewer_service = FakeReviewerService()

    orchestration = ReviewerOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(
                bundle,
            ),
        ),
        reviewer_service=reviewer_service,
    )

    await orchestration.generate_reviewer(
        user_id=user_id,
        request=request,
    )

    assert reviewer_service.arguments is not None

    sources = reviewer_service.arguments[
        "sources"
    ]

    assert isinstance(
        sources,
        tuple,
    )

    assert len(
        sources,
    ) == 2

    first_source = sources[
        0
    ]

    assert isinstance(
        first_source,
        ReviewerSource,
    )

    assert first_source.chunk_index == 0
    assert first_source.locator_label == "Page 1"


@async_test
async def test_subject_scope_creates_subject_title() -> None:
    """Subject-wide reviewers must receive a stable title."""

    user_id = uuid4()
    subject_id = uuid4()

    first_file_id = uuid4()
    second_file_id = uuid4()

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.SUBJECT,
        subject_id=subject_id,
        reviewer_length=ReviewerLength.LONG,
    )

    bundle = ReviewerSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.SUBJECT,
        study_file_id=None,
        chunks=(
            ReviewerSourceChunk(
                study_file_id=first_file_id,
                source_name="Week 1.pdf",
                chunk_index=0,
                content="Week one content.",
            ),
            ReviewerSourceChunk(
                study_file_id=second_file_id,
                source_name="Week 2.pdf",
                chunk_index=0,
                content="Week two content.",
            ),
        ),
    )

    orchestration = ReviewerOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(
                bundle,
            ),
        ),
        reviewer_service=FakeReviewerService(),
    )

    result = await orchestration.generate_reviewer(
        user_id=user_id,
        request=request,
    )

    assert result.title == (
        "Subject Reviewer (2 files)"
    )

    assert result.study_file_id is None
    assert result.scope_type == ReviewerScopeType.SUBJECT


@async_test
async def test_source_owner_mismatch_is_rejected() -> None:
    """Orchestration must defend against mismatched source ownership."""

    authenticated_user_id = uuid4()

    _, request, bundle = (
        _file_request_and_bundle(
            user_id=uuid4(),
        )
    )

    orchestration = ReviewerOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(
                bundle,
            ),
        ),
        reviewer_service=FakeReviewerService(),
    )

    with pytest.raises(
        ReviewerValidationError,
    ):
        await orchestration.generate_reviewer(
            user_id=authenticated_user_id,
            request=request,
        )


@async_test
async def test_generation_metadata_mismatch_is_rejected() -> None:
    """Saved source metadata must match what the generator received."""

    user_id, request, bundle = (
        _file_request_and_bundle()
    )

    invalid_generation = ReviewerGenerationResult(
        content=_content(),
        provider="fake",
        model="fake-model",
        input_tokens=None,
        output_tokens=None,
        generation_attempt_count=1,
        source_character_count=sum(
            len(
                chunk.content,
            )
            for chunk in bundle.chunks
        ),
        source_chunk_count=1,
        source_file_count=bundle.file_count,
    )

    reviewer_service = FakeReviewerService()

    orchestration = ReviewerOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            invalid_generation,
        ),
        reviewer_service=reviewer_service,
    )

    with pytest.raises(
        ReviewerGenerationResponseError,
    ):
        await orchestration.generate_reviewer(
            user_id=user_id,
            request=request,
        )

    assert reviewer_service.arguments is None