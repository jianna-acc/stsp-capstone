# File: /backend/tests/test_quiz_attempt_service.py

# Purpose: Verifies Quiz-attempt lifecycle, answer submission,
# final scoring, and strong/weak topic classification.

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.quiz_attempt_repository import (
    QuizAnswerSubmissionResult,
)
from app.schemas.quiz import (
    QuizAnswerFeedbackResponse,
    QuizAnswerSubmissionRequest,
    QuizAttemptAnswerResponse,
    QuizAttemptResponse,
    QuizAttemptStatus,
    QuizQuestionType,
)
from app.services.quiz_attempt_errors import (
    QuizAttemptConflictError,
    QuizAttemptNotFoundError,
    QuizAttemptResponseError,
)
from app.services.quiz_attempt_service import (
    QuizAttemptService,
)


def _attempt(
    *,
    attempt_id: UUID | None = None,
    quiz_id: UUID | None = None,
    completed: bool = False,
    correct_count: int = 0,
    question_count: int = 3,
) -> QuizAttemptResponse:
    """Return one valid Quiz attempt."""

    now = datetime.now(
        UTC,
    )

    return QuizAttemptResponse(
        id=(
            attempt_id
            if attempt_id is not None
            else uuid4()
        ),
        quiz_id=(
            quiz_id
            if quiz_id is not None
            else uuid4()
        ),
        status=(
            QuizAttemptStatus.COMPLETED
            if completed
            else QuizAttemptStatus.IN_PROGRESS
        ),
        current_position=(
            question_count + 1
            if completed
            else 1
        ),
        correct_count=correct_count,
        question_count=question_count,
        score_percentage=round(
            (
                correct_count
                / question_count
            )
            * 100,
            2,
        ),
        started_at=now,
        completed_at=(
            now
            if completed
            else None
        ),
        created_at=now,
        updated_at=now,
    )


def _answer(
    *,
    attempt_id: UUID,
    position: int,
    topic: str,
    is_correct: bool,
) -> QuizAttemptAnswerResponse:
    """Return one persisted answer."""

    now = datetime.now(
        UTC,
    )

    return QuizAttemptAnswerResponse(
        id=uuid4(),
        attempt_id=attempt_id,
        quiz_question_id=uuid4(),
        position=position,
        topic=topic,
        question_type=(
            QuizQuestionType.MULTIPLE_CHOICE
        ),
        submitted_answer="Answer",
        is_correct=is_correct,
        answered_at=now,
        created_at=now,
    )


class FakeQuizAttemptRepository:
    """Controlled persistence dependency."""

    def __init__(
        self,
    ) -> None:
        self.attempts: dict[
            UUID,
            QuizAttemptResponse,
        ] = {}

        self.answers: dict[
            UUID,
            tuple[
                QuizAttemptAnswerResponse,
                ...,
            ],
        ] = {}

        self.started: tuple[
            UUID,
            UUID,
        ] | None = None

        self.submitted: dict[
            str,
            object,
        ] | None = None

    def start_attempt(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizAttemptResponse:
        self.started = (
            user_id,
            quiz_id,
        )

        result = _attempt(
            quiz_id=quiz_id,
        )

        self.attempts[
            result.id
        ] = result

        return result

    def submit_answer(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
        position: int,
        submitted_answer: str,
    ) -> QuizAnswerSubmissionResult:
        self.submitted = {
            "user_id": user_id,
            "attempt_id": attempt_id,
            "position": position,
            "submitted_answer": submitted_answer,
        }

        attempt = self.attempts[
            attempt_id
        ]

        return QuizAnswerSubmissionResult(
            attempt=attempt,
            feedback=QuizAnswerFeedbackResponse(
                attempt_id=attempt_id,
                quiz_question_id=uuid4(),
                position=position,
                is_correct=True,
                correct_answer="Jose Rizal",
                explanation="The source identifies Jose Rizal.",
                next_position=position + 1,
                attempt_completed=False,
            ),
        )

    def get_attempt(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResponse | None:
        return self.attempts.get(
            attempt_id,
        )

    def list_answers(
        self,
        *,
        attempt_id: UUID,
    ) -> tuple[
        QuizAttemptAnswerResponse,
        ...,
    ]:
        return self.answers.get(
            attempt_id,
            (),
        )


def test_start_attempt_forwards_authenticated_owner() -> None:
    """Attempt creation must preserve owner and Quiz ID."""

    repository = FakeQuizAttemptRepository()

    service = QuizAttemptService(
        repository,
    )

    user_id = uuid4()
    quiz_id = uuid4()

    result = service.start_attempt(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    assert result.quiz_id == quiz_id

    assert repository.started == (
        user_id,
        quiz_id,
    )


def test_submit_answer_forwards_expected_position() -> None:
    """Answer submission must preserve its expected question position."""

    repository = FakeQuizAttemptRepository()

    service = QuizAttemptService(
        repository,
    )

    user_id = uuid4()
    quiz_id = uuid4()

    attempt = repository.start_attempt(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    service.submit_answer(
        user_id=user_id,
        attempt_id=attempt.id,
        position=1,
        request=QuizAnswerSubmissionRequest(
            answer="  Jose Rizal  ",
        ),
    )

    assert repository.submitted is not None

    assert (
        repository.submitted[
            "position"
        ]
        == 1
    )

    assert (
        repository.submitted[
            "submitted_answer"
        ]
        == "Jose Rizal"
    )


def test_missing_attempt_raises_not_found() -> None:
    """Owned attempt lookup must fail safely."""

    service = QuizAttemptService(
        FakeQuizAttemptRepository(),
    )

    with pytest.raises(
        QuizAttemptNotFoundError,
    ):
        service.get_attempt(
            user_id=uuid4(),
            attempt_id=uuid4(),
        )


def test_in_progress_attempt_has_no_final_result() -> None:
    """Final results require completion."""

    repository = FakeQuizAttemptRepository()

    service = QuizAttemptService(
        repository,
    )

    attempt = _attempt(
        completed=False,
    )

    repository.attempts[
        attempt.id
    ] = attempt

    with pytest.raises(
        QuizAttemptConflictError,
    ):
        service.get_result(
            user_id=uuid4(),
            attempt_id=attempt.id,
        )


def test_completed_attempt_builds_strong_and_weak_topics() -> None:
    """Topic accuracy >=70% is strong; lower accuracy is weak."""

    repository = FakeQuizAttemptRepository()

    service = QuizAttemptService(
        repository,
    )

    attempt = _attempt(
        completed=True,
        correct_count=3,
        question_count=4,
    )

    repository.attempts[
        attempt.id
    ] = attempt

    repository.answers[
        attempt.id
    ] = (
        _answer(
            attempt_id=attempt.id,
            position=1,
            topic="Rizal",
            is_correct=True,
        ),
        _answer(
            attempt_id=attempt.id,
            position=2,
            topic="Rizal",
            is_correct=True,
        ),
        _answer(
            attempt_id=attempt.id,
            position=3,
            topic="Reform Movement",
            is_correct=True,
        ),
        _answer(
            attempt_id=attempt.id,
            position=4,
            topic="Reform Movement",
            is_correct=False,
        ),
    )

    result = service.get_result(
        user_id=uuid4(),
        attempt_id=attempt.id,
    )

    assert result.correct_count == 3
    assert result.score_percentage == 75

    assert [
        topic.topic
        for topic in result.strong_topics
    ] == [
        "Rizal",
    ]

    assert [
        topic.topic
        for topic in result.weak_topics
    ] == [
        "Reform Movement",
    ]

    assert (
        result.strong_topics[
            0
        ].accuracy_percentage
        == 100
    )

    assert (
        result.weak_topics[
            0
        ].accuracy_percentage
        == 50
    )


def test_completed_attempt_requires_complete_answer_history() -> None:
    """Corrupt completed attempts must not produce misleading results."""

    repository = FakeQuizAttemptRepository()

    service = QuizAttemptService(
        repository,
    )

    attempt = _attempt(
        completed=True,
        correct_count=1,
        question_count=2,
    )

    repository.attempts[
        attempt.id
    ] = attempt

    repository.answers[
        attempt.id
    ] = (
        _answer(
            attempt_id=attempt.id,
            position=1,
            topic="Rizal",
            is_correct=True,
        ),
    )

    with pytest.raises(
        QuizAttemptResponseError,
    ):
        service.get_result(
            user_id=uuid4(),
            attempt_id=attempt.id,
        )