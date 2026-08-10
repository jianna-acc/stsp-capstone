# File: /backend/app/api/routes/quiz_attempts.py
# Purpose: Provides authenticated Quiz-attempt start, history,
# retrieval, answer-submission, final-result, and review endpoints.

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.quiz_attempt_dependency import (
    get_quiz_attempt_service,
)
from app.repositories.quiz_attempt_repository import (
    QuizAnswerSubmissionResult,
)
from app.schemas.quiz import (
    QuizAnswerSubmissionRequest,
    QuizAnswerSubmissionResponse,
    QuizApiErrorResponse,
    QuizAttemptListResponse,
    QuizAttemptResponse,
    QuizAttemptResultResponse,
    QuizAttemptReviewResponse,
)
from app.services.quiz_attempt_errors import (
    QuizAttemptConflictError,
    QuizAttemptError,
    QuizAttemptNotFoundError,
    QuizAttemptPersistenceError,
    QuizAttemptResponseError,
    QuizAttemptValidationError,
)
from app.services.quiz_attempt_service import (
    QuizAttemptService,
)

router = APIRouter(
    tags=[
        "quiz-attempts",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": QuizApiErrorResponse,
        "description": (
            "The Quiz-attempt operation is invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": QuizApiErrorResponse,
        "description": (
            "The requested Quiz or Quiz attempt was not found."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": QuizApiErrorResponse,
        "description": (
            "The Quiz attempt is not in the required state."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": QuizApiErrorResponse,
        "description": (
            "Quiz-attempt storage is temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": QuizApiErrorResponse,
        "description": (
            "The Quiz-attempt response could not be completed."
        ),
    },
}


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def start_quiz_attempt(
    quiz_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizAttemptService,
        Depends(
            get_quiz_attempt_service,
        ),
    ],
) -> QuizAttemptResponse | JSONResponse:
    """Start one fresh attempt for an owned Quiz."""

    try:
        return await run_in_threadpool(
            service.start_attempt,
            user_id=authenticated_user.user_id,
            quiz_id=quiz_id,
        )

    except QuizAttemptError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def list_quiz_attempts(
    quiz_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizAttemptService,
        Depends(
            get_quiz_attempt_service,
        ),
    ],
) -> QuizAttemptListResponse | JSONResponse:
    """Return attempt history for one owned Quiz."""

    try:
        return await run_in_threadpool(
            service.list_attempts,
            user_id=authenticated_user.user_id,
            quiz_id=quiz_id,
        )

    except QuizAttemptError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/quiz-attempts/{attempt_id}",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def get_quiz_attempt(
    attempt_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizAttemptService,
        Depends(
            get_quiz_attempt_service,
        ),
    ],
) -> QuizAttemptResponse | JSONResponse:
    """Return one owned Quiz attempt."""

    try:
        return await run_in_threadpool(
            service.get_attempt,
            user_id=authenticated_user.user_id,
            attempt_id=attempt_id,
        )

    except QuizAttemptError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.post(
    (
        "/quiz-attempts/{attempt_id}"
        "/questions/{position}/answer"
    ),
    response_model=QuizAnswerSubmissionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def submit_quiz_answer(
    attempt_id: UUID,
    position: int,
    payload: QuizAnswerSubmissionRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizAttemptService,
        Depends(
            get_quiz_attempt_service,
        ),
    ],
) -> QuizAnswerSubmissionResponse | JSONResponse:
    """Submit and immediately grade the current Quiz question."""

    try:
        result = await run_in_threadpool(
            service.submit_answer,
            user_id=authenticated_user.user_id,
            attempt_id=attempt_id,
            position=position,
            request=payload,
        )

        return _build_submission_response(
            result,
        )

    except QuizAttemptError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/quiz-attempts/{attempt_id}/result",
    response_model=QuizAttemptResultResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def get_quiz_attempt_result(
    attempt_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizAttemptService,
        Depends(
            get_quiz_attempt_service,
        ),
    ],
) -> QuizAttemptResultResponse | JSONResponse:
    """Return final score and topic strengths for a completed attempt."""

    try:
        return await run_in_threadpool(
            service.get_result,
            user_id=authenticated_user.user_id,
            attempt_id=attempt_id,
        )

    except QuizAttemptError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/quiz-attempts/{attempt_id}/review",
    response_model=QuizAttemptReviewResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def get_quiz_attempt_review(
    attempt_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizAttemptService,
        Depends(
            get_quiz_attempt_service,
        ),
    ],
) -> QuizAttemptReviewResponse | JSONResponse:
    """Return answer review for one completed owned attempt."""

    try:
        return await run_in_threadpool(
            service.get_review,
            user_id=authenticated_user.user_id,
            attempt_id=attempt_id,
        )

    except QuizAttemptError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_submission_response(
    result: QuizAnswerSubmissionResult,
) -> QuizAnswerSubmissionResponse:
    """Convert a submitted answer into the public API contract."""

    return QuizAnswerSubmissionResponse(
        attempt=result.attempt,
        feedback=result.feedback,
    )


def _build_controlled_error_response(
    error: QuizAttemptError,
) -> JSONResponse:
    """Convert controlled Quiz-attempt errors into safe HTTP responses."""

    if isinstance(
        error,
        QuizAttemptValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "QUIZ_ATTEMPT_VALIDATION_FAILED"
        message = "The Quiz-attempt operation is invalid."

    elif isinstance(
        error,
        QuizAttemptNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "QUIZ_ATTEMPT_NOT_FOUND"
        message = (
            "The requested Quiz or Quiz attempt was not found."
        )

    elif isinstance(
        error,
        QuizAttemptConflictError,
    ):
        status_code = status.HTTP_409_CONFLICT
        error_code = "QUIZ_ATTEMPT_CONFLICT"
        message = (
            "The Quiz attempt is not in the required state."
        )

    elif isinstance(
        error,
        QuizAttemptPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = "QUIZ_ATTEMPT_PERSISTENCE_FAILED"
        message = (
            "Quiz-attempt storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        QuizAttemptResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "QUIZ_ATTEMPT_RESPONSE_FAILED"
        message = (
            "The Quiz-attempt response could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "QUIZ_ATTEMPT_RESPONSE_FAILED"
        message = (
            "The Quiz-attempt response could not be completed."
        )

    body = QuizApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(
            mode="json",
        ),
    )