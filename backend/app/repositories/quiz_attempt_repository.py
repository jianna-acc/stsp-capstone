# File: /backend/app/repositories/quiz_attempt_repository.py
# Purpose: Starts, grades, reads, lists, and reviews owned Quiz
# attempts through trusted Supabase table and RPC operations.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from typing import Protocol, Self
from uuid import UUID

from postgrest.exceptions import APIError
from pydantic import ValidationError

from app.schemas.quiz import (
    QuizAnswerFeedbackResponse,
    QuizAttemptAnswerResponse,
    QuizAttemptResponse,
    QuizQuestionResponse,
)
from app.services.quiz_attempt_errors import (
    QuizAttemptConflictError,
    QuizAttemptNotFoundError,
    QuizAttemptPersistenceError,
    QuizAttemptResponseError,
    QuizAttemptValidationError,
)

_QUIZ_ATTEMPT_COLUMNS = (
    "id,"
    "quiz_id,"
    "status,"
    "current_position,"
    "correct_count,"
    "question_count,"
    "score_percentage,"
    "started_at,"
    "completed_at,"
    "created_at,"
    "updated_at"
)

_QUIZ_ATTEMPT_ANSWER_COLUMNS = (
    "id,"
    "attempt_id,"
    "quiz_question_id,"
    "position,"
    "topic,"
    "question_type,"
    "submitted_answer,"
    "is_correct,"
    "answered_at,"
    "created_at"
)

_QUIZ_REVIEW_QUESTION_COLUMNS = (
    "id,"
    "position,"
    "question_type,"
    "topic,"
    "question,"
    "choices,"
    "correct_answer,"
    "explanation"
)


class _SupabaseResponse(
    Protocol,
):
    data: object


class _SupabaseQuery(
    Protocol,
):
    def select(
        self,
        columns: str,
    ) -> Self: ...

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> Self: ...

    def limit(
        self,
        count: int,
    ) -> Self: ...

    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseRpcQuery(
    Protocol,
):
    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseClient(
    Protocol,
):
    def table(
        self,
        table_name: str,
    ) -> _SupabaseQuery: ...

    def rpc(
        self,
        function_name: str,
        params: Mapping[
            str,
            object,
        ],
    ) -> _SupabaseRpcQuery: ...


@dataclass(
    frozen=True,
    slots=True,
)
class QuizAnswerSubmissionResult:
    """Updated attempt state plus immediate answer feedback."""

    attempt: QuizAttemptResponse
    feedback: QuizAnswerFeedbackResponse


@dataclass(
    frozen=True,
    slots=True,
)
class QuizReviewQuestionRecord:
    """Private question information used after completion."""

    question: QuizQuestionResponse
    correct_answer: str
    explanation: str


class QuizAttemptRepository:
    """Persistence operations for owned Quiz-taking attempts."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def start_attempt(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizAttemptResponse:
        """Start and return one new owned Quiz attempt."""

        response = self._execute_rpc(
            "start_quiz_attempt",
            {
                "p_user_id": str(
                    user_id,
                ),
                "p_quiz_id": str(
                    quiz_id,
                ),
            },
            operation="start the Quiz attempt",
        )

        row = self._extract_single_row(
            response,
            resource="Quiz attempt",
        )

        return self._parse_attempt(
            row,
        )

    def submit_answer(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
        position: int,
        submitted_answer: str,
    ) -> QuizAnswerSubmissionResult:
        """Atomically grade and save one expected Quiz answer."""

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

        normalized_answer = (
            submitted_answer.strip()
        )

        if not normalized_answer:
            raise QuizAttemptValidationError(
                "Submitted Quiz answer must not be empty.",
            )

        if len(
            normalized_answer,
        ) > 4000:
            raise QuizAttemptValidationError(
                "Submitted Quiz answer is too long.",
            )

        response = self._execute_rpc(
            "submit_quiz_attempt_answer",
            {
                "p_user_id": str(
                    user_id,
                ),
                "p_attempt_id": str(
                    attempt_id,
                ),
                "p_position": position,
                "p_submitted_answer": (
                    normalized_answer
                ),
            },
            operation="submit the Quiz answer",
        )

        row = self._extract_single_row(
            response,
            resource="Quiz answer submission",
        )

        attempt_payload = {
            "id": row.get(
                "attempt_id",
            ),
            "quiz_id": row.get(
                "quiz_id",
            ),
            "status": row.get(
                "status",
            ),
            "current_position": row.get(
                "current_position",
            ),
            "correct_count": row.get(
                "correct_count",
            ),
            "question_count": row.get(
                "question_count",
            ),
            "score_percentage": row.get(
                "score_percentage",
            ),
            "started_at": row.get(
                "started_at",
            ),
            "completed_at": row.get(
                "completed_at",
            ),
            "created_at": row.get(
                "created_at",
            ),
            "updated_at": row.get(
                "updated_at",
            ),
        }

        feedback_payload = {
            "attempt_id": row.get(
                "attempt_id",
            ),
            "quiz_question_id": row.get(
                "quiz_question_id",
            ),
            "position": row.get(
                "answered_position",
            ),
            "is_correct": row.get(
                "is_correct",
            ),
            "correct_answer": row.get(
                "correct_answer",
            ),
            "explanation": row.get(
                "explanation",
            ),
            "next_position": row.get(
                "next_position",
            ),
            "attempt_completed": row.get(
                "attempt_completed",
            ),
        }

        try:
            attempt = (
                QuizAttemptResponse.model_validate(
                    attempt_payload,
                )
            )

            feedback = (
                QuizAnswerFeedbackResponse.model_validate(
                    feedback_payload,
                )
            )

        except ValidationError as exc:
            raise QuizAttemptResponseError(
                "The Quiz answer submission response was invalid.",
            ) from exc

        return QuizAnswerSubmissionResult(
            attempt=attempt,
            feedback=feedback,
        )

    def get_attempt(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResponse | None:
        """Return one owned Quiz attempt."""

        response = self._execute_query(
            self._client
            .table(
                "quiz_attempts",
            )
            .select(
                _QUIZ_ATTEMPT_COLUMNS,
            )
            .eq(
                "id",
                str(
                    attempt_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .limit(
                1,
            ),
            operation="load the Quiz attempt",
        )

        rows = self._extract_rows(
            response,
            resource="Quiz attempt",
        )

        if not rows:
            return None

        if len(
            rows,
        ) != 1:
            raise QuizAttemptResponseError(
                "The Quiz attempt lookup response was invalid.",
            )

        return self._parse_attempt(
            rows[
                0
            ],
        )

    def list_attempts(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> tuple[
        QuizAttemptResponse,
        ...,
    ]:
        """Return attempts for one owned Quiz, newest first."""

        ownership_response = self._execute_query(
            self._client
            .table(
                "quizzes",
            )
            .select(
                "id",
            )
            .eq(
                "id",
                str(
                    quiz_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .limit(
                1,
            ),
            operation="verify Quiz ownership",
        )

        ownership_rows = self._extract_rows(
            ownership_response,
            resource="Quiz",
        )

        if not ownership_rows:
            raise QuizAttemptNotFoundError(
                "The requested Quiz was not found.",
            )

        response = self._execute_query(
            self._client
            .table(
                "quiz_attempts",
            )
            .select(
                _QUIZ_ATTEMPT_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .eq(
                "quiz_id",
                str(
                    quiz_id,
                ),
            )
            .order(
                "started_at",
                desc=True,
            ),
            operation="list Quiz attempts",
        )

        rows = self._extract_rows(
            response,
            resource="Quiz attempt",
        )

        attempts: list[
            QuizAttemptResponse
        ] = []

        for row in rows:
            attempts.append(
                self._parse_attempt(
                    row,
                )
            )

        return tuple(
            attempts,
        )

    def list_answers(
        self,
        *,
        attempt_id: UUID,
    ) -> tuple[
        QuizAttemptAnswerResponse,
        ...,
    ]:
        """Return submitted answers for one already-owned attempt."""

        response = self._execute_query(
            self._client
            .table(
                "quiz_attempt_answers",
            )
            .select(
                _QUIZ_ATTEMPT_ANSWER_COLUMNS,
            )
            .eq(
                "attempt_id",
                str(
                    attempt_id,
                ),
            )
            .order(
                "position",
                desc=False,
            ),
            operation="list Quiz attempt answers",
        )

        rows = self._extract_rows(
            response,
            resource="Quiz attempt answer",
        )

        answers: list[
            QuizAttemptAnswerResponse
        ] = []

        for row in rows:
            try:
                answers.append(
                    QuizAttemptAnswerResponse.model_validate(
                        row,
                    )
                )

            except ValidationError as exc:
                raise QuizAttemptResponseError(
                    "Stored Quiz attempt answer data was invalid.",
                ) from exc

        return tuple(
            answers,
        )

    def list_review_questions(
        self,
        *,
        quiz_id: UUID,
    ) -> tuple[
        QuizReviewQuestionRecord,
        ...,
    ]:
        """Return private question data for a completed owned attempt."""

        response = self._execute_query(
            self._client
            .table(
                "quiz_questions",
            )
            .select(
                _QUIZ_REVIEW_QUESTION_COLUMNS,
            )
            .eq(
                "quiz_id",
                str(
                    quiz_id,
                ),
            )
            .order(
                "position",
                desc=False,
            ),
            operation="load Quiz review questions",
        )

        rows = self._extract_rows(
            response,
            resource="Quiz review question",
        )

        records: list[
            QuizReviewQuestionRecord
        ] = []

        for row in rows:
            public_payload = {
                "id": row.get(
                    "id",
                ),
                "position": row.get(
                    "position",
                ),
                "question_type": row.get(
                    "question_type",
                ),
                "topic": row.get(
                    "topic",
                ),
                "question": row.get(
                    "question",
                ),
                "choices": row.get(
                    "choices",
                ),
            }

            try:
                question = (
                    QuizQuestionResponse.model_validate(
                        public_payload,
                    )
                )

            except ValidationError as exc:
                raise QuizAttemptResponseError(
                    "Stored Quiz review question was invalid.",
                ) from exc

            correct_answer = row.get(
                "correct_answer",
            )

            explanation = row.get(
                "explanation",
            )

            if (
                not isinstance(
                    correct_answer,
                    str,
                )
                or not correct_answer.strip()
            ):
                raise QuizAttemptResponseError(
                    "Stored Quiz review answer was invalid.",
                )

            if (
                not isinstance(
                    explanation,
                    str,
                )
                or not explanation.strip()
            ):
                raise QuizAttemptResponseError(
                    "Stored Quiz review explanation was invalid.",
                )

            records.append(
                QuizReviewQuestionRecord(
                    question=question,
                    correct_answer=(
                        correct_answer.strip()
                    ),
                    explanation=(
                        explanation.strip()
                    ),
                )
            )

        return tuple(
            records,
        )

    def _execute_rpc(
        self,
        function_name: str,
        params: Mapping[
            str,
            object,
        ],
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one trusted Quiz-attempt RPC."""

        try:
            query = self._client.rpc(
                function_name,
                params,
            )

            return query.execute()

        except APIError as exc:
            self._raise_mapped_persistence_error(
                exc,
                operation=operation,
            )

    def _execute_query(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one Quiz-attempt table query."""

        try:
            return query.execute()

        except APIError as exc:
            raise QuizAttemptPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _raise_mapped_persistence_error(
        self,
        error: APIError,
        *,
        operation: str,
    ) -> None:
        """Convert trusted RPC state errors into controlled failures."""

        message = str(
            error,
        ).casefold()

        if (
            "requested quiz was not found"
            in message
            or
            "requested quiz attempt was not found"
            in message
            or
            "current quiz question was not found"
            in message
        ):
            raise QuizAttemptNotFoundError(
                "The requested Quiz resource was not found.",
            ) from error

        if (
            "already completed"
            in message
            or
            "position does not match"
            in message
        ):
            raise QuizAttemptConflictError(
                "The Quiz attempt state has changed.",
            ) from error

        raise QuizAttemptPersistenceError(
            f"Unable to {operation}.",
        ) from error

    def _extract_single_row(
        self,
        response: _SupabaseResponse,
        *,
        resource: str,
    ) -> Mapping[
        str,
        object,
    ]:
        """Require one row from an RPC response."""

        rows = self._extract_rows(
            response,
            resource=resource,
        )

        if len(
            rows,
        ) != 1:
            raise QuizAttemptResponseError(
                f"The {resource} response was invalid.",
            )

        return rows[
            0
        ]

    def _extract_rows(
        self,
        response: _SupabaseResponse,
        *,
        resource: str,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Validate generic Supabase list-row data."""

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            isinstance(
                data,
                (
                    str,
                    bytes,
                ),
            )
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise QuizAttemptResponseError(
                f"Supabase returned invalid {resource} data.",
            )

        rows: list[
            Mapping[
                str,
                object,
            ]
        ] = []

        for item in data:
            if not isinstance(
                item,
                Mapping,
            ):
                raise QuizAttemptResponseError(
                    f"Supabase returned an invalid {resource} row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_attempt(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> QuizAttemptResponse:
        """Parse one persisted Quiz-attempt row."""

        try:
            return QuizAttemptResponse.model_validate(
                row,
            )

        except ValidationError as exc:
            raise QuizAttemptResponseError(
                "Stored Quiz attempt data was invalid.",
            ) from exc