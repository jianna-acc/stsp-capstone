# File: /backend/app/api/routes/flashcard_reviews.py
# Purpose: Records authenticated Flashcard self-assessment review events.

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from starlette.concurrency import (
    run_in_threadpool,
)

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.flashcard_review_dependency import (
    get_flashcard_review_service,
)
from app.schemas.flashcard_review import (
    FlashcardReviewCreateRequest,
    FlashcardReviewResponse,
)
from app.services.flashcard_review_errors import (
    FlashcardReviewError,
    FlashcardReviewNotFoundError,
    FlashcardReviewPersistenceError,
    FlashcardReviewResponseError,
    FlashcardReviewValidationError,
)
from app.services.flashcard_review_service import (
    FlashcardReviewService,
)

router = APIRouter(
    prefix="/flashcards",
    tags=[
        "flashcards",
    ],
)


@router.post(
    "/{deck_id}/reviews",
    response_model=FlashcardReviewResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": (
                "The Flashcard review request is invalid."
            ),
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The Flashcard review target was not found."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "Flashcard review storage is temporarily unavailable."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": (
                "The Flashcard review response could not be completed."
            ),
        },
    },
)
async def record_flashcard_review(
    deck_id: UUID,
    payload: FlashcardReviewCreateRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        FlashcardReviewService,
        Depends(
            get_flashcard_review_service,
        ),
    ],
) -> FlashcardReviewResponse | JSONResponse:
    """Persist one authenticated Flashcard self-assessment."""

    try:
        return await run_in_threadpool(
            service.record_review,
            user_id=authenticated_user.user_id,
            deck_id=deck_id,
            card_position=payload.card_position,
            outcome=payload.outcome,
        )

    except FlashcardReviewError as exc:
        return _build_controlled_error_response(
            exc,
        )


def _build_controlled_error_response(
    exc: FlashcardReviewError,
) -> JSONResponse:
    """Map controlled Flashcard review errors to safe HTTP responses."""

    if isinstance(
        exc,
        FlashcardReviewValidationError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error_code": "FLASHCARD_REVIEW_INVALID",
                "message": "The Flashcard review request is invalid.",
            },
        )

    if isinstance(
        exc,
        FlashcardReviewNotFoundError,
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_code": "FLASHCARD_REVIEW_NOT_FOUND",
                "message": "The Flashcard review target was not found.",
            },
        )

    if isinstance(
        exc,
        FlashcardReviewPersistenceError,
    ):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error_code": "FLASHCARD_REVIEW_STORAGE_UNAVAILABLE",
                "message": (
                    "Flashcard review storage is temporarily unavailable."
                ),
            },
        )

    if isinstance(
        exc,
        FlashcardReviewResponseError,
    ):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "FLASHCARD_REVIEW_RESPONSE_INVALID",
                "message": (
                    "The Flashcard review response could not be completed."
                ),
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "FLASHCARD_REVIEW_FAILED",
            "message": "The Flashcard review could not be completed.",
        },
    )