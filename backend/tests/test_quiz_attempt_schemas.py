# File: /backend/tests/test_quiz_attempt_schemas.py

# Purpose: Verifies Quiz attempt, answer-submission,
# immediate-feedback, scoring, and topic-result contracts.

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.quiz import (
    QuizAnswerFeedbackResponse,
    QuizAnswerSubmissionRequest,
    QuizAttemptAnswerResponse,
    QuizAttemptResponse,
    QuizAttemptResultResponse,
    QuizAttemptStatus,
    QuizQuestionType,
    QuizTopicResult,
)


def test_answer_submission_is_normalized() -> None:
    """Submitted answers must be trimmed before grading."""

    request = QuizAnswerSubmissionRequest(
        answer="  Jose Rizal  ",
    )

    assert request.answer == "Jose Rizal"


def test_blank_answer_submission_is_rejected() -> None:
    """Students cannot submit an empty Quiz answer."""

    with pytest.raises(
        ValidationError,
    ):
        QuizAnswerSubmissionRequest(
            answer="   ",
        )


def test_in_progress_attempt_is_valid() -> None:
    """Active attempts must point to an unanswered question."""

    now = datetime.now(
        UTC,
    )

    attempt = QuizAttemptResponse(
        id=uuid4(),
        quiz_id=uuid4(),
        status=QuizAttemptStatus.IN_PROGRESS,
        current_position=2,
        correct_count=1,
        question_count=5,
        score_percentage=20,
        started_at=now,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )

    assert (
        attempt.status
        == QuizAttemptStatus.IN_PROGRESS
    )

    assert attempt.current_position == 2


def test_completed_attempt_requires_terminal_position() -> None:
    """Completed attempts must advance beyond the final question."""

    now = datetime.now(
        UTC,
    )

    attempt = QuizAttemptResponse(
        id=uuid4(),
        quiz_id=uuid4(),
        status=QuizAttemptStatus.COMPLETED,
        current_position=6,
        correct_count=4,
        question_count=5,
        score_percentage=80,
        started_at=now,
        completed_at=now,
        created_at=now,
        updated_at=now,
    )

    assert (
        attempt.status
        == QuizAttemptStatus.COMPLETED
    )

    assert attempt.current_position == 6


def test_completed_attempt_requires_completed_at() -> None:
    """Completed attempts cannot omit their completion time."""

    now = datetime.now(
        UTC,
    )

    with pytest.raises(
        ValidationError,
    ):
        QuizAttemptResponse(
            id=uuid4(),
            quiz_id=uuid4(),
            status=QuizAttemptStatus.COMPLETED,
            current_position=6,
            correct_count=4,
            question_count=5,
            score_percentage=80,
            started_at=now,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )


def test_attempt_answer_preserves_topic_and_correctness() -> None:
    """Stored answer history must support scoring and analytics."""

    now = datetime.now(
        UTC,
    )

    answer = QuizAttemptAnswerResponse(
        id=uuid4(),
        attempt_id=uuid4(),
        quiz_question_id=uuid4(),
        position=1,
        topic="Rizal",
        question_type=(
            QuizQuestionType.IDENTIFICATION
        ),
        submitted_answer="Jose Rizal",
        is_correct=True,
        answered_at=now,
        created_at=now,
    )

    assert answer.topic == "Rizal"
    assert answer.is_correct is True


def test_in_progress_feedback_requires_next_position() -> None:
    """Immediate feedback must identify the next question."""

    feedback = QuizAnswerFeedbackResponse(
        attempt_id=uuid4(),
        quiz_question_id=uuid4(),
        position=1,
        is_correct=True,
        correct_answer="Jose Rizal",
        explanation="The source identifies Jose Rizal.",
        next_position=2,
        attempt_completed=False,
    )

    assert feedback.next_position == 2


def test_completed_feedback_has_no_next_position() -> None:
    """Final-question feedback must mark the attempt complete."""

    feedback = QuizAnswerFeedbackResponse(
        attempt_id=uuid4(),
        quiz_question_id=uuid4(),
        position=5,
        is_correct=False,
        correct_answer="Jose Rizal",
        explanation="The source identifies Jose Rizal.",
        next_position=None,
        attempt_completed=True,
    )

    assert feedback.attempt_completed is True
    assert feedback.next_position is None


def test_topic_result_requires_consistent_accuracy() -> None:
    """Topic accuracy must match its correct-answer count."""

    result = QuizTopicResult(
        topic="Photosynthesis",
        correct_count=2,
        question_count=3,
        accuracy_percentage=66.67,
    )

    assert result.correct_count == 2

    with pytest.raises(
        ValidationError,
    ):
        QuizTopicResult(
            topic="Photosynthesis",
            correct_count=2,
            question_count=3,
            accuracy_percentage=50,
        )


def test_final_result_supports_strong_and_weak_topics() -> None:
    """Completed Quizzes must expose score and topic groups."""

    now = datetime.now(
        UTC,
    )

    result = QuizAttemptResultResponse(
        attempt_id=uuid4(),
        quiz_id=uuid4(),
        correct_count=4,
        question_count=5,
        score_percentage=80,
        strong_topics=(
            QuizTopicResult(
                topic="Rizal",
                correct_count=3,
                question_count=3,
                accuracy_percentage=100,
            ),
        ),
        weak_topics=(
            QuizTopicResult(
                topic="Reform Movement",
                correct_count=1,
                question_count=2,
                accuracy_percentage=50,
            ),
        ),
        completed_at=now,
    )

    assert result.score_percentage == 80
    assert len(
        result.strong_topics,
    ) == 1
    assert len(
        result.weak_topics,
    ) == 1


def test_topic_cannot_be_both_strong_and_weak() -> None:
    """One topic cannot appear in both result groups."""

    now = datetime.now(
        UTC,
    )

    topic = QuizTopicResult(
        topic="Rizal",
        correct_count=1,
        question_count=1,
        accuracy_percentage=100,
    )

    with pytest.raises(
        ValidationError,
    ):
        QuizAttemptResultResponse(
            attempt_id=uuid4(),
            quiz_id=uuid4(),
            correct_count=1,
            question_count=1,
            score_percentage=100,
            strong_topics=(
                topic,
            ),
            weak_topics=(
                topic,
            ),
            completed_at=now,
        )