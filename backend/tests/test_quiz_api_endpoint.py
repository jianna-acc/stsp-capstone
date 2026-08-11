# File: /backend/tests/test_quiz_api_endpoint.py

# Purpose: Tests authenticated Quiz API endpoints without
# requiring live Supabase or Gemini services.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.quiz_dependency import (
    get_quiz_service,
)
from app.api.quiz_orchestration_dependency import (
    get_quiz_orchestration_service,
)
from app.api.routes.quizzes import (
    router as quiz_router,
)
from app.database.supabase_client import (
    get_supabase_client,
)
from app.schemas.quiz import (
    QuizDifficulty,
    QuizGenerateRequest,
    QuizQuestionResponse,
    QuizQuestionType,
    QuizResponse,
    QuizScopeType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizGenerationError,
    QuizNotFoundError,
    QuizPersistenceError,
    QuizSourceUnavailableError,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

QUIZ_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

STUDY_FILE_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_quiz() -> QuizResponse:
    """Return one safe Quiz API response."""

    now = datetime.now(
        UTC,
    )

    return QuizResponse(
        id=QUIZ_ID,
        subject_id=SUBJECT_ID,
        study_file_id=STUDY_FILE_ID,
        scope_type=QuizScopeType.FILE,
        title="Biology Quiz",
        quiz_type=QuizType.MULTIPLE_CHOICE,
        difficulty=QuizDifficulty.MEDIUM,
        question_count=1,
        questions=(
            QuizQuestionResponse(
                id=UUID(
                    "55555555-5555-4555-8555-555555555555"
                ),
                position=1,
                question_type=(
                    QuizQuestionType.MULTIPLE_CHOICE
                ),
                topic="Photosynthesis",
                question=(
                    "What process converts light energy "
                    "into chemical energy?"
                ),
                choices=(
                    "Photosynthesis",
                    "Respiration",
                    "Fermentation",
                    "Transpiration",
                ),
            ),
        ),
        generation_model="fake-model",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


class FakeQuizService:
    """Record synchronous saved-Quiz API operations."""

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

    def get_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizResponse:
        self.calls.append(
            (
                "get",
                user_id,
                quiz_id,
            )
        )

        self._raise_error()

        return make_quiz()

    def delete_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> None:
        self.calls.append(
            (
                "delete",
                user_id,
                quiz_id,
            )
        )

        self._raise_error()


class FakeQuizOrchestrationService:
    """Record asynchronous Quiz generation requests."""

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

    async def generate_quiz(
        self,
        *,
        user_id: UUID,
        request: QuizGenerateRequest,
    ) -> QuizResponse:
        self.calls.append(
            (
                "generate",
                user_id,
                request,
            )
        )

        if self.error is not None:
            raise self.error

        return make_quiz()


class UnusedFakeSupabaseClient:
    """Placeholder when real Supabase access is unnecessary."""

    auth = object()


def create_test_client(
    *,
    quiz_service: FakeQuizService | None = None,
    orchestration_service: (
        FakeQuizOrchestrationService | None
    ) = None,
    authenticated: bool = True,
) -> TestClient:
    """Create an isolated Quiz API application."""

    app = FastAPI()

    app.include_router(
        quiz_router,
        prefix="/api",
    )

    app.dependency_overrides[
        get_quiz_service
    ] = lambda: (
        quiz_service
        if quiz_service is not None
        else FakeQuizService()
    )

    app.dependency_overrides[
        get_quiz_orchestration_service
    ] = lambda: (
        orchestration_service
        if orchestration_service is not None
        else FakeQuizOrchestrationService()
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


def test_generate_quiz_uses_authenticated_owner() -> None:
    """Generation must use authenticated ownership."""

    orchestration = FakeQuizOrchestrationService()

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/quizzes/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "quiz_type": "multiple_choice",
                "difficulty": "medium",
                "question_count": 1,
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body[
        "id"
    ] == str(
        QUIZ_ID,
    )

    assert body[
        "title"
    ] == "Biology Quiz"

    assert "user_id" not in body

    call = orchestration.calls[
        0
    ]

    assert call[
        0
    ] == "generate"

    assert call[
        1
    ] == USER_ID

    request = call[
        2
    ]

    assert isinstance(
        request,
        QuizGenerateRequest,
    )

    assert request.study_file_id == (
        STUDY_FILE_ID
    )


def test_generate_response_never_exposes_answer_key() -> None:
    """Generated Quiz response must hide private answer data."""

    with create_test_client() as client:
        response = client.post(
            "/api/quizzes/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "quiz_type": "multiple_choice",
                "difficulty": "medium",
                "question_count": 1,
            },
        )

    assert response.status_code == 201

    question = response.json()[
        "questions"
    ][
        0
    ]

    assert "correct_answer" not in question
    assert "accepted_answers" not in question
    assert "explanation" not in question


def test_get_quiz_uses_authenticated_owner() -> None:
    """Single Quiz retrieval must remain ownership scoped."""

    service = FakeQuizService()

    with create_test_client(
        quiz_service=service,
    ) as client:
        response = client.get(
            f"/api/quizzes/{QUIZ_ID}",
        )

    assert response.status_code == 200

    assert response.json()[
        "id"
    ] == str(
        QUIZ_ID,
    )

    assert service.calls == [
        (
            "get",
            USER_ID,
            QUIZ_ID,
        )
    ]


def test_delete_quiz_returns_no_content() -> None:
    """Successful Quiz deletion must return HTTP 204."""

    service = FakeQuizService()

    with create_test_client(
        quiz_service=service,
    ) as client:
        response = client.delete(
            f"/api/quizzes/{QUIZ_ID}",
        )

    assert response.status_code == 204
    assert response.content == b""

    assert service.calls == [
        (
            "delete",
            USER_ID,
            QUIZ_ID,
        )
    ]


def test_missing_quiz_returns_404() -> None:
    """Owned Quiz lookup failures must return a safe 404."""

    service = FakeQuizService(
        error=QuizNotFoundError(
            "missing",
        ),
    )

    with create_test_client(
        quiz_service=service,
    ) as client:
        response = client.get(
            f"/api/quizzes/{QUIZ_ID}",
        )

    assert response.status_code == 404

    assert response.json()[
        "error_code"
    ] == "QUIZ_NOT_FOUND"


def test_unready_source_returns_409() -> None:
    """Quiz generation must expose source-state conflicts safely."""

    orchestration = FakeQuizOrchestrationService(
        error=QuizSourceUnavailableError(
            "not ready",
        ),
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/quizzes/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "quiz_type": "mixed",
                "difficulty": "medium",
                "question_count": 10,
            },
        )

    assert response.status_code == 409

    assert response.json()[
        "error_code"
    ] == "QUIZ_SOURCE_UNAVAILABLE"


def test_generation_failure_returns_502() -> None:
    """Provider failures must return a safe gateway error."""

    orchestration = FakeQuizOrchestrationService(
        error=QuizGenerationError(
            "provider failed",
        ),
    )

    with create_test_client(
        orchestration_service=orchestration,
    ) as client:
        response = client.post(
            "/api/quizzes/generate",
            json={
                "scope_type": "file",
                "subject_id": str(
                    SUBJECT_ID,
                ),
                "study_file_id": str(
                    STUDY_FILE_ID,
                ),
                "quiz_type": "multiple_choice",
                "difficulty": "medium",
                "question_count": 5,
            },
        )

    assert response.status_code == 502

    assert response.json()[
        "error_code"
    ] == "QUIZ_GENERATION_FAILED"


def test_persistence_failure_returns_503() -> None:
    """Quiz storage failures must become service unavailable."""

    service = FakeQuizService(
        error=QuizPersistenceError(
            "database unavailable",
        ),
    )

    with create_test_client(
        quiz_service=service,
    ) as client:
        response = client.get(
            f"/api/quizzes/{QUIZ_ID}",
        )

    assert response.status_code == 503

    assert response.json()[
        "error_code"
    ] == "QUIZ_PERSISTENCE_FAILED"


def test_unauthenticated_quiz_request_returns_401() -> None:
    """Quiz endpoints must require student authentication."""

    with create_test_client(
        authenticated=False,
    ) as client:
        response = client.get(
            f"/api/quizzes/{QUIZ_ID}",
        )

    assert response.status_code == 401