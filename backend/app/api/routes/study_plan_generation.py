# File: /backend/app/api/routes/study_plan_generation.py
# Purpose: Provides the isolated Track D API endpoint that
# generates and persists a student's study plan.

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
from app.api.study_plan_generation_dependency import (
    get_study_plan_generation_orchestrator,
    get_study_plan_regeneration_orchestrator,
)
from app.schemas.study_plan_api import (
    StudyPlanApiErrorResponse,
)
from app.schemas.study_plan_generation_api import (
    StudyPlanGenerationRequest,
    StudyPlanGenerationResponse,
    StudyPlanRegenerationRequest,
)
from app.services.study_plan_errors import (
    StudyPlanError,
    StudyPlanNotFoundError,
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
)
from app.services.study_plan_generation_orchestrator import (
    StudyPlanGenerationOrchestrator,
)
from app.services.study_plan_regeneration_orchestrator import (
    StudyPlanRegenerationOrchestrator,
)

router = APIRouter(
    prefix="/study-plan-generation",
    tags=[
        "study-plan-generation",
    ],
)


@router.post(
    "",
    response_model=StudyPlanGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": StudyPlanApiErrorResponse,
            "description": (
                "The requested study plan could not "
                "be generated."
            ),
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
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
                "Study-plan generation could not be completed."
            ),
        },
    },
)
async def generate_study_plan(
    payload: StudyPlanGenerationRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    orchestrator: Annotated[
        StudyPlanGenerationOrchestrator,
        Depends(
            get_study_plan_generation_orchestrator,
        ),
    ],
) -> StudyPlanGenerationResponse | JSONResponse:
    """Generate and persist one authenticated student's plan."""

    try:
        return await run_in_threadpool(
            orchestrator.generate_and_save,
            user_id=authenticated_user.user_id,
            title=payload.title,
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            tasks=payload.tasks,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.post(
    "/{study_plan_id}/regenerate",
    response_model=StudyPlanGenerationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": StudyPlanApiErrorResponse,
            "description": (
                "The study plan cannot be regenerated."
            ),
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudyPlanApiErrorResponse,
            "description": (
                "The requested study plan was not found."
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
                "Study-plan regeneration could not be completed."
            ),
        },
    },
)
async def regenerate_study_plan(
    study_plan_id: UUID,
    payload: StudyPlanRegenerationRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    orchestrator: Annotated[
        StudyPlanRegenerationOrchestrator,
        Depends(
            get_study_plan_regeneration_orchestrator,
        ),
    ],
) -> StudyPlanGenerationResponse | JSONResponse:
    """Regenerate one existing generated study plan."""

    try:
        return await run_in_threadpool(
            orchestrator.regenerate,
            user_id=authenticated_user.user_id,
            study_plan_id=study_plan_id,
            tasks=payload.tasks,
        )

    except StudyPlanError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: StudyPlanError,
) -> JSONResponse:
    """Convert controlled generation failures into safe errors."""

    if isinstance(
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
        StudyPlanValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "STUDY_PLAN_GENERATION_INVALID"
        message = (
            "The requested study plan could not "
            "be generated."
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
            "Study-plan generation could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "STUDY_PLAN_GENERATION_FAILED"
        message = (
            "Study-plan generation could not be completed."
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