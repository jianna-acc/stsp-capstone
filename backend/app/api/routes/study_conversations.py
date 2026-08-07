# File: /backend/app/api/routes/study_conversations.py
# Purpose: Provides authenticated CRUD endpoints for saved Study
# Assistant conversations and messages.

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
from app.api.study_conversation_dependency import (
    get_study_conversation_service,
)
from app.schemas.study_conversation import (
    StudyConversationApiErrorResponse,
    StudyConversationCreateRequest,
    StudyConversationDetailResponse,
    StudyConversationListResponse,
    StudyConversationResponse,
    StudyConversationUpdateRequest,
)
from app.services.study_conversation_errors import (
    StudyConversationError,
    StudyConversationNotFoundError,
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
)
from app.services.study_conversation_service import (
    StudyConversationService,
)

router = APIRouter(
    prefix="/study-conversations",
    tags=[
        "study-conversations",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": StudyConversationApiErrorResponse,
        "description": (
            "The conversation operation or filters are invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": StudyConversationApiErrorResponse,
        "description": (
            "The authenticated user does not own the conversation "
            "or it does not exist."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": StudyConversationApiErrorResponse,
        "description": (
            "Conversation persistence is temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": StudyConversationApiErrorResponse,
        "description": (
            "Persisted conversation data could not be processed."
        ),
    },
}


@router.post(
    "",
    response_model=StudyConversationResponse,
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
async def create_study_conversation(
    payload: StudyConversationCreateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyConversationService,
        Depends(
            get_study_conversation_service,
        ),
    ],
) -> StudyConversationResponse | JSONResponse:
    """Create one conversation owned by the authenticated user."""

    try:
        return await run_in_threadpool(
            service.create_conversation,
            user_id=authenticated_user.user_id,
            request=payload,
        )
    except StudyConversationError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "",
    response_model=StudyConversationListResponse,
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
async def list_study_conversations(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyConversationService,
        Depends(
            get_study_conversation_service,
        ),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
        ),
    ] = 20,
) -> StudyConversationListResponse | JSONResponse:
    """List the authenticated user's recent conversations."""

    try:
        return await run_in_threadpool(
            service.list_conversations,
            user_id=authenticated_user.user_id,
            limit=limit,
        )
    except StudyConversationError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{conversation_id}",
    response_model=StudyConversationDetailResponse,
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
async def get_study_conversation(
    conversation_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyConversationService,
        Depends(
            get_study_conversation_service,
        ),
    ],
    message_limit: Annotated[
        int,
        Query(
            ge=1,
            le=500,
        ),
    ] = 200,
) -> StudyConversationDetailResponse | JSONResponse:
    """Load one owned conversation and its saved messages."""

    try:
        return await run_in_threadpool(
            service.get_conversation_detail,
            user_id=authenticated_user.user_id,
            conversation_id=conversation_id,
            message_limit=message_limit,
        )
    except StudyConversationError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.patch(
    "/{conversation_id}",
    response_model=StudyConversationResponse,
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
async def update_study_conversation(
    conversation_id: UUID,
    payload: StudyConversationUpdateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyConversationService,
        Depends(
            get_study_conversation_service,
        ),
    ],
) -> StudyConversationResponse | JSONResponse:
    """Update one conversation owned by the authenticated user."""

    try:
        return await run_in_threadpool(
            service.update_conversation,
            user_id=authenticated_user.user_id,
            conversation_id=conversation_id,
            request=payload,
        )
    except StudyConversationError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{conversation_id}",
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
async def delete_study_conversation(
    conversation_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        StudyConversationService,
        Depends(
            get_study_conversation_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one conversation owned by the authenticated user."""

    try:
        await run_in_threadpool(
            service.delete_conversation,
            user_id=authenticated_user.user_id,
            conversation_id=conversation_id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )
    except StudyConversationError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: StudyConversationError,
) -> JSONResponse:
    """Convert a controlled domain failure into a safe response."""

    if isinstance(
        error,
        StudyConversationValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = (
            "STUDY_CONVERSATION_VALIDATION_FAILED"
        )
        message = (
            "The conversation operation is invalid."
        )
    elif isinstance(
        error,
        StudyConversationNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = (
            "STUDY_CONVERSATION_NOT_FOUND"
        )
        message = (
            "The requested conversation was not found."
        )
    elif isinstance(
        error,
        StudyConversationPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = (
            "STUDY_CONVERSATION_PERSISTENCE_FAILED"
        )
        message = (
            "Conversation storage is temporarily unavailable."
        )
    elif isinstance(
        error,
        StudyConversationResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = (
            "STUDY_CONVERSATION_RESPONSE_FAILED"
        )
        message = (
            "The conversation response could not be completed."
        )
    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = (
            "STUDY_CONVERSATION_RESPONSE_FAILED"
        )
        message = (
            "The conversation response could not be completed."
        )

    error_body = StudyConversationApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )