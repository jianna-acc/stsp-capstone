# File: /backend/tests/test_quiz_attempt_api_endpoint.py

# Purpose: Tests authenticated Quiz-attempt APIs without
# requiring live Supabase services.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.quiz_attempt_dependency import (
    get_quiz_attempt_service,
)
from app.api.routes.quiz_attempts import (
    router as quiz_attempt_router,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.repositories.quiz_attempt_repository import (
    QuizAnswerSubmissionResult,
)
from app.schemas.quiz import (
    QuizAnswerFeedbackResponse,
    QuizAnswerSubmissionRequest,
    QuizAttemptResponse,
    QuizAttemptResultResponse,
    QuizAttemptStatus,
    QuizTopicResult,
)
from app.services.quiz_attempt_errors import (
    QuizAttemptConflictError,
    QuizAttemptNotFoundError,
    QuizAttemptPersistenceError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

QUIZ_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

ATTEMPT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

QUESTION_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_attempt(
    *,
    completed: bool = False,
) -> QuizAttemptResponse:
    """Return one safe Quiz-attempt response."""

    now = datetime.now(
        UTC,
    )

    question_count = 2

    return QuizAttemptResponse(
        id=ATTEMPT_ID,
        quiz_id=QUIZ_ID,
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
        correct_count=(
            1
            if completed
            else 0
        ),
        question_count=question_count,
        score_percentage=(
            50
            if completed
            else 0
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


class FakeQuizAttemptService:
    """Record Quiz-attempt API operations."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error

        self.calls: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def _raise_error(
        self,
    ) -> None:
        if self.error is not None:
            raise self.error

    def start_attempt(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizAttemptResponse:
        self.calls.append(
            (
                "start",
                user_id,
                quiz_id,
            )
        )

        self._raise_error()

        return make_attempt()

    def get_attempt(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResponse:
        self.calls.append(
            (
                "get",
                user_id,
                attempt_id,
            )
        )

        self._raise_error()

        return make_attempt()

    def submit_answer(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
        position: int,
        request: QuizAnswerSubmissionRequest,
    ) -> QuizAnswerSubmissionResult:
        self.calls.append(
            (
                "answer",
                user_id,
                attempt_id,
                position,
                request,
            )
        )

        self._raise_error()

        base_attempt = make_attempt()

        updated_attempt = QuizAttemptResponse(
            **base_attempt.model_dump(
                exclude={
                    "current_position",
                    "correct_count",
                    "score_percentage",
                },
            ),
            current_position=2,
            correct_count=1,
            score_percentage=50,
        )

        return QuizAnswerSubmissionResult(
            attempt=updated_attempt,
            feedback=QuizAnswerFeedbackResponse(
                attempt_id=ATTEMPT_ID,
                quiz_question_id=QUESTION_ID,
                position=1,
                is_correct=True,
                correct_answer="Jose Rizal",
                explanation=(
                    "The source identifies Jose Rizal."
                ),
                next_position=2,
                attempt_completed=False,
            ),
        )

    def get_result(
        self,
        *,
        user_id: UUID,
        attempt_id: UUID,
    ) -> QuizAttemptResultResponse:
        self.calls.append(
            (
                "result",
                user_id,
                attempt_id,
            )
        )

        self._raise_error()

        attempt = make_attempt(
            completed=True,
        )

        assert attempt.completed_at is not None

        return QuizAttemptResultResponse(
            attempt_id=ATTEMPT_ID,
            quiz_id=QUIZ_ID,
            correct_count=1,
            question_count=2,
            score_percentage=50,
            strong_topics=(
                QuizTopicResult(
                    topic="Rizal",
                    correct_count=1,
                    question_count=1,
                    accuracy_percentage=100,
                ),
            ),
            weak_topics=(
                QuizTopicResult(
                    topic="Reform Movement",
                    correct_count=0,
                    question_count=1,
                    accuracy_percentage=0,
                ),
            ),
            completed_at=attempt.completed_at,
        )


class UnusedFakeSupabaseClient:
    """Placeholder for isolated authentication tests."""

    auth = object()


def create_test_client(
    *,
    service: FakeQuizAttemptService | None = None,
    authenticated: bool = True,
) -> TestClient:
    """Create an isolated Quiz-attempt API application."""

    app = FastAPI()

    app.include_router(
        quiz_attempt_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_quiz_attempt_service
    ] = lambda: (
        service
        if service is not None
        else FakeQuizAttemptService()
    )

    app.dependency_overrides[
        get_supabase_client
    ] = lambda: UnusedFakeSupabaseClient()

    if authenticated:
        app.dependency_overrides[
            require_authenticated_user
        ] = lambda: AuthenticatedUser(
            user_id=USER_ID,
        )

    return TestClient(
        app,
    )


def test_start_attempt_uses_authenticated_owner() -> None:
    """Attempt creation must use authenticated ownership."""

    service = FakeQuizAttemptService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            f"/api/quizzes/{QUIZ_ID}/attempts",
        )

    assert response.status_code == 201

    assert response.json()[
        "id"
    ] == str(
        ATTEMPT_ID,
    )

    assert service.calls == [
        (
            "start",
            USER_ID,
            QUIZ_ID,
        )
    ]


def test_get_attempt_uses_authenticated_owner() -> None:
    """Attempt retrieval must remain ownership scoped."""

    service = FakeQuizAttemptService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            f"/api/quiz-attempts/{ATTEMPT_ID}",
        )

    assert response.status_code == 200

    assert service.calls == [
        (
            "get",
            USER_ID,
            ATTEMPT_ID,
        )
    ]


def test_submit_answer_returns_immediate_feedback() -> None:
    """Submission must return correctness and explanation."""

    service = FakeQuizAttemptService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            (
                f"/api/quiz-attempts/{ATTEMPT_ID}"
                "/questions/1/answer"
            ),
            json={
                "answer": "Jose Rizal",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "feedback"
    ][
        "is_correct"
    ] is True

    assert body[
        "feedback"
    ][
        "correct_answer"
    ] == "Jose Rizal"

    assert body[
        "feedback"
    ][
        "explanation"
    ]

    assert body[
        "feedback"
    ][
        "next_position"
    ] == 2

    call = service.calls[
        0
    ]

    assert call[
        0
    ] == "answer"

    assert call[
        1
    ] == USER_ID

    assert call[
        2
    ] == ATTEMPT_ID

    assert call[
        3
    ] == 1


def test_completed_result_returns_score_and_topics() -> None:
    """Completed attempts expose final performance."""

    service = FakeQuizAttemptService()

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            (
                f"/api/quiz-attempts/"
                f"{ATTEMPT_ID}/result"
            ),
        )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "score_percentage"
    ] == 50

    assert body[
        "strong_topics"
    ][
        0
    ][
        "topic"
    ] == "Rizal"

    assert body[
        "weak_topics"
    ][
        0
    ][
        "topic"
    ] == "Reform Movement"


def test_missing_attempt_returns_404() -> None:
    """Missing owned attempts must return a safe 404."""

    service = FakeQuizAttemptService(
        error=QuizAttemptNotFoundError(
            "missing",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            f"/api/quiz-attempts/{ATTEMPT_ID}",
        )

    assert response.status_code == 404

    assert response.json()[
        "error_code"
    ] == "QUIZ_ATTEMPT_NOT_FOUND"


def test_attempt_conflict_returns_409() -> None:
    """Completed or stale operations must return 409."""

    service = FakeQuizAttemptService(
        error=QuizAttemptConflictError(
            "stale",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.post(
            (
                f"/api/quiz-attempts/{ATTEMPT_ID}"
                "/questions/1/answer"
            ),
            json={
                "answer": "Jose Rizal",
            },
        )

    assert response.status_code == 409

    assert response.json()[
        "error_code"
    ] == "QUIZ_ATTEMPT_CONFLICT"


def test_attempt_persistence_failure_returns_503() -> None:
    """Storage failures must return service unavailable."""

    service = FakeQuizAttemptService(
        error=QuizAttemptPersistenceError(
            "database unavailable",
        ),
    )

    with create_test_client(
        service=service,
    ) as client:
        response = client.get(
            f"/api/quiz-attempts/{ATTEMPT_ID}",
        )

    assert response.status_code == 503

    assert response.json()[
        "error_code"
    ] == "QUIZ_ATTEMPT_PERSISTENCE_FAILED"


def test_unauthenticated_attempt_request_returns_401() -> None:
    """Quiz-attempt endpoints require authentication."""

    with create_test_client(
        authenticated=False,
    ) as client:
        response = client.get(
            f"/api/quiz-attempts/{ATTEMPT_ID}",
        )

    assert response.status_code == 401