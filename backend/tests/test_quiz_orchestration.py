# File: /backend/tests/test_quiz_orchestration.py

# Purpose: Verifies Quiz source loading, generation metadata,
# ownership validation, and persistence orchestration.

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec
from uuid import UUID, uuid4

import pytest

from app.schemas.quiz import (
    QuizDifficulty,
    QuizGeneratedContent,
    QuizGeneratedQuestion,
    QuizGenerateRequest,
    QuizQuestionResponse,
    QuizQuestionType,
    QuizResponse,
    QuizScopeType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizGenerationResponseError,
    QuizValidationError,
)
from app.services.quiz_generation import (
    QuizGenerationResult,
)
from app.services.quiz_orchestration import (
    QuizOrchestrationService,
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


def _request_and_bundle(
    *,
    user_id: UUID | None = None,
) -> tuple[
    UUID,
    QuizGenerateRequest,
    QuizSourceBundle,
]:
    """Return matching file-scoped Quiz inputs."""

    resolved_user_id = (
        user_id
        if user_id is not None
        else uuid4()
    )

    subject_id = uuid4()
    file_id = uuid4()

    request = QuizGenerateRequest(
        scope_type=QuizScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=1,
    )

    bundle = QuizSourceBundle(
        user_id=resolved_user_id,
        subject_id=subject_id,
        scope_type=QuizScopeType.FILE,
        study_file_id=file_id,
        chunks=(
            QuizSourceChunk(
                study_file_id=file_id,
                source_name="Rizal Lecture.pdf",
                chunk_index=0,
                content="Jose Rizal wrote Noli Me Tangere.",
                locator_type="page",
                locator_label="Page 1",
            ),
        ),
    )

    return (
        resolved_user_id,
        request,
        bundle,
    )


def _content() -> QuizGeneratedContent:
    """Return one valid generated Quiz."""

    return QuizGeneratedContent(
        title="Rizal Quiz",
        questions=(
            QuizGeneratedQuestion(
                position=1,
                question_type=(
                    QuizQuestionType.MULTIPLE_CHOICE
                ),
                topic="Rizal",
                question="Who wrote Noli Me Tangere?",
                choices=(
                    "Jose Rizal",
                    "Andres Bonifacio",
                ),
                correct_answer="Jose Rizal",
                explanation="Jose Rizal wrote the novel.",
            ),
        ),
    )


def _generation_result(
    bundle: QuizSourceBundle,
) -> QuizGenerationResult:
    """Return generation metadata matching the source bundle."""

    return QuizGenerationResult(
        content=_content(),
        provider="fake",
        model="fake-model",
        input_tokens=100,
        output_tokens=200,
        generation_attempt_count=1,
        source_character_count=(
            bundle.character_count
        ),
        source_chunk_count=(
            bundle.chunk_count
        ),
        source_file_count=(
            bundle.file_count
        ),
    )


class FakeSourceLoader:
    """Return one controlled Quiz source bundle."""

    def __init__(
        self,
        bundle: QuizSourceBundle,
    ) -> None:
        self.bundle = bundle

        self.user_id: UUID | None = None
        self.request: QuizGenerateRequest | None = None

    async def load(
        self,
        *,
        user_id: UUID,
        request: QuizGenerateRequest,
    ) -> QuizSourceBundle:
        self.user_id = user_id
        self.request = request

        return self.bundle


class FakeGenerationService:
    """Return one controlled Quiz generation result."""

    def __init__(
        self,
        result: QuizGenerationResult,
    ) -> None:
        self.result = result

        self.request: QuizGenerateRequest | None = None
        self.bundle: QuizSourceBundle | None = None

    async def generate(
        self,
        *,
        request: QuizGenerateRequest,
        source_bundle: QuizSourceBundle,
    ) -> QuizGenerationResult:
        self.request = request
        self.bundle = source_bundle

        return self.result


class FakeQuizService:
    """Record generated Quiz persistence."""

    def __init__(
        self,
    ) -> None:
        self.arguments: dict[
            str,
            object,
        ] | None = None

    def save_generated_quiz(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: QuizScopeType,
        quiz_type: QuizType,
        difficulty: QuizDifficulty,
        question_count: int,
        content: QuizGeneratedContent,
        generation_model: str,
    ) -> QuizResponse:
        self.arguments = {
            "user_id": user_id,
            "subject_id": subject_id,
            "study_file_id": study_file_id,
            "scope_type": scope_type,
            "quiz_type": quiz_type,
            "difficulty": difficulty,
            "question_count": question_count,
            "content": content,
            "generation_model": generation_model,
        }

        now = datetime.now(
            UTC,
        )

        public_questions = tuple(
            QuizQuestionResponse(
                id=uuid4(),
                position=question.position,
                question_type=question.question_type,
                topic=question.topic,
                question=question.question,
                choices=question.choices,
            )
            for question in content.questions
        )

        return QuizResponse(
            id=uuid4(),
            subject_id=subject_id,
            study_file_id=study_file_id,
            scope_type=scope_type,
            title=content.title,
            quiz_type=quiz_type,
            difficulty=difficulty,
            question_count=question_count,
            questions=public_questions,
            generation_model=generation_model,
            generation_count=1,
            generated_at=now,
            created_at=now,
            updated_at=now,
        )


@async_test
async def test_file_quiz_is_generated_and_saved() -> None:
    """File scope must execute the complete Quiz workflow."""

    user_id, request, bundle = (
        _request_and_bundle()
    )

    source_loader = FakeSourceLoader(
        bundle,
    )

    generation_service = FakeGenerationService(
        _generation_result(
            bundle,
        ),
    )

    quiz_service = FakeQuizService()

    orchestration = QuizOrchestrationService(
        source_loader=source_loader,
        generation_service=generation_service,
        quiz_service=quiz_service,
    )

    result = await orchestration.generate_quiz(
        user_id=user_id,
        request=request,
    )

    assert result.title == "Rizal Quiz"

    assert (
        result.quiz_type
        == QuizType.MULTIPLE_CHOICE
    )

    assert result.generation_model == "fake-model"

    assert result.study_file_id == (
        request.study_file_id
    )

    assert source_loader.user_id == user_id

    assert generation_service.bundle is bundle

    assert quiz_service.arguments is not None

    assert (
        quiz_service.arguments[
            "difficulty"
        ]
        == QuizDifficulty.MEDIUM
    )


@async_test
async def test_source_owner_must_match_authenticated_user() -> None:
    """Loaded Quiz material must belong to the caller."""

    user_id, request, bundle = (
        _request_and_bundle()
    )

    wrong_owner_bundle = QuizSourceBundle(
        user_id=uuid4(),
        subject_id=bundle.subject_id,
        scope_type=bundle.scope_type,
        study_file_id=bundle.study_file_id,
        chunks=bundle.chunks,
    )

    orchestration = QuizOrchestrationService(
        source_loader=FakeSourceLoader(
            wrong_owner_bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(
                wrong_owner_bundle,
            ),
        ),
        quiz_service=FakeQuizService(),
    )

    with pytest.raises(
        QuizValidationError,
    ):
        await orchestration.generate_quiz(
            user_id=user_id,
            request=request,
        )


@async_test
async def test_source_subject_must_match_request() -> None:
    """Loaded Quiz material must match the requested subject."""

    user_id, request, bundle = (
        _request_and_bundle()
    )

    mismatched_bundle = QuizSourceBundle(
        user_id=user_id,
        subject_id=uuid4(),
        scope_type=bundle.scope_type,
        study_file_id=bundle.study_file_id,
        chunks=bundle.chunks,
    )

    orchestration = QuizOrchestrationService(
        source_loader=FakeSourceLoader(
            mismatched_bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(
                mismatched_bundle,
            ),
        ),
        quiz_service=FakeQuizService(),
    )

    with pytest.raises(
        QuizValidationError,
    ):
        await orchestration.generate_quiz(
            user_id=user_id,
            request=request,
        )


@async_test
async def test_generation_metadata_must_match_sources() -> None:
    """Generation metadata cannot describe different source data."""

    user_id, request, bundle = (
        _request_and_bundle()
    )

    generation = _generation_result(
        bundle,
    )

    bad_generation = QuizGenerationResult(
        content=generation.content,
        provider=generation.provider,
        model=generation.model,
        input_tokens=generation.input_tokens,
        output_tokens=generation.output_tokens,
        generation_attempt_count=(
            generation.generation_attempt_count
        ),
        source_character_count=(
            generation.source_character_count
        ),
        source_chunk_count=(
            generation.source_chunk_count
            + 1
        ),
        source_file_count=(
            generation.source_file_count
        ),
    )

    orchestration = QuizOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            bad_generation,
        ),
        quiz_service=FakeQuizService(),
    )

    with pytest.raises(
        QuizGenerationResponseError,
    ):
        await orchestration.generate_quiz(
            user_id=user_id,
            request=request,
        )


@async_test
async def test_subject_scope_preserves_null_study_file() -> None:
    """Subject Quiz persistence must not invent one study file."""

    user_id = uuid4()
    subject_id = uuid4()

    first_file_id = uuid4()
    second_file_id = uuid4()

    request = QuizGenerateRequest(
        scope_type=QuizScopeType.SUBJECT,
        subject_id=subject_id,
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.EASY,
        question_count=1,
    )

    bundle = QuizSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=QuizScopeType.SUBJECT,
        study_file_id=None,
        chunks=(
            QuizSourceChunk(
                study_file_id=first_file_id,
                source_name="Week 1.pdf",
                chunk_index=0,
                content="Jose Rizal wrote Noli Me Tangere.",
            ),
            QuizSourceChunk(
                study_file_id=second_file_id,
                source_name="Week 2.pdf",
                chunk_index=0,
                content="The novel criticized colonial abuses.",
            ),
        ),
    )

    quiz_service = FakeQuizService()

    orchestration = QuizOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(
                bundle,
            ),
        ),
        quiz_service=quiz_service,
    )

    result = await orchestration.generate_quiz(
        user_id=user_id,
        request=request,
    )

    assert result.study_file_id is None

    assert quiz_service.arguments is not None

    assert (
        quiz_service.arguments[
            "study_file_id"
        ]
        is None
    )