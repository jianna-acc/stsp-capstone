# File: /backend/tests/test_quiz_service.py

# Purpose: Verifies Quiz persistence service creation,
# retrieval, deletion, and owned not-found handling.

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.schemas.quiz import (
    QuizDifficulty,
    QuizGeneratedContent,
    QuizGeneratedQuestion,
    QuizQuestionResponse,
    QuizQuestionType,
    QuizResponse,
    QuizScopeType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizNotFoundError,
)
from app.services.quiz_service import (
    QuizService,
)


def _content() -> QuizGeneratedContent:
    """Return one valid private generated Quiz."""

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


def _response(
    *,
    quiz_id: UUID | None = None,
    subject_id: UUID | None = None,
) -> QuizResponse:
    """Return one student-safe Quiz response."""

    now = datetime.now(
        UTC,
    )

    return QuizResponse(
        id=(
            quiz_id
            if quiz_id is not None
            else uuid4()
        ),
        subject_id=(
            subject_id
            if subject_id is not None
            else uuid4()
        ),
        scope_type=QuizScopeType.SUBJECT,
        title="Rizal Quiz",
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=1,
        questions=(
            QuizQuestionResponse(
                id=uuid4(),
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
            ),
        ),
        generation_model="fake-model",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


class FakeQuizRepository:
    """Controlled repository dependency for QuizService."""

    def __init__(
        self,
    ) -> None:
        self.created_arguments: dict[
            str,
            object,
        ] | None = None

        self.quiz_by_id: dict[
            UUID,
            QuizResponse,
        ] = {}

        self.deleted_ids: list[
            UUID
        ] = []

        self.get_user_id: UUID | None = None
        self.delete_user_id: UUID | None = None

    def create_quiz(
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
        self.created_arguments = {
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

        return _response(
            subject_id=subject_id,
        )

    def get_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizResponse | None:
        self.get_user_id = user_id

        return self.quiz_by_id.get(
            quiz_id,
        )

    def delete_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> bool:
        self.delete_user_id = user_id

        if quiz_id not in self.quiz_by_id:
            return False

        self.deleted_ids.append(
            quiz_id,
        )

        del self.quiz_by_id[
            quiz_id
        ]

        return True


def test_save_generated_quiz_forwards_generation_data() -> None:
    """Generated Quiz data must be forwarded to persistence."""

    repository = FakeQuizRepository()

    service = QuizService(
        repository,
    )

    user_id = uuid4()
    subject_id = uuid4()

    content = _content()

    result = service.save_generated_quiz(
        user_id=user_id,
        subject_id=subject_id,
        study_file_id=None,
        scope_type=QuizScopeType.SUBJECT,
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=1,
        content=content,
        generation_model="fake-model",
    )

    assert result.subject_id == subject_id

    assert (
        repository.created_arguments
        is not None
    )

    assert (
        repository.created_arguments[
            "user_id"
        ]
        == user_id
    )

    assert (
        repository.created_arguments[
            "content"
        ]
        is content
    )

    assert (
        repository.created_arguments[
            "generation_model"
        ]
        == "fake-model"
    )


def test_get_existing_quiz_succeeds() -> None:
    """Existing owned Quiz must be returned."""

    repository = FakeQuizRepository()

    service = QuizService(
        repository,
    )

    user_id = uuid4()
    quiz_id = uuid4()

    expected = _response(
        quiz_id=quiz_id,
    )

    repository.quiz_by_id[
        quiz_id
    ] = expected

    result = service.get_quiz(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    assert result is expected
    assert repository.get_user_id == user_id


def test_get_missing_quiz_raises_not_found() -> None:
    """Missing Quiz retrieval must fail safely."""

    service = QuizService(
        FakeQuizRepository(),
    )

    with pytest.raises(
        QuizNotFoundError,
    ):
        service.get_quiz(
            user_id=uuid4(),
            quiz_id=uuid4(),
        )


def test_delete_existing_quiz_succeeds() -> None:
    """Existing owned Quiz must be deletable."""

    repository = FakeQuizRepository()

    service = QuizService(
        repository,
    )

    user_id = uuid4()
    quiz_id = uuid4()

    repository.quiz_by_id[
        quiz_id
    ] = _response(
        quiz_id=quiz_id,
    )

    service.delete_quiz(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    assert quiz_id in repository.deleted_ids
    assert repository.delete_user_id == user_id


def test_delete_missing_quiz_raises_not_found() -> None:
    """Missing Quiz deletion must fail safely."""

    service = QuizService(
        FakeQuizRepository(),
    )

    with pytest.raises(
        QuizNotFoundError,
    ):
        service.delete_quiz(
            user_id=uuid4(),
            quiz_id=uuid4(),
        )