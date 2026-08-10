# File: /backend/app/repositories/quiz_repository.py
# Purpose: Atomically persists generated Quizzes and returns
# student-safe Quiz data without exposing private answer keys.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, Self
from uuid import UUID

from pydantic import ValidationError

from app.schemas.quiz import (
    QuizAttemptResponse,
    QuizDifficulty,
    QuizGeneratedContent,
    QuizQuestionResponse,
    QuizResponse,
    QuizScopeType,
    QuizSummaryResponse,
    QuizType,
)
from app.services.quiz_errors import (
    QuizPersistenceError,
    QuizResponseError,
    QuizValidationError,
)

_QUIZ_COLUMNS = (
    "id,"
    "subject_id,"
    "study_file_id,"
    "scope_type,"
    "title,"
    "quiz_type,"
    "difficulty,"
    "question_count,"
    "generation_model,"
    "generation_count,"
    "generated_at,"
    "created_at,"
    "updated_at"
)

_QUIZ_SUMMARY_COLUMNS = (
    "id,"
    "subject_id,"
    "study_file_id,"
    "scope_type,"
    "title,"
    "quiz_type,"
    "difficulty,"
    "question_count,"
    "generated_at,"
    "created_at,"
    "updated_at"
)

# Deliberately excludes:
# correct_answer
# accepted_answers
# explanation
_QUIZ_QUESTION_PUBLIC_COLUMNS = (
    "id,"
    "position,"
    "question_type,"
    "topic,"
    "question,"
    "choices"
)

_QUIZ_ATTEMPT_SUMMARY_COLUMNS = (
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

    def delete(
        self,
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


class QuizRepository:
    """Persist and read Quizzes belonging to one student."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

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
        """Atomically save and return one generated Quiz."""

        normalized_model = generation_model.strip()

        if not normalized_model:
            raise QuizValidationError(
                "Quiz generation model must not be empty.",
            )

        if (
            isinstance(
                question_count,
                bool,
            )
            or not isinstance(
                question_count,
                int,
            )
            or not 1 <= question_count <= 50
        ):
            raise QuizValidationError(
                "Quiz question count must be between 1 and 50.",
            )

        if (
            len(
                content.questions,
            )
            != question_count
        ):
            raise QuizValidationError(
                "Generated Quiz count does not match "
                "the requested count.",
            )

        if (
            scope_type is QuizScopeType.FILE
            and study_file_id is None
        ):
            raise QuizValidationError(
                "File-scope Quizzes require a study file.",
            )

        if (
            scope_type is QuizScopeType.SUBJECT
            and study_file_id is not None
        ):
            raise QuizValidationError(
                "Subject-scope Quizzes cannot store "
                "a study file.",
            )

        params: dict[
            str,
            object,
        ] = {
            "p_user_id": str(
                user_id,
            ),
            "p_subject_id": str(
                subject_id,
            ),
            "p_study_file_id": (
                str(
                    study_file_id,
                )
                if study_file_id is not None
                else None
            ),
            "p_scope_type": scope_type.value,
            "p_title": content.title,
            "p_quiz_type": quiz_type.value,
            "p_difficulty": difficulty.value,
            "p_question_count": question_count,
            "p_generation_model": normalized_model,
            "p_questions": [
                question.model_dump(
                    mode="json",
                )
                for question in content.questions
            ],
        }

        try:
            rpc_query = self._client.rpc(
                "create_quiz_with_questions",
                params,
            )

        except Exception as exc:
            raise QuizPersistenceError(
                "Unable to prepare Quiz persistence.",
            ) from exc

        response = self._execute_rpc(
            rpc_query,
            operation="create the Quiz",
        )

        quiz_id = self._extract_created_quiz_id(
            response,
        )

        quiz = self.get_quiz(
            user_id=user_id,
            quiz_id=quiz_id,
        )

        if quiz is None:
            raise QuizResponseError(
                "The created Quiz could not be loaded.",
            )

        return quiz

    def get_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizResponse | None:
        """Return one owned Quiz without its private answer key."""

        quiz_response = self._execute(
            self._client
            .table(
                "quizzes",
            )
            .select(
                _QUIZ_COLUMNS,
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
            operation="load the Quiz",
        )

        quiz_rows = self._extract_rows(
            quiz_response,
            resource="Quiz",
        )

        if not quiz_rows:
            return None

        if len(
            quiz_rows,
        ) != 1:
            raise QuizResponseError(
                "The Quiz lookup response was invalid.",
            )

        question_response = self._execute(
            self._client
            .table(
                "quiz_questions",
            )
            .select(
                _QUIZ_QUESTION_PUBLIC_COLUMNS,
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
            operation="load the Quiz questions",
        )

        question_rows = self._extract_rows(
            question_response,
            resource="Quiz question",
        )

        questions = self._parse_questions(
            question_rows,
        )

        return self._parse_quiz(
            quiz_rows[0],
            questions=questions,
        )

    def list_quizzes(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        QuizSummaryResponse,
        ...,
    ]:
        """Return saved Quizzes with latest attempt summaries."""

        quiz_response = self._execute(
            self._client
            .table(
                "quizzes",
            )
            .select(
                _QUIZ_SUMMARY_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "created_at",
                desc=True,
            ),
            operation="list saved Quizzes",
        )

        quiz_rows = self._extract_rows(
            quiz_response,
            resource="Quiz",
        )

        if not quiz_rows:
            return ()

        quiz_ids = {
            str(
                row.get(
                    "id",
                )
            )
            for row in quiz_rows
        }

        attempt_response = self._execute(
            self._client
            .table(
                "quiz_attempts",
            )
            .select(
                _QUIZ_ATTEMPT_SUMMARY_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "started_at",
                desc=True,
            ),
            operation="list Quiz attempt summaries",
        )

        attempt_rows = self._extract_rows(
            attempt_response,
            resource="Quiz attempt",
        )

        attempt_counts: dict[
            str,
            int,
        ] = {}

        latest_attempts: dict[
            str,
            QuizAttemptResponse,
        ] = {}

        for row in attempt_rows:
            try:
                attempt = (
                    QuizAttemptResponse.model_validate(
                        row,
                    )
                )

            except ValidationError as exc:
                raise QuizResponseError(
                    "Stored Quiz attempt summary was invalid.",
                ) from exc

            quiz_key = str(
                attempt.quiz_id,
            )

            if quiz_key not in quiz_ids:
                continue

            attempt_counts[
                quiz_key
            ] = (
                attempt_counts.get(
                    quiz_key,
                    0,
                )
                + 1
            )

            if quiz_key not in latest_attempts:
                latest_attempts[
                    quiz_key
                ] = attempt

        summaries: list[
            QuizSummaryResponse
        ] = []

        for row in quiz_rows:
            quiz_key = str(
                row.get(
                    "id",
                )
            )

            payload = dict(
                row,
            )

            payload[
                "attempt_count"
            ] = attempt_counts.get(
                quiz_key,
                0,
            )

            payload[
                "latest_attempt"
            ] = latest_attempts.get(
                quiz_key,
            )

            try:
                summaries.append(
                    QuizSummaryResponse.model_validate(
                        payload,
                    )
                )

            except ValidationError as exc:
                raise QuizResponseError(
                    "Stored Quiz summary data was invalid.",
                ) from exc

        return tuple(
            summaries,
        )

    def delete_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> bool:
        """Delete one Quiz belonging to the student."""

        response = self._execute(
            self._client
            .table(
                "quizzes",
            )
            .delete()
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
            ),
            operation="delete the Quiz",
        )

        rows = self._extract_rows(
            response,
            resource="Quiz",
        )

        return bool(
            rows,
        )

    def _execute(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one Supabase table query safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise QuizPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _execute_rpc(
        self,
        query: _SupabaseRpcQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one trusted Supabase RPC safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise QuizPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _extract_created_quiz_id(
        self,
        response: _SupabaseResponse,
    ) -> UUID:
        """Extract the UUID returned by the persistence RPC."""

        data = getattr(
            response,
            "data",
            None,
        )

        candidate: object = data

        if (
            isinstance(
                data,
                Sequence,
            )
            and not isinstance(
                data,
                (str, bytes),
            )
        ):
            if len(
                data,
            ) != 1:
                raise QuizResponseError(
                    "Quiz persistence returned an invalid Quiz ID.",
                )

            candidate = data[
                0
            ]

        try:
            return UUID(
                str(
                    candidate,
                )
            )

        except (
            TypeError,
            ValueError,
            AttributeError,
        ) as exc:
            raise QuizResponseError(
                "Quiz persistence returned an invalid Quiz ID.",
            ) from exc

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
        """Validate and normalize Supabase row data."""

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            isinstance(
                data,
                (str, bytes),
            )
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise QuizResponseError(
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
                raise QuizResponseError(
                    f"Supabase returned an invalid {resource} row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_questions(
        self,
        rows: Sequence[
            Mapping[
                str,
                object,
            ]
        ],
    ) -> tuple[
        QuizQuestionResponse,
        ...,
    ]:
        """Parse student-safe Quiz questions."""

        questions: list[
            QuizQuestionResponse
        ] = []

        for row in rows:
            try:
                question = (
                    QuizQuestionResponse.model_validate(
                        row,
                    )
                )

            except ValidationError as exc:
                raise QuizResponseError(
                    "The stored Quiz question data was invalid.",
                ) from exc

            questions.append(
                question,
            )

        return tuple(
            questions,
        )

    def _parse_quiz(
        self,
        row: Mapping[
            str,
            object,
        ],
        *,
        questions: tuple[
            QuizQuestionResponse,
            ...,
        ],
    ) -> QuizResponse:
        """Parse one Quiz row into a student-safe response."""

        payload = dict(
            row,
        )

        payload[
            "questions"
        ] = questions

        try:
            return QuizResponse.model_validate(
                payload,
            )

        except ValidationError as exc:
            raise QuizResponseError(
                "The stored Quiz data was invalid.",
            ) from exc