# File: /backend/app/api/routes/flashcards.py
# Purpose: Provides authenticated Flashcard generation,
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
from app.api.flashcard_dependency import (
    get_flashcard_service,
)
from app.api.flashcard_orchestration_dependency import (
    get_flashcard_orchestration_service,
)
from app.schemas.flashcard import (
    FlashcardApiErrorResponse,
    FlashcardDeckResponse,
    FlashcardGenerateRequest,
)
from app.schemas.flashcard_summary import (
    FlashcardListResponse,
)
from app.services.flashcard_errors import (
    FlashcardError,
    FlashcardGenerationError,
    FlashcardGenerationResponseError,
    FlashcardOrchestrationError,
    FlashcardPersistenceError,
    FlashcardResponseError,
    FlashcardSourceNotFoundError,
    FlashcardSourceUnavailableError,
    FlashcardValidationError,
)
from app.services.flashcard_orchestration import (
    FlashcardOrchestrationService,
)
from app.services.flashcard_service import (
    FlashcardService,
)
from app.services.supabase_admin import (
    SupabaseAdminError,
)

router = APIRouter(
    prefix="/flashcards",
    tags=[
        "flashcards",
    ],
)


_ERROR_RESPONSE_MODELS = {
    status.HTTP_400_BAD_REQUEST: {
        "model": FlashcardApiErrorResponse,
        "description": (
            "The Flashcard request or filters are invalid."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": FlashcardApiErrorResponse,
        "description": (
            "The requested Flashcard deck or source "
            "material was not found."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": FlashcardApiErrorResponse,
        "description": (
            "The selected study material is not ready "
            "for Flashcard generation."
        ),
    },
    status.HTTP_502_BAD_GATEWAY: {
        "model": FlashcardApiErrorResponse,
        "description": (
            "The configured AI provider could not "
            "generate the Flashcards."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": FlashcardApiErrorResponse,
        "description": (
            "Flashcard storage or source loading is "
            "temporarily unavailable."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": FlashcardApiErrorResponse,
        "description": (
            "The Flashcard response could not be completed."
        ),
    },
}


@router.post(
    "/generate",
    response_model=FlashcardDeckResponse,
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
async def generate_flashcards(
    payload: FlashcardGenerateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        FlashcardOrchestrationService,
        Depends(
            get_flashcard_orchestration_service,
        ),
    ],
) -> FlashcardDeckResponse | JSONResponse:
    """Generate and save one Flashcard deck."""

    try:
        return await service.generate_deck(
            user_id=authenticated_user.user_id,
            request=payload,
        )

    except FlashcardError as exc:
        return _build_controlled_error_response(
            exc,
        )

    except SupabaseAdminError:
        return _build_source_storage_error_response()


@router.get(
    "",
    response_model=FlashcardListResponse,
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
async def list_flashcards(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        FlashcardService,
        Depends(
            get_flashcard_service,
        ),
    ],
    subject_id: Annotated[
        UUID | None,
        Query(),
    ] = None,
) -> FlashcardListResponse | JSONResponse:
    """List the authenticated student's saved decks."""

    try:
        items = await run_in_threadpool(
            service.list_decks,
            user_id=authenticated_user.user_id,
            subject_id=subject_id,
        )

        return FlashcardListResponse(
            items=items,
        )

    except FlashcardError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.get(
    "/{deck_id}",
    response_model=FlashcardDeckResponse,
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
async def get_flashcard_deck(
    deck_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        FlashcardService,
        Depends(
            get_flashcard_service,
        ),
    ],
) -> FlashcardDeckResponse | JSONResponse:
    """Return one saved Flashcard deck owned by the student."""

    try:
        deck = await run_in_threadpool(
            service.get_deck,
            user_id=authenticated_user.user_id,
            deck_id=deck_id,
        )

        if deck is None:
            return _build_not_found_response()

        return deck

    except FlashcardError as exc:
        return _build_controlled_error_response(
            exc,
        )


@router.delete(
    "/{deck_id}",
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
async def delete_flashcard_deck(
    deck_id: UUID,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        FlashcardService,
        Depends(
            get_flashcard_service,
        ),
    ],
) -> Response | JSONResponse:
    """Delete one saved Flashcard deck owned by the student."""

    try:
        deleted = await run_in_threadpool(
            service.delete_deck,
            user_id=authenticated_user.user_id,
            deck_id=deck_id,
        )

        if not deleted:
            return _build_not_found_response()

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except FlashcardError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    error: FlashcardError,
) -> JSONResponse:
    """Convert controlled Flashcard failures into safe errors."""

    if isinstance(
        error,
        FlashcardValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "FLASHCARD_VALIDATION_FAILED"
        message = "The Flashcard operation is invalid."

    elif isinstance(
        error,
        FlashcardSourceNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "FLASHCARD_NOT_FOUND"
        message = (
            "The requested Flashcard deck or study "
            "material was not found."
        )

    elif isinstance(
        error,
        FlashcardSourceUnavailableError,
    ):
        status_code = status.HTTP_409_CONFLICT
        error_code = "FLASHCARD_SOURCE_UNAVAILABLE"
        message = (
            "The selected study material is not ready "
            "for Flashcard generation."
        )

    elif isinstance(
        error,
        FlashcardPersistenceError,
    ):
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        error_code = "FLASHCARD_PERSISTENCE_FAILED"
        message = (
            "Flashcard storage is temporarily unavailable."
        )

    elif isinstance(
        error,
        FlashcardGenerationResponseError,
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = (
            "FLASHCARD_GENERATION_RESPONSE_FAILED"
        )
        message = (
            "The generated Flashcards could not "
            "be processed."
        )

    elif isinstance(
        error,
        FlashcardGenerationError,
    ):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_code = "FLASHCARD_GENERATION_FAILED"
        message = (
            "The Flashcards could not be generated."
        )

    elif isinstance(
        error,
        (
            FlashcardResponseError,
            FlashcardOrchestrationError,
        ),
    ):
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "FLASHCARD_RESPONSE_FAILED"
        message = (
            "The Flashcard response could not be completed."
        )

    else:
        status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        error_code = "FLASHCARD_RESPONSE_FAILED"
        message = (
            "The Flashcard response could not be completed."
        )

    error_body = FlashcardApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )


def _build_not_found_response() -> JSONResponse:
    """Return a safe response for a missing owned deck."""

    error_body = FlashcardApiErrorResponse(
        error_code="FLASHCARD_NOT_FOUND",
        message=(
            "The requested Flashcard deck was not found."
        ),
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_body.model_dump(
            mode="json",
        ),
    )


def _build_source_storage_error_response(
) -> JSONResponse:
    """Return a safe trusted source-storage error."""

    error_body = FlashcardApiErrorResponse(
        error_code="FLASHCARD_SOURCE_STORAGE_FAILED",
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