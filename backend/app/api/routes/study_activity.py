# File: /backend/app/api/routes/study_activity.py
# Purpose: Provides authenticated actual Study Activity timer
# start, pause, resume, break, completion, and active-state APIs.

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
from app.api.study_activity_dependency import (
    get_study_activity_service,
)
from app.schemas.study_activity import (
    StudyActivityApiErrorResponse,
    StudyActivityBreakStartRequest,
    StudyActivityResponse,
    StudyActivityStartRequest,
    StudyActivityTransitionAction,
)
from app.services.study_activity_errors import (
    StudyActivityConflictError,
    StudyActivityError,
    StudyActivityNotFoundError,
    StudyActivityPersistenceError,
    StudyActivityResponseError,
    StudyActivityValidationError,
)
from app.services.study_activity_service import (
    StudyActivityService,
)

router = APIRouter(
    prefix="/study-activity",
    tags=[
        "study-activity",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": StudyActivityApiErrorResponse,
        "description": (
            "The Study Activity operation is invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": StudyActivityApiErrorResponse,
        "description": (
            "The requested Study Activity resource was not found."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": StudyActivityApiErrorResponse,
        "description": (
            "The timer state conflicts with the requested action."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": StudyActivityApiErrorResponse,
        "description": (
            "Study Activity storage is temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": StudyActivityApiErrorResponse,
        "description": (
            "The Study Activity response could not be completed."
        ),
    },
}


@router.get(
    "/active",
    response_model=StudyActivityResponse | None,
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
async def get_active_study_activity(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
) -> StudyActivityResponse | JSONResponse | None:
    """Return the student's unfinished timer when one exists."""

    try:
        return await run_in_threadpool(
            service.get_active_activity,
            user_id=authenticated_user.user_id,
        )

    except StudyActivityError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.post(
    "/start",
    response_model=StudyActivityResponse,
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
async def start_study_activity(
    payload: StudyActivityStartRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
) -> StudyActivityResponse | JSONResponse:
    """Start one focus timer."""

    try:
        return await run_in_threadpool(
            service.start_activity,
            user_id=authenticated_user.user_id,
            request=payload,
        )

    except StudyActivityError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.post(
    "/{activity_id}/pause",
    response_model=StudyActivityResponse,
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
async def pause_study_activity(
    activity_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
) -> StudyActivityResponse | JSONResponse:
    """Pause one running focus timer."""

    return await _transition_activity(
        service=service,
        user_id=authenticated_user.user_id,
        activity_id=activity_id,
        action=StudyActivityTransitionAction.PAUSE,
    )


@router.post(
    "/{activity_id}/resume",
    response_model=StudyActivityResponse,
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
async def resume_study_activity(
    activity_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
) -> StudyActivityResponse | JSONResponse:
    """Resume one paused timer in focus mode."""

    return await _transition_activity(
        service=service,
        user_id=authenticated_user.user_id,
        activity_id=activity_id,
        action=StudyActivityTransitionAction.RESUME,
    )


@router.post(
    "/{activity_id}/break/start",
    response_model=StudyActivityResponse,
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
async def start_study_activity_break(
    activity_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
    payload: StudyActivityBreakStartRequest | None = None,
) -> StudyActivityResponse | JSONResponse:
    """Finish focus and begin a persisted timed break."""

    break_request = (
        payload
        if payload is not None
        else StudyActivityBreakStartRequest()
    )

    try:
        return await run_in_threadpool(
            service.start_break,
            user_id=authenticated_user.user_id,
            activity_id=activity_id,
            request=break_request,
        )

    except StudyActivityError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.post(
    "/{activity_id}/break/end",
    response_model=StudyActivityResponse,
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
async def end_study_activity_break(
    activity_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
) -> StudyActivityResponse | JSONResponse:
    """Finish the break segment and resume focus."""

    return await _transition_activity(
        service=service,
        user_id=authenticated_user.user_id,
        activity_id=activity_id,
        action=StudyActivityTransitionAction.END_BREAK,
    )


@router.post(
    "/{activity_id}/end",
    response_model=StudyActivityResponse,
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
async def end_study_activity(
    activity_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyActivityService,
        Depends(
            get_study_activity_service,
        ),
    ],
) -> StudyActivityResponse | JSONResponse:
    """End one running or paused timer."""

    return await _transition_activity(
        service=service,
        user_id=authenticated_user.user_id,
        activity_id=activity_id,
        action=StudyActivityTransitionAction.COMPLETE,
    )


async def _transition_activity(
    *,
    service: StudyActivityService,
    user_id: UUID,
    activity_id: UUID,
    action: StudyActivityTransitionAction,
) -> StudyActivityResponse | JSONResponse:
    """Execute one controlled timer transition."""

    try:
        return await run_in_threadpool(
            service.transition_activity,
            user_id=user_id,
            activity_id=activity_id,
            action=action,
        )

    except StudyActivityError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: StudyActivityError,
) -> JSONResponse:
    """Convert controlled timer failures into safe public errors."""

    if isinstance(
        error,
        StudyActivityValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "STUDY_ACTIVITY_VALIDATION_FAILED"
        message = (
            "The Study Activity operation is invalid."
        )

    elif isinstance(
        error,
        StudyActivityNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "STUDY_ACTIVITY_NOT_FOUND"
        message = (
            "The requested Study Activity resource was not found."
        )

    elif isinstance(
        error,
        StudyActivityConflictError,
    ):
        status_code = status.HTTP_409_CONFLICT
        error_code = "STUDY_ACTIVITY_CONFLICT"
        message = (
            "The study timer is not in a valid state for that action."
        )

    elif isinstance(
        error,
        StudyActivityPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = "STUDY_ACTIVITY_PERSISTENCE_FAILED"
        message = (
            "Study Activity storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        StudyActivityResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "STUDY_ACTIVITY_RESPONSE_FAILED"
        message = (
            "The Study Activity response could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "STUDY_ACTIVITY_RESPONSE_FAILED"
        message = (
            "The Study Activity response could not be completed."
        )

    body = StudyActivityApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(
            mode="json",
        ),
    )