# File: /backend/tests/test_quiz_schemas.py

# Purpose: Verifies quiz generation and student-safe response
# schema validation.

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

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


def _multiple_choice_question(
    *,
    position: int = 1,
) -> QuizGeneratedQuestion:
    """Return one valid generated multiple-choice question."""

    return QuizGeneratedQuestion(
        position=position,
        question_type=QuizQuestionType.MULTIPLE_CHOICE,
        topic="Nationalism",
        question="Who wrote Noli Me Tangere?",
        choices=(
            "Jose Rizal",
            "Andres Bonifacio",
            "Emilio Aguinaldo",
            "Apolinario Mabini",
        ),
        correct_answer="Jose Rizal",
        explanation=(
            "Jose Rizal wrote Noli Me Tangere as part of his "
            "critique of Spanish colonial society."
        ),
    )


def _public_question(
    *,
    position: int = 1,
) -> QuizQuestionResponse:
    """Return one student-safe saved question."""

    return QuizQuestionResponse(
        id=uuid4(),
        position=position,
        question_type=QuizQuestionType.MULTIPLE_CHOICE,
        topic="Nationalism",
        question="Who wrote Noli Me Tangere?",
        choices=(
            "Jose Rizal",
            "Andres Bonifacio",
            "Emilio Aguinaldo",
            "Apolinario Mabini",
        ),
    )


def test_subject_quiz_request_is_valid() -> None:
    """Subject quiz generation must not require one file."""

    request = QuizGenerateRequest(
        scope_type=QuizScopeType.SUBJECT,
        subject_id=uuid4(),
        quiz_type=QuizType.MIXED,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=10,
    )

    assert request.study_file_id is None
    assert request.quiz_type == QuizType.MIXED
    assert request.question_count == 10


def test_file_quiz_request_requires_file() -> None:
    """File quiz generation must include study_file_id."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGenerateRequest(
            scope_type=QuizScopeType.FILE,
            subject_id=uuid4(),
        )


def test_subject_quiz_request_rejects_file() -> None:
    """Subject scope must not silently become file scope."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGenerateRequest(
            scope_type=QuizScopeType.SUBJECT,
            subject_id=uuid4(),
            study_file_id=uuid4(),
        )


@pytest.mark.parametrize(
    "question_count",
    (
        0,
        51,
    ),
)
def test_question_count_must_be_supported(
    question_count: int,
) -> None:
    """Quiz question count must remain within safe limits."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGenerateRequest(
            scope_type=QuizScopeType.SUBJECT,
            subject_id=uuid4(),
            question_count=question_count,
        )


def test_multiple_choice_question_is_valid() -> None:
    """Multiple-choice questions must preserve their answer key."""

    question = _multiple_choice_question()

    assert len(question.choices) == 4
    assert question.correct_answer == "Jose Rizal"
    assert question.explanation


def test_multiple_choice_requires_choices() -> None:
    """Multiple-choice questions cannot omit answer choices."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGeneratedQuestion(
            position=1,
            question_type=QuizQuestionType.MULTIPLE_CHOICE,
            topic="Topic",
            question="Question?",
            correct_answer="Answer",
            explanation="Explanation.",
        )


def test_multiple_choice_answer_must_match_choice() -> None:
    """Multiple-choice answer key must identify a real choice."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGeneratedQuestion(
            position=1,
            question_type=QuizQuestionType.MULTIPLE_CHOICE,
            topic="Topic",
            question="Question?",
            choices=(
                "Choice A",
                "Choice B",
            ),
            correct_answer="Choice C",
            explanation="Explanation.",
        )


def test_true_false_question_is_valid() -> None:
    """True-or-false questions require the standard choices."""

    question = QuizGeneratedQuestion(
        position=1,
        question_type=QuizQuestionType.TRUE_FALSE,
        topic="Rizal",
        question="Rizal wrote Noli Me Tangere.",
        choices=(
            "True",
            "False",
        ),
        correct_answer="True",
        explanation="Rizal is the author of the novel.",
    )

    assert question.correct_answer == "True"
    assert len(question.choices) == 2


def test_true_false_rejects_invalid_choices() -> None:
    """True-or-false questions cannot contain arbitrary choices."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGeneratedQuestion(
            position=1,
            question_type=QuizQuestionType.TRUE_FALSE,
            topic="Topic",
            question="Statement.",
            choices=(
                "Yes",
                "No",
            ),
            correct_answer="Yes",
            explanation="Explanation.",
        )


def test_identification_supports_alternative_answers() -> None:
    """Identification can preserve accepted answer variants."""

    question = QuizGeneratedQuestion(
        position=1,
        question_type=QuizQuestionType.IDENTIFICATION,
        topic="Rizal",
        question="Who wrote Noli Me Tangere?",
        correct_answer="Jose Rizal",
        accepted_answers=(
            "José Rizal",
            "Dr. Jose Rizal",
        ),
        explanation="Jose Rizal wrote the novel.",
    )

    assert question.choices == ()
    assert len(question.accepted_answers) == 2


def test_identification_rejects_choices() -> None:
    """Identification questions must remain free response."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGeneratedQuestion(
            position=1,
            question_type=QuizQuestionType.IDENTIFICATION,
            topic="Topic",
            question="Identify the person.",
            choices=(
                "Person A",
                "Person B",
            ),
            correct_answer="Person A",
            explanation="Explanation.",
        )


def test_generated_content_requires_sequential_positions() -> None:
    """Generated quiz questions must preserve display order."""

    with pytest.raises(
        ValidationError,
    ):
        QuizGeneratedContent(
            title="History Quiz",
            questions=(
                _multiple_choice_question(
                    position=1,
                ),
                _multiple_choice_question(
                    position=3,
                ),
            ),
        )


def test_public_question_does_not_expose_answer_key() -> None:
    """Quiz delivery must not reveal answers before submission."""

    question = _public_question()

    payload = question.model_dump()

    assert "correct_answer" not in payload
    assert "accepted_answers" not in payload
    assert "explanation" not in payload


def test_saved_quiz_response_is_valid() -> None:
    """Saved quiz response must expose safe quiz metadata."""

    now = datetime.now(
        UTC,
    )

    response = QuizResponse(
        id=uuid4(),
        subject_id=uuid4(),
        scope_type=QuizScopeType.SUBJECT,
        title="Rizal Quiz",
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=1,
        questions=(
            _public_question(),
        ),
        generation_model="gemini-test-model",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )

    assert response.question_count == 1
    assert len(response.questions) == 1
    assert response.study_file_id is None


def test_saved_quiz_question_count_must_match() -> None:
    """Saved quiz metadata cannot disagree with question rows."""

    now = datetime.now(
        UTC,
    )

    with pytest.raises(
        ValidationError,
    ):
        QuizResponse(
            id=uuid4(),
            subject_id=uuid4(),
            scope_type=QuizScopeType.SUBJECT,
            title="Rizal Quiz",
            quiz_type=QuizType.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.MEDIUM,
            question_count=2,
            questions=(
                _public_question(),
            ),
            generation_model="gemini-test-model",
            generation_count=1,
            generated_at=now,
            created_at=now,
            updated_at=now,
        )