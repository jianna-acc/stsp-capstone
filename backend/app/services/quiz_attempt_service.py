# File: /backend/app/services/quiz_attempt_service.py
# Purpose: Coordinates Quiz attempts, atomic answer submission,
# final scoring, attempt history, and completed-attempt review.

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.repositories.quiz_attempt_repository import (
    QuizAnswerSubmissionResult,
    QuizReviewQuestionRecord,
)
from app.schemas.quiz import (
    QuizAnswerSubmissionRequest,
    QuizAttemptAnswerResponse,
    QuizAttemptListResponse,
    QuizAttemptResponse,
    QuizAttemptResultResponse,
    QuizAttemptReviewAnswerResponse,
    QuizAttemptReviewResponse,
    QuizAttemptStatus,
    QuizTopicResult,
)
from app.services.quiz_attempt_errors import (
    QuizAttemptConflictError,
    QuizAttemptNotFoundError,
    QuizAttemptResponseError,
    QuizAttemptValidationError,
)

STRONG_TOPIC_THRESHOLD_PERCENTAGE = 70.0


class _QuizAttemptRepository(
    Protocol,
):
    """Persistence operations required by QuizAttemptService."""

    def start_attempt(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizAttemptResponse: ...

    def submit_answer(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
        position: int,
        submitted_answer: str,
    ) -> QuizAnswerSubmissionResult: ...

    def get_attempt(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResponse | None: ...

    def list_attempts(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> Sequence[
        QuizAttemptResponse
    ]: ...

    def list_answers(
        self,
        *,
        attempt_id: UUID,
    ) -> Sequence[
        QuizAttemptAnswerResponse
    ]: ...

    def list_review_questions(
        self,
        *,
        quiz_id: UUID,
    ) -> Sequence[
        QuizReviewQuestionRecord
    ]: ...


class QuizAttemptService:
    """Coordinates one student's Quiz-taking lifecycle."""

    def __init__(
        self,
        repository: _QuizAttemptRepository,
    ) -> None:
        self._repository = repository

    def start_attempt(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizAttemptResponse:
        """Start one fresh attempt for an owned Quiz."""

        return self._repository.start_attempt(
            user_id=user_id,
            quiz_id=quiz_id,
        )

    def submit_answer(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
        position: int,
        request: QuizAnswerSubmissionRequest,
    ) -> QuizAnswerSubmissionResult:
        """Submit and immediately grade one expected question."""

        if (
            isinstance(
                position,
                bool,
            )
            or not isinstance(
                position,
                int,
            )
            or position < 1
        ):
            raise QuizAttemptValidationError(
                "Quiz answer position must be positive.",
            )

        if not isinstance(
            request,
            QuizAnswerSubmissionRequest,
        ):
            raise QuizAttemptValidationError(
                "request must be a QuizAnswerSubmissionRequest.",
            )

        return self._repository.submit_answer(
            user_id=user_id,
            attempt_id=attempt_id,
            position=position,
            submitted_answer=request.answer,
        )

    def get_attempt(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResponse:
        """Return one owned Quiz attempt."""

        attempt = self._repository.get_attempt(
            user_id=user_id,
            attempt_id=attempt_id,
        )

        if attempt is None:
            raise QuizAttemptNotFoundError(
                "The requested Quiz attempt was not found.",
            )

        return attempt

    def list_attempts(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizAttemptListResponse:
        """Return saved attempts for one owned Quiz."""

        attempts = tuple(
            self._repository.list_attempts(
                user_id=user_id,
                quiz_id=quiz_id,
            )
        )

        return QuizAttemptListResponse(
            quiz_id=quiz_id,
            items=attempts,
        )

    def get_result(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResultResponse:
        """Build final score and strong/weak topics."""

        attempt = self._get_completed_attempt(
            user_id=user_id,
            attempt_id=attempt_id,
        )

        answers = self._get_completed_answers(
            attempt=attempt,
        )

        return self._build_result(
            attempt=attempt,
            answers=answers,
        )

    def get_review(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptReviewResponse:
        """Return a completed attempt with answers and explanations."""

        attempt = self._get_completed_attempt(
            user_id=user_id,
            attempt_id=attempt_id,
        )

        answers = self._get_completed_answers(
            attempt=attempt,
        )

        review_questions = tuple(
            self._repository.list_review_questions(
                quiz_id=attempt.quiz_id,
            )
        )

        if (
            len(
                review_questions,
            )
            != attempt.question_count
        ):
            raise QuizAttemptResponseError(
                "Stored Quiz review questions are incomplete.",
            )

        questions_by_id = {
            record.question.id: record
            for record in review_questions
        }

        review_answers: list[
            QuizAttemptReviewAnswerResponse
        ] = []

        for answer in answers:
            record = questions_by_id.get(
                answer.quiz_question_id,
            )

            if record is None:
                raise QuizAttemptResponseError(
                    "Quiz review question could not be matched "
                    "to its submitted answer.",
                )

            review_answers.append(
                QuizAttemptReviewAnswerResponse(
                    answer_id=answer.id,
                    question=record.question,
                    submitted_answer=(
                        answer.submitted_answer
                    ),
                    is_correct=answer.is_correct,
                    correct_answer=(
                        record.correct_answer
                    ),
                    explanation=(
                        record.explanation
                    ),
                    answered_at=answer.answered_at,
                )
            )

        result = self._build_result(
            attempt=attempt,
            answers=answers,
        )

        return QuizAttemptReviewResponse(
            attempt=attempt,
            answers=tuple(
                review_answers,
            ),
            result=result,
        )

    def _get_completed_attempt(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResponse:
        """Require one completed owned attempt."""

        attempt = self.get_attempt(
            user_id=user_id,
            attempt_id=attempt_id,
        )

        if (
            attempt.status
            != QuizAttemptStatus.COMPLETED
        ):
            raise QuizAttemptConflictError(
                "Quiz results and review are unavailable "
                "until the attempt is completed.",
            )

        if attempt.completed_at is None:
            raise QuizAttemptResponseError(
                "Completed Quiz attempt is missing completed_at.",
            )

        return attempt

    def _get_completed_answers(
        self,
        *,
        attempt: QuizAttemptResponse,
    ) -> tuple[
        QuizAttemptAnswerResponse,
        ...,
    ]:
        """Require a complete answer history."""

        answers = tuple(
            self._repository.list_answers(
                attempt_id=attempt.id,
            )
        )

        if (
            len(
                answers,
            )
            != attempt.question_count
        ):
            raise QuizAttemptResponseError(
                "Completed Quiz answer history is incomplete.",
            )

        return answers

    def _build_result(
        self,
        *,
        attempt: QuizAttemptResponse,
        answers: Sequence[
            QuizAttemptAnswerResponse
        ],
    ) -> QuizAttemptResultResponse:
        """Build one validated final result."""

        if attempt.completed_at is None:
            raise QuizAttemptResponseError(
                "Completed Quiz attempt is missing completed_at.",
            )

        topic_results = self._build_topic_results(
            answers,
        )

        strong_topics = tuple(
            result
            for result in topic_results
            if (
                result.accuracy_percentage
                >= STRONG_TOPIC_THRESHOLD_PERCENTAGE
            )
        )

        weak_topics = tuple(
            result
            for result in topic_results
            if (
                result.accuracy_percentage
                < STRONG_TOPIC_THRESHOLD_PERCENTAGE
            )
        )

        return QuizAttemptResultResponse(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            correct_count=attempt.correct_count,
            question_count=attempt.question_count,
            score_percentage=(
                attempt.score_percentage
            ),
            strong_topics=strong_topics,
            weak_topics=weak_topics,
            completed_at=attempt.completed_at,
        )

    def _build_topic_results(
        self,
        answers: Sequence[
            QuizAttemptAnswerResponse
        ],
    ) -> tuple[
        QuizTopicResult,
        ...,
    ]:
        """Aggregate correctness by normalized topic."""

        topic_order: list[
            str
        ] = []

        display_names: dict[
            str,
            str,
        ] = {}

        correct_counts: dict[
            str,
            int,
        ] = {}

        question_counts: dict[
            str,
            int,
        ] = {}

        for answer in answers:
            normalized_topic = " ".join(
                answer.topic.casefold().split()
            )

            if normalized_topic not in display_names:
                topic_order.append(
                    normalized_topic,
                )

                display_names[
                    normalized_topic
                ] = answer.topic

                correct_counts[
                    normalized_topic
                ] = 0

                question_counts[
                    normalized_topic
                ] = 0

            question_counts[
                normalized_topic
            ] += 1

            if answer.is_correct:
                correct_counts[
                    normalized_topic
                ] += 1

        results: list[
            QuizTopicResult
        ] = []

        for normalized_topic in topic_order:
            correct_count = correct_counts[
                normalized_topic
            ]

            question_count = question_counts[
                normalized_topic
            ]

            accuracy = round(
                (
                    correct_count
                    / question_count
                )
                * 100,
                2,
            )

            results.append(
                QuizTopicResult(
                    topic=display_names[
                        normalized_topic
                    ],
                    correct_count=correct_count,
                    question_count=question_count,
                    accuracy_percentage=accuracy,
                )
            )

        return tuple(
            results,
        )