# File: /backend/tests/test_quiz_repository.py

# Purpose: Verifies atomic Quiz persistence, owned retrieval,
# deletion, response validation, and answer-key protection.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.quiz_repository import (
    QuizRepository,
)
from app.schemas.quiz import (
    QuizDifficulty,
    QuizGeneratedContent,
    QuizGeneratedQuestion,
    QuizQuestionType,
    QuizScopeType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizPersistenceError,
    QuizResponseError,
    QuizValidationError,
)


class FakeResponse:
    """Minimal Supabase-style response."""

    def __init__(
        self,
        data: object,
    ) -> None:
        self.data = data


class FakeQuery:
    """Record chained Supabase table operations."""

    def __init__(
        self,
        response_data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error
        self.operations: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.operations.append(
            (
                "select",
                columns,
            )
        )
        return self

    def delete(
        self,
    ) -> FakeQuery:
        self.operations.append(
            (
                "delete",
                None,
            )
        )
        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.operations.append(
            (
                "eq",
                (
                    column,
                    value,
                ),
            )
        )
        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> FakeQuery:
        self.operations.append(
            (
                "order",
                (
                    column,
                    desc,
                ),
            )
        )
        return self

    def limit(
        self,
        count: int,
    ) -> FakeQuery:
        self.operations.append(
            (
                "limit",
                count,
            )
        )
        return self

    def execute(
        self,
    ) -> FakeResponse:
        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.response_data,
        )


class FakeRpcQuery:
    """Record one fake Supabase RPC execution."""

    def __init__(
        self,
        response_data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response_data = response_data
        self.error = error

    def execute(
        self,
    ) -> FakeResponse:
        if self.error is not None:
            raise self.error

        return FakeResponse(
            self.response_data,
        )


class FakeClient:
    """Minimal Supabase client for Quiz repository tests."""

    def __init__(
        self,
        *,
        table_queries: dict[
            str,
            FakeQuery,
        ],
        rpc_query: FakeRpcQuery | None = None,
    ) -> None:
        self.table_queries = table_queries
        self.rpc_query = rpc_query
        self.table_names: list[
            str
        ] = []
        self.rpc_calls: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        self.table_names.append(
            table_name,
        )

        return self.table_queries[
            table_name
        ]

    def rpc(
        self,
        function_name: str,
        params: object,
    ) -> FakeRpcQuery:
        self.rpc_calls.append(
            (
                function_name,
                params,
            )
        )

        if self.rpc_query is None:
            raise RuntimeError(
                "No RPC query configured.",
            )

        return self.rpc_query


def _generated_content() -> QuizGeneratedContent:
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
                    "Emilio Aguinaldo",
                    "Apolinario Mabini",
                ),
                correct_answer="Jose Rizal",
                explanation="Jose Rizal wrote the novel.",
            ),
        ),
    )


def _quiz_row(
    *,
    quiz_id: UUID,
    subject_id: UUID,
    study_file_id: UUID | None = None,
    scope_type: str = "subject",
) -> dict[
    str,
    object,
]:
    """Return one valid stored Quiz row."""

    now = datetime.now(
        UTC,
    ).isoformat()

    return {
        "id": str(
            quiz_id,
        ),
        "subject_id": str(
            subject_id,
        ),
        "study_file_id": (
            str(
                study_file_id,
            )
            if study_file_id is not None
            else None
        ),
        "scope_type": scope_type,
        "title": "Rizal Quiz",
        "quiz_type": "multiple_choice",
        "difficulty": "medium",
        "question_count": 1,
        "generation_model": "gemini-test-model",
        "generation_count": 1,
        "generated_at": now,
        "created_at": now,
        "updated_at": now,
    }


def _question_row() -> dict[
    str,
    object,
]:
    """Return one student-safe stored question row."""

    return {
        "id": str(
            uuid4(),
        ),
        "position": 1,
        "question_type": "multiple_choice",
        "topic": "Rizal",
        "question": "Who wrote Noli Me Tangere?",
        "choices": [
            "Jose Rizal",
            "Andres Bonifacio",
            "Emilio Aguinaldo",
            "Apolinario Mabini",
        ],
    }


def test_create_quiz_uses_atomic_rpc_and_returns_safe_quiz() -> None:
    """Creation must persist the complete Quiz through one RPC."""

    user_id = uuid4()
    subject_id = uuid4()
    quiz_id = uuid4()

    quiz_query = FakeQuery(
        [
            _quiz_row(
                quiz_id=quiz_id,
                subject_id=subject_id,
            ),
        ],
    )

    question_query = FakeQuery(
        [
            _question_row(),
        ],
    )

    client = FakeClient(
        table_queries={
            "quizzes": quiz_query,
            "quiz_questions": question_query,
        },
        rpc_query=FakeRpcQuery(
            str(
                quiz_id,
            ),
        ),
    )

    repository = QuizRepository(
        client,
    )

    result = repository.create_quiz(
        user_id=user_id,
        subject_id=subject_id,
        study_file_id=None,
        scope_type=QuizScopeType.SUBJECT,
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=1,
        content=_generated_content(),
        generation_model="gemini-test-model",
    )

    assert result.id == quiz_id
    assert result.subject_id == subject_id
    assert len(
        result.questions,
    ) == 1

    assert len(
        client.rpc_calls,
    ) == 1

    function_name, params = (
        client.rpc_calls[
            0
        ]
    )

    assert (
        function_name
        == "create_quiz_with_questions"
    )

    assert isinstance(
        params,
        dict,
    )

    assert params[
        "p_user_id"
    ] == str(
        user_id,
    )

    assert params[
        "p_subject_id"
    ] == str(
        subject_id,
    )

    assert params[
        "p_scope_type"
    ] == "subject"

    assert params[
        "p_quiz_type"
    ] == "multiple_choice"

    assert params[
        "p_difficulty"
    ] == "medium"

    assert params[
        "p_question_count"
    ] == 1

    questions = params[
        "p_questions"
    ]

    assert isinstance(
        questions,
        list,
    )

    assert questions[
        0
    ][
        "correct_answer"
    ] == "Jose Rizal"


def test_get_quiz_never_selects_private_answer_fields() -> None:
    """Student Quiz retrieval must not query answer-key columns."""

    user_id = uuid4()
    subject_id = uuid4()
    quiz_id = uuid4()

    quiz_query = FakeQuery(
        [
            _quiz_row(
                quiz_id=quiz_id,
                subject_id=subject_id,
            ),
        ],
    )

    question_query = FakeQuery(
        [
            _question_row(),
        ],
    )

    repository = QuizRepository(
        FakeClient(
            table_queries={
                "quizzes": quiz_query,
                "quiz_questions": question_query,
            },
        )
    )

    result = repository.get_quiz(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    assert result is not None

    select_operations = [
        value
        for operation, value in question_query.operations
        if operation == "select"
    ]

    assert len(
        select_operations,
    ) == 1

    columns = select_operations[
        0
    ]

    assert isinstance(
        columns,
        str,
    )

    assert "correct_answer" not in columns
    assert "accepted_answers" not in columns
    assert "explanation" not in columns

    payload = result.questions[
        0
    ].model_dump()

    assert "correct_answer" not in payload
    assert "accepted_answers" not in payload
    assert "explanation" not in payload


def test_get_quiz_filters_authenticated_owner() -> None:
    """Quiz lookup must filter by Quiz ID and owner."""

    user_id = uuid4()
    subject_id = uuid4()
    quiz_id = uuid4()

    quiz_query = FakeQuery(
        [
            _quiz_row(
                quiz_id=quiz_id,
                subject_id=subject_id,
            ),
        ],
    )

    repository = QuizRepository(
        FakeClient(
            table_queries={
                "quizzes": quiz_query,
                "quiz_questions": FakeQuery(
                    [
                        _question_row(),
                    ],
                ),
            },
        )
    )

    result = repository.get_quiz(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    assert result is not None

    assert (
        "eq",
        (
            "id",
            str(
                quiz_id,
            ),
        ),
    ) in quiz_query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in quiz_query.operations


def test_get_missing_quiz_does_not_load_questions() -> None:
    """Missing owned Quiz must return before loading questions."""

    question_query = FakeQuery(
        [
            _question_row(),
        ],
    )

    client = FakeClient(
        table_queries={
            "quizzes": FakeQuery(
                [],
            ),
            "quiz_questions": question_query,
        },
    )

    result = QuizRepository(
        client,
    ).get_quiz(
        user_id=uuid4(),
        quiz_id=uuid4(),
    )

    assert result is None

    assert "quiz_questions" not in (
        client.table_names
    )


def test_delete_quiz_filters_owner() -> None:
    """Deletion must target one owned Quiz."""

    user_id = uuid4()
    quiz_id = uuid4()

    query = FakeQuery(
        [
            {
                "id": str(
                    quiz_id,
                ),
            },
        ],
    )

    repository = QuizRepository(
        FakeClient(
            table_queries={
                "quizzes": query,
            },
        )
    )

    deleted = repository.delete_quiz(
        user_id=user_id,
        quiz_id=quiz_id,
    )

    assert deleted is True

    assert (
        "eq",
        (
            "id",
            str(
                quiz_id,
            ),
        ),
    ) in query.operations

    assert (
        "eq",
        (
            "user_id",
            str(
                user_id,
            ),
        ),
    ) in query.operations


def test_create_quiz_rejects_question_count_mismatch() -> None:
    """Persistence must reject incomplete generated Quiz data."""

    repository = QuizRepository(
        FakeClient(
            table_queries={},
        )
    )

    with pytest.raises(
        QuizValidationError,
    ):
        repository.create_quiz(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=QuizScopeType.SUBJECT,
            quiz_type=QuizType.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.MEDIUM,
            question_count=2,
            content=_generated_content(),
            generation_model="gemini-test-model",
        )


def test_create_file_quiz_requires_file() -> None:
    """File-scope Quiz persistence must require study_file_id."""

    repository = QuizRepository(
        FakeClient(
            table_queries={},
        )
    )

    with pytest.raises(
        QuizValidationError,
    ):
        repository.create_quiz(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=QuizScopeType.FILE,
            quiz_type=QuizType.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.MEDIUM,
            question_count=1,
            content=_generated_content(),
            generation_model="gemini-test-model",
        )


def test_rpc_failure_becomes_persistence_error() -> None:
    """Supabase RPC failures must become controlled errors."""

    repository = QuizRepository(
        FakeClient(
            table_queries={},
            rpc_query=FakeRpcQuery(
                None,
                error=RuntimeError(
                    "database unavailable",
                ),
            ),
        )
    )

    with pytest.raises(
        QuizPersistenceError,
    ):
        repository.create_quiz(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=QuizScopeType.SUBJECT,
            quiz_type=QuizType.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.MEDIUM,
            question_count=1,
            content=_generated_content(),
            generation_model="gemini-test-model",
        )


def test_invalid_rpc_identifier_is_rejected() -> None:
    """Persistence must reject malformed RPC responses."""

    repository = QuizRepository(
        FakeClient(
            table_queries={},
            rpc_query=FakeRpcQuery(
                "not-a-uuid",
            ),
        )
    )

    with pytest.raises(
        QuizResponseError,
    ):
        repository.create_quiz(
            user_id=uuid4(),
            subject_id=uuid4(),
            study_file_id=None,
            scope_type=QuizScopeType.SUBJECT,
            quiz_type=QuizType.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.MEDIUM,
            question_count=1,
            content=_generated_content(),
            generation_model="gemini-test-model",
        )