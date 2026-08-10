# File: /backend/app/schemas/quiz.py
# Purpose: Defines validated Quiz generation, attempt, history,
# review, and student-safe response contracts.

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class QuizScopeType(str, Enum):
    """Supported study-material scopes for Quiz generation."""

    SUBJECT = "subject"
    FILE = "file"


class QuizType(str, Enum):
    """Quiz composition requested by the student."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    IDENTIFICATION = "identification"
    MIXED = "mixed"


class QuizQuestionType(str, Enum):
    """Concrete question types stored inside a Quiz."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    IDENTIFICATION = "identification"


class QuizDifficulty(str, Enum):
    """Supported Quiz difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuizAttemptStatus(str, Enum):
    """Lifecycle states for a Quiz attempt."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuizBaseModel(BaseModel):
    """Shared strict configuration for Quiz contracts."""

    model_config = ConfigDict(
        extra="forbid",
    )


class QuizGenerateRequest(QuizBaseModel):
    """Validated request for generating one Quiz."""

    scope_type: QuizScopeType
    subject_id: UUID
    study_file_id: UUID | None = None
    quiz_type: QuizType = QuizType.MIXED
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    question_count: int = Field(
        default=10,
        ge=1,
        le=50,
    )

    @model_validator(
        mode="after",
    )
    def validate_scope(
        self,
    ) -> Self:
        """Ensure subject and file scopes cannot be mixed."""

        if (
            self.scope_type == QuizScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "File quiz generation requires study_file_id.",
            )

        if (
            self.scope_type == QuizScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "Subject quiz generation cannot target one study file.",
            )

        return self


class QuizQuestionCore(QuizBaseModel):
    """Student-visible fields shared by generated Quiz questions."""

    position: int = Field(
        ge=1,
    )
    question_type: QuizQuestionType
    topic: str
    question: str
    choices: tuple[str, ...] = ()

    @field_validator(
        "topic",
        "question",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """Reject blank topic and question text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz question text fields must not be empty.",
            )

        return normalized

    @field_validator(
        "choices",
    )
    @classmethod
    def validate_choices(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Normalize choices and reject blanks or duplicates."""

        normalized_choices = tuple(
            choice.strip()
            for choice in value
        )

        if any(
            not choice
            for choice in normalized_choices
        ):
            raise ValueError(
                "Quiz choices must not contain empty values.",
            )

        normalized_keys = [
            choice.casefold()
            for choice in normalized_choices
        ]

        if len(
            normalized_keys,
        ) != len(
            set(
                normalized_keys,
            ),
        ):
            raise ValueError(
                "Quiz choices must be unique.",
            )

        return normalized_choices


class QuizGeneratedQuestion(QuizQuestionCore):
    """AI-generated question including its private answer key."""

    correct_answer: str
    accepted_answers: tuple[str, ...] = ()
    explanation: str

    @field_validator(
        "correct_answer",
        "explanation",
    )
    @classmethod
    def validate_answer_text(
        cls,
        value: str,
    ) -> str:
        """Reject blank answers and explanations."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz answers and explanations must not be empty.",
            )

        return normalized

    @field_validator(
        "accepted_answers",
    )
    @classmethod
    def validate_accepted_answers(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Normalize optional identification answer alternatives."""

        normalized_answers = tuple(
            answer.strip()
            for answer in value
        )

        if any(
            not answer
            for answer in normalized_answers
        ):
            raise ValueError(
                "Accepted answers must not contain empty values.",
            )

        normalized_keys = [
            answer.casefold()
            for answer in normalized_answers
        ]

        if len(
            normalized_keys,
        ) != len(
            set(
                normalized_keys,
            ),
        ):
            raise ValueError(
                "Accepted answers must be unique.",
            )

        return normalized_answers

    @model_validator(
        mode="after",
    )
    def validate_question_type(
        self,
    ) -> Self:
        """Ensure answer structure matches the question type."""

        if self.question_type == QuizQuestionType.MULTIPLE_CHOICE:
            self._validate_multiple_choice()

        elif self.question_type == QuizQuestionType.TRUE_FALSE:
            self._validate_true_false()

        else:
            self._validate_identification()

        return self

    def _validate_multiple_choice(
        self,
    ) -> None:
        """Validate one multiple-choice question."""

        if len(
            self.choices,
        ) < 2:
            raise ValueError(
                "Multiple-choice questions require at least two choices.",
            )

        valid_answers = {
            choice.casefold()
            for choice in self.choices
        }

        if self.correct_answer.casefold() not in valid_answers:
            raise ValueError(
                "The multiple-choice correct answer must match a choice.",
            )

        if self.accepted_answers:
            raise ValueError(
                "Multiple-choice questions cannot define accepted answers.",
            )

    def _validate_true_false(
        self,
    ) -> None:
        """Validate one true-or-false question."""

        normalized_choices = {
            choice.casefold()
            for choice in self.choices
        }

        if normalized_choices != {
            "true",
            "false",
        }:
            raise ValueError(
                "True-or-false questions require True and False choices.",
            )

        if self.correct_answer.casefold() not in {
            "true",
            "false",
        }:
            raise ValueError(
                "True-or-false correct answer must be True or False.",
            )

        if self.accepted_answers:
            raise ValueError(
                "True-or-false questions cannot define accepted answers.",
            )

    def _validate_identification(
        self,
    ) -> None:
        """Validate one identification question."""

        if self.choices:
            raise ValueError(
                "Identification questions cannot define choices.",
            )


class QuizGeneratedContent(QuizBaseModel):
    """Complete private AI-generated Quiz content."""

    title: str
    questions: tuple[
        QuizGeneratedQuestion,
        ...,
    ] = Field(
        min_length=1,
        max_length=50,
    )

    @field_validator(
        "title",
    )
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        """Reject an empty generated Quiz title."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz title must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_question_positions(
        self,
    ) -> Self:
        """Require questions to use sequential positions."""

        positions = [
            question.position
            for question in self.questions
        ]

        expected_positions = list(
            range(
                1,
                len(
                    self.questions,
                )
                + 1,
            ),
        )

        if positions != expected_positions:
            raise ValueError(
                "Quiz question positions must be sequential starting at 1.",
            )

        return self


class QuizQuestionResponse(QuizQuestionCore):
    """Student-safe saved question without its answer key."""

    id: UUID


class QuizResponse(QuizBaseModel):
    """Student-safe saved Quiz returned through the API."""

    id: UUID
    subject_id: UUID
    study_file_id: UUID | None = None
    scope_type: QuizScopeType
    title: str
    quiz_type: QuizType
    difficulty: QuizDifficulty
    question_count: int = Field(
        ge=1,
        le=50,
    )
    questions: tuple[
        QuizQuestionResponse,
        ...,
    ]
    generation_model: str
    generation_count: int = Field(
        ge=1,
    )
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "title",
        "generation_model",
    )
    @classmethod
    def validate_response_text(
        cls,
        value: str,
    ) -> str:
        """Reject blank saved Quiz metadata."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz response text fields must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_saved_quiz(
        self,
    ) -> Self:
        """Ensure saved Quiz metadata and questions are consistent."""

        if (
            self.scope_type == QuizScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "A saved file quiz requires study_file_id.",
            )

        if (
            self.scope_type == QuizScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "A saved subject quiz cannot target one study file.",
            )

        if len(
            self.questions,
        ) != self.question_count:
            raise ValueError(
                "Quiz question_count must match the saved questions.",
            )

        positions = [
            question.position
            for question in self.questions
        ]

        expected_positions = list(
            range(
                1,
                self.question_count + 1,
            ),
        )

        if positions != expected_positions:
            raise ValueError(
                "Saved quiz question positions must be sequential.",
            )

        return self


class QuizApiErrorResponse(QuizBaseModel):
    """Safe public error body for Quiz endpoints."""

    error_code: str
    message: str

    @field_validator(
        "error_code",
        "message",
    )
    @classmethod
    def validate_error_text(
        cls,
        value: str,
    ) -> str:
        """Reject blank public Quiz error fields."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz API error fields must not be empty.",
            )

        return normalized


class QuizAnswerSubmissionRequest(QuizBaseModel):
    """One answer submitted for the current Quiz question."""

    answer: str = Field(
        min_length=1,
        max_length=4000,
    )

    @field_validator(
        "answer",
    )
    @classmethod
    def validate_answer(
        cls,
        value: str,
    ) -> str:
        """Trim and reject blank submitted answers."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz answer must not be empty.",
            )

        return normalized


class QuizAttemptResponse(QuizBaseModel):
    """Student-safe persisted Quiz attempt state."""

    id: UUID
    quiz_id: UUID
    status: QuizAttemptStatus
    current_position: int = Field(
        ge=1,
    )
    correct_count: int = Field(
        ge=0,
    )
    question_count: int = Field(
        ge=1,
        le=50,
    )
    score_percentage: float = Field(
        ge=0,
        le=100,
    )
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(
        mode="after",
    )
    def validate_attempt_state(
        self,
    ) -> Self:
        """Ensure persisted Quiz-attempt progress is consistent."""

        if self.correct_count > self.question_count:
            raise ValueError(
                "Quiz attempt correct_count cannot exceed question_count.",
            )

        if self.current_position > self.question_count + 1:
            raise ValueError(
                "Quiz attempt current_position is out of range.",
            )

        if self.status is QuizAttemptStatus.IN_PROGRESS:
            if self.completed_at is not None:
                raise ValueError(
                    "In-progress Quiz attempt cannot have completed_at.",
                )

            if self.current_position > self.question_count:
                raise ValueError(
                    "In-progress Quiz attempt cannot be past the final question.",
                )

        else:
            if self.completed_at is None:
                raise ValueError(
                    "Completed Quiz attempt requires completed_at.",
                )

            if self.current_position != self.question_count + 1:
                raise ValueError(
                    "Completed Quiz attempt must be past the final question.",
                )

        return self


class QuizAttemptAnswerResponse(QuizBaseModel):
    """Student-safe stored submitted answer history."""

    id: UUID
    attempt_id: UUID
    quiz_question_id: UUID
    position: int = Field(
        ge=1,
    )
    topic: str
    question_type: QuizQuestionType
    submitted_answer: str
    is_correct: bool
    answered_at: datetime
    created_at: datetime

    @field_validator(
        "topic",
        "submitted_answer",
    )
    @classmethod
    def validate_attempt_answer_text(
        cls,
        value: str,
    ) -> str:
        """Reject blank stored answer text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz attempt answer text must not be empty.",
            )

        return normalized


class QuizAnswerFeedbackResponse(QuizBaseModel):
    """Immediate grading feedback for one submitted answer."""

    attempt_id: UUID
    quiz_question_id: UUID
    position: int = Field(
        ge=1,
    )
    is_correct: bool
    correct_answer: str
    explanation: str
    next_position: int | None = Field(
        default=None,
        ge=1,
    )
    attempt_completed: bool

    @field_validator(
        "correct_answer",
        "explanation",
    )
    @classmethod
    def validate_feedback_text(
        cls,
        value: str,
    ) -> str:
        """Reject empty answer feedback."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz feedback text must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_feedback_progress(
        self,
    ) -> Self:
        """Ensure next-question state matches completion."""

        if self.attempt_completed:
            if self.next_position is not None:
                raise ValueError(
                    "Completed Quiz feedback cannot "
                    "contain next_position.",
                )

        elif self.next_position is None:
            raise ValueError(
                "In-progress Quiz feedback requires "
                "next_position.",
            )

        return self


class QuizTopicResult(QuizBaseModel):
    """Accuracy summary for one topic in a completed Quiz."""

    topic: str
    correct_count: int = Field(
        ge=0,
    )
    question_count: int = Field(
        ge=1,
    )
    accuracy_percentage: float = Field(
        ge=0,
        le=100,
    )

    @field_validator(
        "topic",
    )
    @classmethod
    def validate_topic(
        cls,
        value: str,
    ) -> str:
        """Reject an empty result topic."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz result topic must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_topic_score(
        self,
    ) -> Self:
        """Ensure topic counts and accuracy are consistent."""

        if self.correct_count > self.question_count:
            raise ValueError(
                "Quiz topic correct_count cannot "
                "exceed question_count.",
            )

        expected_accuracy = round(
            (
                self.correct_count
                / self.question_count
            )
            * 100,
            2,
        )

        if (
            abs(
                self.accuracy_percentage
                - expected_accuracy
            )
            > 0.01
        ):
            raise ValueError(
                "Quiz topic accuracy does not match "
                "its correct and question counts.",
            )

        return self


class QuizAttemptResultResponse(QuizBaseModel):
    """Final score and topic strengths for a completed Quiz."""

    attempt_id: UUID
    quiz_id: UUID
    correct_count: int = Field(
        ge=0,
    )
    question_count: int = Field(
        ge=1,
        le=50,
    )
    score_percentage: float = Field(
        ge=0,
        le=100,
    )
    strong_topics: tuple[
        QuizTopicResult,
        ...,
    ] = ()
    weak_topics: tuple[
        QuizTopicResult,
        ...,
    ] = ()
    completed_at: datetime

    @model_validator(
        mode="after",
    )
    def validate_result(
        self,
    ) -> Self:
        """Ensure final score and topic groups are consistent."""

        if self.correct_count > self.question_count:
            raise ValueError(
                "Quiz result correct_count cannot "
                "exceed question_count.",
            )

        expected_score = round(
            (
                self.correct_count
                / self.question_count
            )
            * 100,
            2,
        )

        if (
            abs(
                self.score_percentage
                - expected_score
            )
            > 0.01
        ):
            raise ValueError(
                "Quiz result score does not match "
                "its correct and question counts.",
            )

        strong_keys = {
            topic.topic.casefold()
            for topic in self.strong_topics
        }

        weak_keys = {
            topic.topic.casefold()
            for topic in self.weak_topics
        }

        if len(
            strong_keys,
        ) != len(
            self.strong_topics,
        ):
            raise ValueError(
                "Strong Quiz topics must be unique.",
            )

        if len(
            weak_keys,
        ) != len(
            self.weak_topics,
        ):
            raise ValueError(
                "Weak Quiz topics must be unique.",
            )

        if strong_keys & weak_keys:
            raise ValueError(
                "A Quiz topic cannot be both "
                "strong and weak.",
            )

        return self


class QuizAnswerSubmissionResponse(QuizBaseModel):
    """Updated attempt state plus immediate answer feedback."""

    attempt: QuizAttemptResponse
    feedback: QuizAnswerFeedbackResponse


class QuizAttemptListResponse(QuizBaseModel):
    """Saved attempts belonging to one Quiz."""

    quiz_id: UUID
    items: tuple[
        QuizAttemptResponse,
        ...,
    ] = ()

    @model_validator(
        mode="after",
    )
    def validate_attempts(
        self,
    ) -> Self:
        """Ensure every listed attempt belongs to the requested Quiz."""

        for attempt in self.items:
            if attempt.quiz_id != self.quiz_id:
                raise ValueError(
                    "Listed Quiz attempt does not "
                    "belong to quiz_id.",
                )

        return self


class QuizSummaryResponse(QuizBaseModel):
    """Student-safe summary for one saved Quiz."""

    id: UUID
    subject_id: UUID
    study_file_id: UUID | None = None
    scope_type: QuizScopeType
    title: str
    quiz_type: QuizType
    difficulty: QuizDifficulty
    question_count: int = Field(
        ge=1,
        le=50,
    )
    attempt_count: int = Field(
        ge=0,
    )
    latest_attempt: QuizAttemptResponse | None = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "title",
    )
    @classmethod
    def validate_summary_title(
        cls,
        value: str,
    ) -> str:
        """Reject an empty saved-Quiz title."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz title must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_summary(
        self,
    ) -> Self:
        """Ensure scope and attempt summary are consistent."""

        if (
            self.scope_type is QuizScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "File-scope Quiz requires study_file_id.",
            )

        if (
            self.scope_type is QuizScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "Subject-scope Quiz cannot contain "
                "study_file_id.",
            )

        if self.attempt_count == 0:
            if self.latest_attempt is not None:
                raise ValueError(
                    "A Quiz without attempts cannot contain "
                    "latest_attempt.",
                )

            return self

        if self.latest_attempt is None:
            raise ValueError(
                "A Quiz with attempts requires latest_attempt.",
            )

        if self.latest_attempt.quiz_id != self.id:
            raise ValueError(
                "Latest attempt does not belong to the Quiz.",
            )

        if (
            self.latest_attempt.question_count
            != self.question_count
        ):
            raise ValueError(
                "Latest attempt question count does not "
                "match the Quiz.",
            )

        return self


class QuizListResponse(QuizBaseModel):
    """Saved Quizzes owned by the authenticated student."""

    items: tuple[
        QuizSummaryResponse,
        ...,
    ] = ()


class QuizAttemptReviewAnswerResponse(QuizBaseModel):
    """One completed answer with private post-attempt review data."""

    answer_id: UUID
    question: QuizQuestionResponse
    submitted_answer: str
    is_correct: bool
    correct_answer: str
    explanation: str
    answered_at: datetime

    @field_validator(
        "submitted_answer",
        "correct_answer",
        "explanation",
    )
    @classmethod
    def validate_review_text(
        cls,
        value: str,
    ) -> str:
        """Reject empty completed-attempt review text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Quiz review text must not be empty.",
            )

        return normalized


class QuizAttemptReviewResponse(QuizBaseModel):
    """Completed attempt including answers and final result."""

    attempt: QuizAttemptResponse
    answers: tuple[
        QuizAttemptReviewAnswerResponse,
        ...,
    ]
    result: QuizAttemptResultResponse

    @model_validator(
        mode="after",
    )
    def validate_review(
        self,
    ) -> Self:
        """Ensure review data represents one complete attempt."""

        if self.attempt.status is not QuizAttemptStatus.COMPLETED:
            raise ValueError(
                "Only completed Quiz attempts can be reviewed.",
            )

        if (
            self.result.attempt_id != self.attempt.id
            or self.result.quiz_id != self.attempt.quiz_id
        ):
            raise ValueError(
                "Quiz review result does not match attempt.",
            )

        if len(
            self.answers,
        ) != self.attempt.question_count:
            raise ValueError(
                "Quiz review answer history is incomplete.",
            )

        expected_positions = list(
            range(
                1,
                self.attempt.question_count + 1,
            )
        )

        actual_positions = [
            answer.question.position
            for answer in self.answers
        ]

        if actual_positions != expected_positions:
            raise ValueError(
                "Quiz review questions must be sequential.",
            )

        question_ids = {
            answer.question.id
            for answer in self.answers
        }

        if len(
            question_ids,
        ) != len(
            self.answers,
        ):
            raise ValueError(
                "Quiz review questions must be unique.",
            )

        return self