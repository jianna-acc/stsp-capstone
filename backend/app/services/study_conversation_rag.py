# File: /backend/app/services/study_conversation_rag.py
# Purpose: Coordinates saved conversations, bounded summary
# memory, message persistence, and grounded answer generation.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from starlette.concurrency import run_in_threadpool

from app.ai.grounded_answer_contracts import (
    MAX_CONVERSATION_MEMORY_MESSAGES,
    ConversationMemoryMessage,
)
from app.schemas.study_conversation import (
    StudyConversationResponse,
    StudyConversationSummaryState,
    StudyConversationSummaryUpdate,
    StudyMessageOutcome,
    StudyMessageResponse,
    StudyMessageSourceResponse,
)
from app.services.rag_orchestration import (
    RagOrchestrationRequest,
    RagOrchestrationResult,
)
from app.services.study_conversation_errors import (
    StudyConversationNotFoundError,
    StudyConversationValidationError,
)
from app.services.study_conversation_memory import (
    build_conversation_memory,
)
from app.services.study_conversation_summary import (
    CONVERSATION_SUMMARY_VERSION,
    build_conversation_summary_update,
)

MAX_CONVERSATION_TITLE_CHARACTERS = 120

SUMMARY_REFRESH_WINDOW_LIMIT = 501

RECENT_MESSAGES_WITH_SUMMARY = (
    MAX_CONVERSATION_MEMORY_MESSAGES
    - 1
)


class _ConversationRepositoryProtocol(
    Protocol,
):
    def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str,
        subject_id: UUID | None,
        study_file_id: UUID | None,
    ) -> StudyConversationResponse: ...

    def get_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationResponse | None: ...

    def get_summary_state(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationSummaryState | None: ...

    def list_messages_from_offset(
        self,
        *,
        conversation_id: UUID,
        offset: int,
        limit: int = SUMMARY_REFRESH_WINDOW_LIMIT,
    ) -> list[
        StudyMessageResponse
    ]: ...

    def save_summary_state(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        update: StudyConversationSummaryUpdate,
    ) -> StudyConversationSummaryState | None: ...

    def list_recent_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = MAX_CONVERSATION_MEMORY_MESSAGES,
    ) -> list[
        StudyMessageResponse
    ]: ...

    def save_user_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
    ) -> StudyMessageResponse: ...

    def save_assistant_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
        outcome: StudyMessageOutcome,
        sources: tuple[
            StudyMessageSourceResponse,
            ...,
        ],
    ) -> StudyMessageResponse: ...


class _RagServiceProtocol(
    Protocol,
):
    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> RagOrchestrationResult: ...


@dataclass(
    frozen=True,
    slots=True,
)
class StudyConversationRagResult:
    """Persisted conversation and answer result."""

    conversation: StudyConversationResponse

    user_message: StudyMessageResponse
    assistant_message: StudyMessageResponse

    rag_result: RagOrchestrationResult

    def __post_init__(
        self,
    ) -> None:
        conversation_id = self.conversation.id

        if (
            self.user_message.conversation_id
            != conversation_id
        ):
            raise ValueError(
                "The saved user message does not match "
                "the resolved conversation.",
            )

        if (
            self.assistant_message.conversation_id
            != conversation_id
        ):
            raise ValueError(
                "The saved assistant message does not match "
                "the resolved conversation.",
            )

        if (
            self.rag_result.request.conversation_id
            != conversation_id
        ):
            raise ValueError(
                "The RAG result does not match "
                "the resolved conversation.",
            )


class StudyConversationRagService:
    """Run one conversation-aware grounded-answer operation."""

    def __init__(
        self,
        *,
        repository: _ConversationRepositoryProtocol,
        rag_service: _RagServiceProtocol,
    ) -> None:
        self._repository = repository
        self._rag_service = rag_service

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> StudyConversationRagResult:
        """Resolve the conversation, save the pair, and answer."""

        if not isinstance(
            request,
            RagOrchestrationRequest,
        ):
            raise StudyConversationValidationError(
                "The conversation-aware RAG request is invalid.",
            )

        conversation = await self._resolve_conversation(
            request,
        )

        memory = await self._load_memory(
            request=request,
            conversation=conversation,
        )

        resolved_request = self._build_resolved_request(
            request=request,
            conversation=conversation,
            memory=memory,
        )

        user_message = await run_in_threadpool(
            self._repository.save_user_message,
            conversation_id=conversation.id,
            content=resolved_request.question,
        )

        rag_result = await self._rag_service.answer(
            resolved_request,
        )

        message_outcome = self._map_outcome(
            rag_result,
        )

        message_sources = tuple(
            StudyMessageSourceResponse(
                source_number=source.source_number,
                source_name=source.source_name,
                chunk_index=source.chunk_index,
                similarity_score=source.similarity_score,
            )
            for source in rag_result.sources
        )

        assistant_message = await run_in_threadpool(
            self._repository.save_assistant_message,
            conversation_id=conversation.id,
            content=rag_result.answer,
            outcome=message_outcome,
            sources=message_sources,
        )

        return StudyConversationRagResult(
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
            rag_result=rag_result,
        )

    async def _load_memory(
        self,
        *,
        request: RagOrchestrationRequest,
        conversation: StudyConversationResponse,
    ) -> tuple[
        ConversationMemoryMessage,
        ...,
    ]:
        """Refresh and load memory before saving the new question."""

        if request.conversation_id is None:
            return ()

        summary_state = await run_in_threadpool(
            self._repository.get_summary_state,
            user_id=request.user_id,
            conversation_id=conversation.id,
        )

        if summary_state is None:
            raise StudyConversationNotFoundError(
                "The requested conversation was not found.",
            )

        if (
            summary_state.conversation_id
            != conversation.id
        ):
            raise StudyConversationValidationError(
                "The conversation summary does not match "
                "the resolved conversation.",
            )

        if (
            summary_state.summary_version
            != CONVERSATION_SUMMARY_VERSION
        ):
            raise StudyConversationValidationError(
                "The stored conversation summary version "
                "is not supported.",
            )

        message_window = await run_in_threadpool(
            self._repository.list_messages_from_offset,
            conversation_id=conversation.id,
            offset=(
                summary_state.summarized_message_count
            ),
            limit=SUMMARY_REFRESH_WINDOW_LIMIT,
        )

        summary_state = await self._refresh_summary(
            user_id=request.user_id,
            conversation_id=conversation.id,
            summary_state=summary_state,
            message_window=message_window,
        )

        recent_limit = (
            RECENT_MESSAGES_WITH_SUMMARY
            if summary_state.summary_text is not None
            else MAX_CONVERSATION_MEMORY_MESSAGES
        )

        recent_messages = await run_in_threadpool(
            self._repository.list_recent_messages,
            conversation_id=conversation.id,
            limit=recent_limit,
        )

        return build_conversation_memory(
            recent_messages,
            summary_text=summary_state.summary_text,
        )

    async def _refresh_summary(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        summary_state: StudyConversationSummaryState,
        message_window: list[
            StudyMessageResponse
        ],
    ) -> StudyConversationSummaryState:
        """Summarize older unsummarized messages when required."""

        summary_messages = _select_summary_messages(
            summary_state=summary_state,
            message_window=message_window,
        )

        if not summary_messages:
            return summary_state

        summary_update = (
            build_conversation_summary_update(
                state=summary_state,
                messages=summary_messages,
            )
        )

        if summary_update is None:
            raise StudyConversationValidationError(
                "The conversation summary refresh "
                "produced no update.",
            )

        saved_state = await run_in_threadpool(
            self._repository.save_summary_state,
            user_id=user_id,
            conversation_id=conversation_id,
            update=summary_update,
        )

        if saved_state is None:
            raise StudyConversationNotFoundError(
                "The requested conversation was not found.",
            )

        return saved_state

    async def _resolve_conversation(
        self,
        request: RagOrchestrationRequest,
    ) -> StudyConversationResponse:
        if request.conversation_id is not None:
            conversation = await run_in_threadpool(
                self._repository.get_conversation,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
            )

            if conversation is None:
                raise StudyConversationNotFoundError(
                    "The requested conversation was not found.",
                )

            return conversation

        return await run_in_threadpool(
            self._repository.create_conversation,
            user_id=request.user_id,
            title=_build_conversation_title(
                request.question,
            ),
            subject_id=request.subject_id,
            study_file_id=request.study_file_id,
        )

    @staticmethod
    def _build_resolved_request(
        *,
        request: RagOrchestrationRequest,
        conversation: StudyConversationResponse,
        memory: tuple[
            ConversationMemoryMessage,
            ...,
        ],
    ) -> RagOrchestrationRequest:
        subject_id = _resolve_filter(
            request_value=request.subject_id,
            conversation_value=conversation.subject_id,
            field_name="subject_id",
        )

        study_file_id = _resolve_filter(
            request_value=request.study_file_id,
            conversation_value=conversation.study_file_id,
            field_name="study_file_id",
        )

        return RagOrchestrationRequest(
            user_id=request.user_id,
            question=request.question,
            memory=memory,
            conversation_id=conversation.id,
            subject_id=subject_id,
            study_file_id=study_file_id,
            match_count=request.match_count,
            similarity_threshold=(
                request.similarity_threshold
            ),
        )

    @staticmethod
    def _map_outcome(
        result: RagOrchestrationResult,
    ) -> StudyMessageOutcome:
        if result.outcome.value == "answered":
            return "answered"

        if result.outcome.value == "no_context":
            return "no_context"

        raise StudyConversationValidationError(
            "The RAG result contains an unsupported outcome.",
        )


def _select_summary_messages(
    *,
    summary_state: StudyConversationSummaryState,
    message_window: list[
        StudyMessageResponse
    ],
) -> tuple[
    StudyMessageResponse,
    ...,
]:
    """Select only messages older than the newest memory window."""

    if summary_state.summary_text is None:
        if (
            len(
                message_window,
            )
            <= MAX_CONVERSATION_MEMORY_MESSAGES
        ):
            return ()
    elif (
        len(
            message_window,
        )
        <= RECENT_MESSAGES_WITH_SUMMARY
    ):
        return ()

    return tuple(
        message_window[
            :-RECENT_MESSAGES_WITH_SUMMARY
        ]
    )


def _build_conversation_title(
    question: str,
) -> str:
    """Create a compact title from the first question."""

    normalized_question = " ".join(
        question.split(),
    )

    if not normalized_question:
        return "New conversation"

    if (
        len(
            normalized_question,
        )
        <= MAX_CONVERSATION_TITLE_CHARACTERS
    ):
        return normalized_question

    shortened_title = normalized_question[
        : (
            MAX_CONVERSATION_TITLE_CHARACTERS
            - 3
        )
    ].rstrip()

    return f"{shortened_title}..."


def _resolve_filter(
    *,
    request_value: UUID | None,
    conversation_value: UUID | None,
    field_name: str,
) -> UUID | None:
    """Resolve one request filter against saved conversation data."""

    if (
        request_value is not None
        and conversation_value is not None
        and request_value != conversation_value
    ):
        raise StudyConversationValidationError(
            f"The request {field_name} conflicts "
            "with the saved conversation.",
        )

    if request_value is not None:
        return request_value

    return conversation_value
