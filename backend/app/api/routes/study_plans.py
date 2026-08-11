# File: /backend/app/api/routes/study_plans.py
# Purpose: Provides authenticated CRUD endpoints for Track D
# study plans and manually scheduled study sessions.

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
from app.api.study_plan_dependency import (
    get_study_plan_service,
)
from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanListResponse,
    StudyPlanResponse,
    StudySessionCreateRequest,
    StudySessionListResponse,
    StudySessionResponse,
)
from app.schemas.study_plan_api import (
    StudyPlanApiErrorResponse,
)
from app.services.study_plan_errors import (
    StudyPlanError,
    StudyPlanNotFoundError,
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
    StudySessionNotFoundError,
)
from app.services.study_plan_service import (
    StudyPlanService,
)

router = APIRouter(
    prefix="/study-plans",
    tags=[
        "study-plans",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": StudyPlanApiErrorResponse,
        "description": (
            "The study-plan operation is invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": StudyPlanApiErrorResponse,
        "description": (
            "The requested study plan or session "
            "was not found."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": StudyPlanApiErrorResponse,
        "description": (
            "Study-plan storage is temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": StudyPlanApiErrorResponse,
        "description": (
            "The study-plan response could not be completed."
        ),
    },
}


@router.post(
    "",
    response_model=StudyPlanResponse,
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
async def create_study_plan(
    payload: StudyPlanCreateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
) -> StudyPlanResponse | JSONResponse:
    """Create one manual study plan for the student."""

    try:
        return await run_in_threadpool(
            service.create_study_plan,
            user_id=authenticated_user.user_id,
            request=payload,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "",
    response_model=StudyPlanListResponse,
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
async def list_study_plans(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 50,
) -> StudyPlanListResponse | JSONResponse:
    """List study plans belonging to the student."""

    try:
        return await run_in_threadpool(
            service.list_study_plans,
            user_id=authenticated_user.user_id,
            limit=limit,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{study_plan_id}",
    response_model=StudyPlanResponse,
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
async def get_study_plan(
    study_plan_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
) -> StudyPlanResponse | JSONResponse:
    """Return one study plan belonging to the student."""

    try:
        return await run_in_threadpool(
            service.get_study_plan,
            user_id=authenticated_user.user_id,
            study_plan_id=study_plan_id,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{study_plan_id}",
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
async def delete_study_plan(
    study_plan_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one owned study plan and its sessions."""

    try:
        await run_in_threadpool(
            service.delete_study_plan,
            user_id=authenticated_user.user_id,
            study_plan_id=study_plan_id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.post(
    "/{study_plan_id}/sessions",
    response_model=StudySessionResponse,
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
async def create_study_session(
    study_plan_id: UUID,
    payload: StudySessionCreateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
) -> StudySessionResponse | JSONResponse:
    """Add one manually scheduled session to an owned plan."""

    try:
        return await run_in_threadpool(
            service.create_study_session,
            user_id=authenticated_user.user_id,
            study_plan_id=study_plan_id,
            request=payload,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{study_plan_id}/sessions",
    response_model=StudySessionListResponse,
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
async def list_study_sessions(
    study_plan_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=200,
        ),
    ] = 200,
) -> StudySessionListResponse | JSONResponse:
    """List scheduled sessions from one owned study plan."""

    try:
        return await run_in_threadpool(
            service.list_study_sessions,
            user_id=authenticated_user.user_id,
            study_plan_id=study_plan_id,
            limit=limit,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{study_plan_id}/sessions/{study_session_id}",
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
async def delete_study_session(
    study_plan_id: UUID,
    study_session_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyPlanService,
        Depends(
            get_study_plan_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one session from an owned study plan."""

    try:
        await run_in_threadpool(
            service.delete_study_session,
            user_id=authenticated_user.user_id,
            study_plan_id=study_plan_id,
            study_session_id=study_session_id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: StudyPlanError,
) -> JSONResponse:
    """Convert controlled Track D failures into safe API errors."""

    if isinstance(
        error,
        StudyPlanValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "STUDY_PLAN_VALIDATION_FAILED"
        message = (
            "The study-plan operation is invalid."
        )

    elif isinstance(
        error,
        StudyPlanNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "STUDY_PLAN_NOT_FOUND"
        message = (
            "The requested study plan was not found."
        )

    elif isinstance(
        error,
        StudySessionNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "STUDY_SESSION_NOT_FOUND"
        message = (
            "The requested study session was not found."
        )

    elif isinstance(
        error,
        StudyPlanPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = "STUDY_PLAN_PERSISTENCE_FAILED"
        message = (
            "Study-plan storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        StudyPlanResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "STUDY_PLAN_RESPONSE_FAILED"
        message = (
            "The study-plan response could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "STUDY_PLAN_RESPONSE_FAILED"
        message = (
            "The study-plan response could not be completed."
        )

    error_body = StudyPlanApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )