# File: /backend/app/api/routes/rag.py

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.api.study_conversation_rag_dependency import (
    get_study_conversation_rag_service,
)
from app.schemas.rag import (
    RagAnswerOutcome,
    RagAnswerRequest,
    RagAnswerResponse,
    RagApiErrorResponse,
    RagSourceResponse,
)
from app.services.rag_orchestration import (
    RagOrchestrationError,
    RagOrchestrationFailureCode,
    RagOrchestrationRequest,
)
from app.services.study_conversation_errors import (
    StudyConversationError,
    StudyConversationNotFoundError,
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
)
from app.services.study_conversation_rag import (
    StudyConversationRagResult,
    StudyConversationRagService,
)

router = APIRouter(
    prefix="/rag",
    tags=[
        "rag",
    ],
)


_ERROR_RESPONSES: dict[
    RagOrchestrationFailureCode,
    tuple[
        int,
        str,
    ],
] = {
    RagOrchestrationFailureCode.VALIDATION_FAILED: (
        status.HTTP_400_BAD_REQUEST,
        "The grounded-answer request is invalid.",
    ),
    RagOrchestrationFailureCode.RETRIEVAL_FAILED: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Study-material retrieval is temporarily unavailable.",
    ),
    RagOrchestrationFailureCode.GENERATION_FAILED: (
        status.HTTP_502_BAD_GATEWAY,
        "The grounded answer could not be generated.",
    ),
    RagOrchestrationFailureCode.RESPONSE_FAILED: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "The grounded-answer response could not be completed.",
    ),
}


@router.post(
    "/answer",
    response_model=RagAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": RagApiErrorResponse,
            "description": "Invalid combined RAG request.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student "
                "authentication."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": RagApiErrorResponse,
            "description": (
                "The requested saved conversation "
                "was not found."
            ),
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": RagApiErrorResponse,
            "description": (
                "The configured generation provider failed."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": RagApiErrorResponse,
            "description": (
                "Study-material retrieval is unavailable."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": RagApiErrorResponse,
            "description": (
                "The generated response was inconsistent."
            ),
        },
    },
)
async def answer_study_question(
    payload: RagAnswerRequest,
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    conversation_rag_service: Annotated[
        StudyConversationRagService,
        Depends(
            get_study_conversation_rag_service,
        ),
    ],
) -> RagAnswerResponse | JSONResponse:
    """Answer a student's question using eligible study materials."""

    try:
        orchestration_request = RagOrchestrationRequest(
            user_id=authenticated_user.user_id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            study_file_id=payload.study_file_id,
            subject_id=payload.subject_id,
            match_count=payload.match_count,
            similarity_threshold=(
                payload.similarity_threshold
            ),
        )

        result = await conversation_rag_service.answer(
            orchestration_request,
        )

        return _build_answer_response(
            result,
        )
    except StudyConversationError as exc:
        return _build_conversation_error_response(
            exc,
        )
    except RagOrchestrationError as exc:
        return _build_controlled_error_response(
            exc,
        )
    except ValidationError:
        return _build_internal_response_error()


def _build_answer_response(
    result: StudyConversationRagResult,
) -> RagAnswerResponse:
    """Convert the persisted RAG result into a safe response."""

    rag_result = result.rag_result

    sources = tuple(
        RagSourceResponse(
            source_number=source.source_number,
            source_name=source.source_name,
            chunk_index=source.chunk_index,
            similarity_score=source.similarity_score,
        )
        for source in rag_result.sources
    )

    return RagAnswerResponse(
        conversation_id=result.conversation.id,
        outcome=RagAnswerOutcome(
            rag_result.outcome.value,
        ),
        answer=rag_result.answer,
        sources=sources,
        retrieved_count=rag_result.retrieved_count,
        source_count=rag_result.source_count,
        context_available=rag_result.context_available,
    )


def _build_conversation_error_response(
    error: StudyConversationError,
) -> JSONResponse:
    """Convert a conversation failure into a safe RAG error."""

    if isinstance(
        error,
        StudyConversationValidationError,
    ):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = (
            "STUDY_CONVERSATION_VALIDATION_FAILED"
        )
        message = (
            "The saved-conversation request is invalid."
        )
    elif isinstance(
        error,
        StudyConversationNotFoundError,
    ):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "STUDY_CONVERSATION_NOT_FOUND"
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

    error_body = RagApiErrorResponse(
        error_code=error_code,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )


def _build_controlled_error_response(
    error: RagOrchestrationError,
) -> JSONResponse:
    """Convert a controlled service failure into a safe response."""

    status_code, message = _ERROR_RESPONSES[
        error.error_code
    ]

    error_body = RagApiErrorResponse(
        error_code=error.error_code.value,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )


def _build_internal_response_error() -> JSONResponse:
    """Return a safe response for internal schema inconsistency."""

    error_code = (
        RagOrchestrationFailureCode.RESPONSE_FAILED
    )

    status_code, message = _ERROR_RESPONSES[
        error_code
    ]

    error_body = RagApiErrorResponse(
        error_code=error_code.value,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_body.model_dump(
            mode="json",
        ),
    )
