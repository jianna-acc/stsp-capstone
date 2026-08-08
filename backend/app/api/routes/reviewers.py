# File: /backend/app/api/routes/reviewers.py
# Purpose: Provides authenticated reviewer generation,
# listing, retrieval, and deletion endpoints.

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.reviewer_dependency import (
    get_reviewer_service,
)
from app.api.reviewer_orchestration_dependency import (
    get_reviewer_orchestration_service,
)
from app.schemas.reviewer import (
    ReviewerApiErrorResponse,
    ReviewerGenerateRequest,
    ReviewerListResponse,
    ReviewerResponse,
)
from app.services.reviewer_errors import (
    ReviewerError,
    ReviewerGenerationError,
    ReviewerGenerationResponseError,
    ReviewerNotFoundError,
    ReviewerPersistenceError,
    ReviewerResponseError,
    ReviewerSourceNotFoundError,
    ReviewerSourceUnavailableError,
    ReviewerValidationError,
)
from app.services.reviewer_orchestration import (
    ReviewerOrchestrationService,
)
from app.services.reviewer_service import (
    ReviewerService,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
)

router = APIRouter(
    prefix="/reviewers",
    tags=[
        "reviewers",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ReviewerApiErrorResponse,
        "description": (
            "The reviewer request or filters are invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ReviewerApiErrorResponse,
        "description": (
            "The requested reviewer or source material "
            "was not found."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ReviewerApiErrorResponse,
        "description": (
            "The selected study material is not ready "
            "for reviewer generation."
        ),
    },
    status.HTTP_502_BAD_GATEWAY: {
        "model": ReviewerApiErrorResponse,
        "description": (
            "The configured AI provider could not "
            "generate the reviewer."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ReviewerApiErrorResponse,
        "description": (
            "Reviewer storage or source loading is "
            "temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ReviewerApiErrorResponse,
        "description": (
            "The reviewer response could not be completed."
        ),
    },
}


@router.post(
    "/generate",
    response_model=ReviewerResponse,
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
async def generate_reviewer(
    payload: ReviewerGenerateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        ReviewerOrchestrationService,
        Depends(
            get_reviewer_orchestration_service,
        ),
    ],
) -> ReviewerResponse | JSONResponse:
    """Generate and save one reviewer from owned study material."""

    try:
        return await service.generate_reviewer(
            user_id=authenticated_user.user_id,
            request=payload,
        )

    except ReviewerError as exc:
        return _build_controlled_error_response(
            exc,
        )

    except SupabaseAdminError:
        return _build_source_storage_error_response()


@router.get(
    "",
    response_model=ReviewerListResponse,
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
async def list_reviewers(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        ReviewerService,
        Depends(
            get_reviewer_service,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
) -> ReviewerListResponse | JSONResponse:
    """List the authenticated student's saved reviewers."""

    try:
        return await run_in_threadpool(
            service.list_reviewers,
            user_id=authenticated_user.user_id,
            limit=limit,
        )

    except ReviewerError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{reviewer_id}",
    response_model=ReviewerResponse,
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
async def get_reviewer(
    reviewer_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        ReviewerService,
        Depends(
            get_reviewer_service,
        ),
    ],
) -> ReviewerResponse | JSONResponse:
    """Return one saved reviewer owned by the student."""

    try:
        return await run_in_threadpool(
            service.get_reviewer,
            user_id=authenticated_user.user_id,
            reviewer_id=reviewer_id,
        )

    except ReviewerError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{reviewer_id}",
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
async def delete_reviewer(
    reviewer_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        ReviewerService,
        Depends(
            get_reviewer_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one saved reviewer owned by the student."""

    try:
        await run_in_threadpool(
            service.delete_reviewer,
            user_id=authenticated_user.user_id,
            reviewer_id=reviewer_id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except ReviewerError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: ReviewerError,
) -> JSONResponse:
    """Convert controlled reviewer failures into safe API errors."""

    if isinstance(
        error,
        ReviewerValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "REVIEWER_VALIDATION_FAILED"
        message = "The reviewer operation is invalid."

    elif isinstance(
        error,
        (
            ReviewerNotFoundError,
            ReviewerSourceNotFoundError,
        ),
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "REVIEWER_NOT_FOUND"
        message = (
            "The requested reviewer or study material "
            "was not found."
        )

    elif isinstance(
        error,
        ReviewerSourceUnavailableError,
    ):
        status_code = status.HTTP_409_CONFLICT
        error_code = "REVIEWER_SOURCE_UNAVAILABLE"
        message = (
            "The selected study material is not ready "
            "for reviewer generation."
        )

    elif isinstance(
        error,
        ReviewerPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = "REVIEWER_PERSISTENCE_FAILED"
        message = (
            "Reviewer storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        ReviewerGenerationResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "REVIEWER_GENERATION_RESPONSE_FAILED"
        message = (
            "The generated reviewer could not be processed."
        )

    elif isinstance(
        error,
        ReviewerGenerationError,
    ):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_code = "REVIEWER_GENERATION_FAILED"
        message = (
            "The reviewer could not be generated."
        )

    elif isinstance(
        error,
        ReviewerResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "REVIEWER_RESPONSE_FAILED"
        message = (
            "The reviewer response could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "REVIEWER_RESPONSE_FAILED"
        message = (
            "The reviewer response could not be completed."
        )

    error_body = ReviewerApiErrorResponse(
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

    error_body = ReviewerApiErrorResponse(
        error_code="REVIEWER_SOURCE_STORAGE_FAILED",
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