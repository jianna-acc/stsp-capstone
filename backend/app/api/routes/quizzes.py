# File: /backend/app/api/routes/quizzes.py
# Purpose: Provides authenticated Quiz generation,
# listing, retrieval, and deletion endpoints.

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

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
from app.schemas.quiz import (
    QuizApiErrorResponse,
    QuizGenerateRequest,
    QuizListResponse,
    QuizResponse,
)
from app.services.quiz_errors import (
    QuizError,
    QuizGenerationError,
    QuizGenerationResponseError,
    QuizNotFoundError,
    QuizPersistenceError,
    QuizResponseError,
    QuizSourceNotFoundError,
    QuizSourceUnavailableError,
    QuizValidationError,
)
from app.services.quiz_orchestration import (
    QuizOrchestrationService,
)
from app.services.quiz_service import (
    QuizService,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
)

router = APIRouter(
    prefix="/quizzes",
    tags=[
        "quizzes",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": QuizApiErrorResponse,
        "description": (
            "The Quiz request is invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": QuizApiErrorResponse,
        "description": (
            "The requested Quiz or source material "
            "was not found."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": QuizApiErrorResponse,
        "description": (
            "The selected study material is not ready "
            "for Quiz generation."
        ),
    },
    status.HTTP_502_BAD_GATEWAY: {
        "model": QuizApiErrorResponse,
        "description": (
            "The configured AI provider could not "
            "generate the Quiz."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": QuizApiErrorResponse,
        "description": (
            "Quiz storage or source loading is "
            "temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": QuizApiErrorResponse,
        "description": (
            "The Quiz response could not be completed."
        ),
    },
}


@router.post(
    "/generate",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def generate_quiz(
    payload: QuizGenerateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizOrchestrationService,
        Depends(
            get_quiz_orchestration_service,
        ),
    ],
) -> QuizResponse | JSONResponse:
    """Generate and atomically save one owned Quiz."""

    try:
        return await service.generate_quiz(
            user_id=authenticated_user.user_id,
            request=payload,
        )

    except QuizError as exc:
        return _build_controlled_error_response(
            exc,
        )

    except SupabaseAdminError:
        return _build_source_storage_error_response()


@router.get(
    "",
    response_model=QuizListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def list_quizzes(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizService,
        Depends(
            get_quiz_service,
        ),
    ],
) -> QuizListResponse | JSONResponse:
    """Return saved Quizzes owned by the student."""

    try:
        return await run_in_threadpool(
            service.list_quizzes,
            user_id=authenticated_user.user_id,
        )

    except QuizError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def get_quiz(
    quiz_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizService,
        Depends(
            get_quiz_service,
        ),
    ],
) -> QuizResponse | JSONResponse:
    """Return one saved Quiz owned by the student."""

    try:
        return await run_in_threadpool(
            service.get_quiz,
            user_id=authenticated_user.user_id,
            quiz_id=quiz_id,
        )

    except QuizError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{quiz_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        **_ERROR_RESPONSE_MODELS,
    },
)
async def delete_quiz(
    quiz_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        QuizService,
        Depends(
            get_quiz_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one saved Quiz owned by the student."""

    try:
        await run_in_threadpool(
            service.delete_quiz,
            user_id=authenticated_user.user_id,
            quiz_id=quiz_id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except QuizError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: QuizError,
) -> JSONResponse:
    """Convert controlled Quiz failures into safe API errors."""

    if isinstance(
        error,
        QuizValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "QUIZ_VALIDATION_FAILED"
        message = "The Quiz operation is invalid."

    elif isinstance(
        error,
        (
            QuizNotFoundError,
            QuizSourceNotFoundError,
        ),
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "QUIZ_NOT_FOUND"
        message = (
            "The requested Quiz or study material "
            "was not found."
        )

    elif isinstance(
        error,
        QuizSourceUnavailableError,
    ):
        status_code = status.HTTP_409_CONFLICT
        error_code = "QUIZ_SOURCE_UNAVAILABLE"
        message = (
            "The selected study material is not ready "
            "for Quiz generation."
        )

    elif isinstance(
        error,
        QuizPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = "QUIZ_PERSISTENCE_FAILED"
        message = (
            "Quiz storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        QuizGenerationResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "QUIZ_GENERATION_RESPONSE_FAILED"
        message = (
            "The generated Quiz could not be processed."
        )

    elif isinstance(
        error,
        QuizGenerationError,
    ):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_code = "QUIZ_GENERATION_FAILED"
        message = "The Quiz could not be generated."

    elif isinstance(
        error,
        QuizResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "QUIZ_RESPONSE_FAILED"
        message = (
            "The Quiz response could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "QUIZ_RESPONSE_FAILED"
        message = (
            "The Quiz response could not be completed."
        )

    error_body = QuizApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )


def _build_source_storage_error_response(
) -> JSONResponse:
    """Return a safe error for trusted source-storage failures."""

    error_body = QuizApiErrorResponse(
        error_code="QUIZ_SOURCE_STORAGE_FAILED",
        message=(
            "Study-material loading is temporarily unavailable."
        ),
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_body.model_dump(
            mode="json",
        ),
    )