# File: /backend/app/api/routes/academic_tasks.py
# Purpose: Exposes authenticated academic-task CRUD, status,
# and deterministic priority endpoints for student-owned tasks.

from datetime import (
    UTC,
    datetime,
)
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

from app.api.academic_task_dependency import (
    get_academic_task_service,
)
from app.api.academic_task_priority_dependency import (
    get_academic_task_priority_service,
)
from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.schemas.academic_task import (
    AcademicTaskApiErrorResponse,
    AcademicTaskCreateRequest,
    AcademicTaskListResponse,
    AcademicTaskResponse,
    AcademicTaskStatusUpdateRequest,
    AcademicTaskUpdateRequest,
)
from app.schemas.academic_task_priority import (
    AcademicTaskPriorityBreakdownResponse,
    AcademicTaskPriorityListResponse,
    AcademicTaskPriorityResponse,
)
from app.services.academic_task_errors import (
    AcademicTaskError,
    AcademicTaskNotFoundError,
    AcademicTaskPersistenceError,
    AcademicTaskResponseError,
    AcademicTaskValidationError,
)
from app.services.academic_task_priority_service import (
    AcademicTaskPriorityEvaluation,
    AcademicTaskPriorityService,
)
from app.services.academic_task_service import (
    AcademicTaskService,
)

router = APIRouter(
    prefix="/academic-tasks",
    tags=[
        "Academic Tasks",
    ],
)


def _to_priority_response(
    evaluation: AcademicTaskPriorityEvaluation,
) -> AcademicTaskPriorityResponse:
    """Convert one deterministic evaluation into an API response."""

    task = evaluation.task
    priority = evaluation.priority

    return AcademicTaskPriorityResponse(
        task=task,
        priority=(
            AcademicTaskPriorityBreakdownResponse(
                total_score=priority.total_score,
                deadline_score=priority.deadline_score,
                difficulty_score=priority.difficulty_score,
                estimated_time_score=(
                    priority.estimated_time_score
                ),
                output_confidence_score=(
                    priority.output_confidence_score
                ),
                previous_performance_score=(
                    priority.previous_performance_score
                ),
                available_study_time_score=(
                    priority.available_study_time_score
                ),
                status_score=priority.status_score,
            )
        ),
    )


@router.post(
    "",
    response_model=AcademicTaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def create_academic_task(
    payload: AcademicTaskCreateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
) -> AcademicTaskResponse | JSONResponse:
    """Create an academic task for the authenticated student."""

    try:
        return service.create_task(
            user_id=authenticated_user.user_id,
            request=payload,
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/prioritized",
    response_model=AcademicTaskPriorityListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def list_prioritized_academic_tasks(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
    priority_service: Annotated[
        AcademicTaskPriorityService,
        Depends(
            get_academic_task_priority_service,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 100,
) -> AcademicTaskPriorityListResponse | JSONResponse:
    """Return owned academic tasks ranked by priority."""

    try:
        tasks = service.list_tasks(
            user_id=authenticated_user.user_id,
            limit=limit,
        )

        evaluations = (
            priority_service.score_tasks(
                user_id=authenticated_user.user_id,
                tasks=tasks,
                now=datetime.now(
                    UTC,
                ),
            )
        )

        ranked = sorted(
            evaluations,
            key=lambda evaluation: (
                -evaluation.priority.total_score,
                evaluation.task.deadline,
                evaluation.task.created_at,
                str(
                    evaluation.task.id,
                ),
            ),
        )

        return AcademicTaskPriorityListResponse(
            items=tuple(
                _to_priority_response(
                    evaluation,
                )
                for evaluation in ranked
            ),
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "",
    response_model=AcademicTaskListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def list_academic_tasks(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 100,
) -> AcademicTaskListResponse | JSONResponse:
    """Return academic tasks owned by the authenticated student."""

    try:
        tasks = service.list_tasks(
            user_id=authenticated_user.user_id,
            limit=limit,
        )

        return AcademicTaskListResponse(
            items=tuple(
                tasks,
            ),
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{task_id}",
    response_model=AcademicTaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def get_academic_task(
    task_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
) -> AcademicTaskResponse | JSONResponse:
    """Return one academic task owned by the student."""

    try:
        return service.get_task(
            user_id=authenticated_user.user_id,
            task_id=task_id,
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.patch(
    "/{task_id}",
    response_model=AcademicTaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def update_academic_task(
    task_id: UUID,
    payload: AcademicTaskUpdateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
) -> AcademicTaskResponse | JSONResponse:
    """Update one academic task owned by the student."""

    try:
        return service.update_task(
            user_id=authenticated_user.user_id,
            task_id=task_id,
            request=payload,
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.patch(
    "/{task_id}/status",
    response_model=AcademicTaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def change_academic_task_status(
    task_id: UUID,
    payload: AcademicTaskStatusUpdateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
) -> AcademicTaskResponse | JSONResponse:
    """Change only the workflow status of one academic task."""

    try:
        return service.change_task_status(
            user_id=authenticated_user.user_id,
            task_id=task_id,
            status=payload.status,
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{task_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AcademicTaskApiErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AcademicTaskApiErrorResponse,
        },
    },
)
async def delete_academic_task(
    task_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AcademicTaskService,
        Depends(
            get_academic_task_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one academic task owned by the student."""

    try:
        service.delete_task(
            user_id=authenticated_user.user_id,
            task_id=task_id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except AcademicTaskError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: AcademicTaskError,
) -> JSONResponse:
    """Convert academic-task domain errors into safe responses."""

    if isinstance(
        error,
        AcademicTaskNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "ACADEMIC_TASK_NOT_FOUND"
        message = "The requested academic task was not found."

    elif isinstance(
        error,
        AcademicTaskValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "ACADEMIC_TASK_VALIDATION_FAILED"
        message = "The academic-task request was invalid."

    elif isinstance(
        error,
        AcademicTaskPersistenceError,
    ):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_code = "ACADEMIC_TASK_PERSISTENCE_FAILED"
        message = (
            "Academic-task storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        AcademicTaskResponseError,
    ):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "ACADEMIC_TASK_RESPONSE_FAILED"
        message = (
            "Stored academic-task data could not be processed."
        )

    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "ACADEMIC_TASK_FAILED"
        message = "The academic-task operation failed."

    response = AcademicTaskApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(
            mode="json",
        ),
    )