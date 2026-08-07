# File: /backend/tests/test_study_conversation_rag.py
# Purpose: Tests conversation-aware RAG orchestration and message
# persistence without live database or AI provider calls.

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.ai.grounded_answer_contracts import (
    GroundedAnswerRequest,
    GroundedAnswerResult,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.schemas.study_conversation import (
    StudyConversationResponse,
    StudyConversationSummaryState,
    StudyConversationSummaryUpdate,
    StudyMessageResponse,
    StudyMessageSourceResponse,
)
from app.services.rag_orchestration import (
    RagOrchestrationRequest,
    RagOrchestrationResult,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationResult,
)
from app.services.study_conversation_errors import (
    StudyConversationNotFoundError,
    StudyConversationValidationError,
)
from app.services.study_conversation_rag import (
    StudyConversationRagService,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

CONVERSATION_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

STUDY_FILE_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_conversation(
    *,
    conversation_id: UUID = CONVERSATION_ID,
    title: str = "Biology review",
    subject_id: UUID | None = SUBJECT_ID,
    study_file_id: UUID | None = STUDY_FILE_ID,
) -> StudyConversationResponse:
    now = datetime.now(
        UTC,
    )

    return StudyConversationResponse(
        id=conversation_id,
        title=title,
        subject_id=subject_id,
        study_file_id=study_file_id,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )


def make_chunk() -> RetrievedStudyChunk:
    content = (
        "Photosynthesis converts light energy "
        "into chemical energy."
    )

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                uuid4(),
            ),
            "study_file_id": str(
                STUDY_FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": 2,
            "content": content,
            "start_offset": 0,
            "end_offset": len(
                content,
            ),
            "chunk_metadata": {},
            "embedding_model": "fake-embedding-model",
            "similarity_score": 0.93,
        },
    )


def make_rag_result(
    request: RagOrchestrationRequest,
    *,
    no_context: bool = False,
) -> RagOrchestrationResult:
    if no_context:
        retrieval = RetrievalOrchestrationResult(
            request=request.to_retrieval_request(),
            chunks=(),
            embedding_provider="gemini",
            embedding_model="fake-embedding-model",
            embedding_dimensions=768,
        )

        grounded_request = GroundedAnswerRequest(
            question=request.question,
            chunks=(),
            memory=request.memory,
        )

        grounded_result = GroundedAnswerResult.no_context(
            grounded_request,
        )

        return RagOrchestrationResult(
            request=request,
            retrieval=retrieval,
            grounded_answer=grounded_result,
        )

    chunk = make_chunk()

    retrieval = RetrievalOrchestrationResult(
        request=request.to_retrieval_request(),
        chunks=(
            chunk,
        ),
        embedding_provider="gemini",
        embedding_model="fake-embedding-model",
        embedding_dimensions=768,
    )

    grounded_request = GroundedAnswerRequest(
        question=request.question,
        chunks=(
            chunk,
        ),
        memory=request.memory,
    )

    grounded_result = GroundedAnswerResult.generated(
        request=grounded_request,
        answer=(
            "Photosynthesis converts light energy "
            "into chemical energy. [Source 1]"
        ),
        provider="gemini",
        model="fake-generation-model",
    )

    return RagOrchestrationResult(
        request=request,
        retrieval=retrieval,
        grounded_answer=grounded_result,
    )


class FakeRepository:
    def __init__(
        self,
    ) -> None:
        self.conversation: (
            StudyConversationResponse
            | None
        ) = None

        self.messages: list[
            StudyMessageResponse
        ] = []

        self.summary_state: (
            StudyConversationSummaryState
            | None
        ) = StudyConversationSummaryState(
            conversation_id=CONVERSATION_ID,
            summary_text=None,
            summarized_message_count=0,
            summary_updated_at=None,
            summary_version=1,
        )

        self.calls: list[
            tuple[
                object,
                ...,
            ]
        ] = []

    def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str,
        subject_id: UUID | None,
        study_file_id: UUID | None,
    ) -> StudyConversationResponse:
        self.calls.append(
            (
                "create",
                user_id,
                title,
                subject_id,
                study_file_id,
            ),
        )

        conversation = make_conversation(
            title=title,
            subject_id=subject_id,
            study_file_id=study_file_id,
        )

        self.conversation = conversation

        return conversation

    def get_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationResponse | None:
        self.calls.append(
            (
                "get",
                user_id,
                conversation_id,
            ),
        )

        return self.conversation

    def get_summary_state(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationSummaryState | None:
        self.calls.append(
            (
                "get_summary",
                user_id,
                conversation_id,
            ),
        )

        return self.summary_state

    def list_messages_from_offset(
        self,
        *,
        conversation_id: UUID,
        offset: int,
        limit: int = 501,
    ) -> list[
        StudyMessageResponse
    ]:
        self.calls.append(
            (
                "list_window",
                conversation_id,
                offset,
                limit,
            ),
        )

        return self.messages[
            offset:
            (
                offset
                + limit
            )
        ]

    def save_summary_state(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        update: StudyConversationSummaryUpdate,
    ) -> StudyConversationSummaryState | None:
        self.calls.append(
            (
                "save_summary",
                user_id,
                conversation_id,
                update,
            ),
        )

        self.summary_state = (
            StudyConversationSummaryState(
                conversation_id=conversation_id,
                summary_text=update.summary_text,
                summarized_message_count=(
                    update.summarized_message_count
                ),
                summary_updated_at=datetime.now(
                    UTC,
                ),
                summary_version=update.summary_version,
            )
        )

        return self.summary_state

    def list_recent_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = 10,
    ) -> list[
        StudyMessageResponse
    ]:
        self.calls.append(
            (
                "list_recent",
                conversation_id,
                limit,
            ),
        )

        return self.messages[
            -limit:
        ]

    def save_user_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
    ) -> StudyMessageResponse:
        self.calls.append(
            (
                "save_user",
                conversation_id,
                content,
            ),
        )

        return StudyMessageResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content=content,
            created_at=datetime.now(
                UTC,
            ),
        )

    def save_assistant_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
        outcome: str,
        sources: tuple[
            StudyMessageSourceResponse,
            ...,
        ],
    ) -> StudyMessageResponse:
        self.calls.append(
            (
                "save_assistant",
                conversation_id,
                content,
                outcome,
                sources,
            ),
        )

        return StudyMessageResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            outcome=outcome,
            sources=list(
                sources,
            ),
            created_at=datetime.now(
                UTC,
            ),
        )


class FakeRagService:
    def __init__(
        self,
        *,
        no_context: bool = False,
    ) -> None:
        self.no_context = no_context

        self.requests: list[
            RagOrchestrationRequest
        ] = []

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> RagOrchestrationResult:
        self.requests.append(
            request,
        )

        return make_rag_result(
            request,
            no_context=self.no_context,
        )


def test_new_conversation_saves_user_and_assistant_pair() -> None:
    repository = FakeRepository()
    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="What is photosynthesis?",
        subject_id=SUBJECT_ID,
        study_file_id=STUDY_FILE_ID,
    )

    result = asyncio.run(
        service.answer(
            request,
        )
    )

    assert result.conversation.id == CONVERSATION_ID

    assert (
        result.rag_result.request.conversation_id
        == CONVERSATION_ID
    )

    assert result.user_message.role == "user"
    assert result.assistant_message.role == "assistant"
    assert result.assistant_message.outcome == "answered"

    assert repository.calls[0] == (
        "create",
        USER_ID,
        "What is photosynthesis?",
        SUBJECT_ID,
        STUDY_FILE_ID,
    )

    assert repository.calls[1][0] == "save_user"
    assert repository.calls[2][0] == "save_assistant"


def test_existing_conversation_is_checked_before_answering() -> None:
    repository = FakeRepository()

    repository.conversation = make_conversation()

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain this topic.",
        conversation_id=CONVERSATION_ID,
    )

    result = asyncio.run(
        service.answer(
            request,
        )
    )

    assert result.conversation.id == CONVERSATION_ID

    assert repository.calls[0] == (
        "get",
        USER_ID,
        CONVERSATION_ID,
    )

    assert repository.calls[1] == (
        "get_summary",
        USER_ID,
        CONVERSATION_ID,
    )

    assert repository.calls[2] == (
        "list_window",
        CONVERSATION_ID,
        0,
        501,
    )

    assert repository.calls[3] == (
        "list_recent",
        CONVERSATION_ID,
        10,
    )

    assert repository.calls[4][0] == "save_user"

    captured_request = rag_service.requests[0]

    assert captured_request.subject_id == SUBJECT_ID
    assert captured_request.study_file_id == STUDY_FILE_ID


def test_missing_conversation_stops_before_rag() -> None:
    repository = FakeRepository()
    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain the topic.",
        conversation_id=CONVERSATION_ID,
    )

    with pytest.raises(
        StudyConversationNotFoundError,
    ):
        asyncio.run(
            service.answer(
                request,
            )
        )

    assert rag_service.requests == []

    assert repository.calls == [
        (
            "get",
            USER_ID,
            CONVERSATION_ID,
        ),
    ]


def test_existing_conversation_rejects_conflicting_subject() -> None:
    repository = FakeRepository()

    repository.conversation = make_conversation()

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain the topic.",
        conversation_id=CONVERSATION_ID,
        subject_id=uuid4(),
    )

    with pytest.raises(
        StudyConversationValidationError,
        match="subject_id conflicts",
    ):
        asyncio.run(
            service.answer(
                request,
            )
        )

    assert rag_service.requests == []

    assert all(
        call[0] != "save_user"
        for call in repository.calls
    )


def test_existing_conversation_rejects_conflicting_file() -> None:
    repository = FakeRepository()

    repository.conversation = make_conversation()

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain the topic.",
        conversation_id=CONVERSATION_ID,
        study_file_id=uuid4(),
    )

    with pytest.raises(
        StudyConversationValidationError,
        match="study_file_id conflicts",
    ):
        asyncio.run(
            service.answer(
                request,
            )
        )

    assert rag_service.requests == []


def test_no_context_answer_saves_empty_sources() -> None:
    repository = FakeRepository()
    rag_service = FakeRagService(
        no_context=True,
    )

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Explain an unavailable topic.",
    )

    result = asyncio.run(
        service.answer(
            request,
        )
    )

    assert result.assistant_message.outcome == "no_context"
    assert result.assistant_message.sources == []

    assistant_call = repository.calls[-1]

    assert assistant_call[0] == "save_assistant"
    assert assistant_call[3] == "no_context"
    assert assistant_call[4] == ()


def test_long_first_question_creates_short_title() -> None:
    repository = FakeRepository()
    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="x" * 500,
    )

    asyncio.run(
        service.answer(
            request,
        )
    )

    title = repository.calls[0][2]

    assert isinstance(
        title,
        str,
    )

    assert len(
        title,
    ) <= 120

    assert title.endswith(
        "...",
    )

def test_existing_conversation_forwards_recent_memory_before_new_question() -> None:
    repository = FakeRepository()

    repository.conversation = make_conversation()

    now = datetime.now(
        UTC,
    )

    repository.messages = [
        StudyMessageResponse(
            id=uuid4(),
            conversation_id=CONVERSATION_ID,
            role="user",
            content="What is photosynthesis?",
            created_at=now,
        ),
        StudyMessageResponse(
            id=uuid4(),
            conversation_id=CONVERSATION_ID,
            role="assistant",
            content=(
                "It converts light energy into "
                "chemical energy."
            ),
            outcome="no_context",
            sources=[],
            created_at=now,
        ),
    ]

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Why is that important?",
        conversation_id=CONVERSATION_ID,
    )

    asyncio.run(
        service.answer(
            request,
        )
    )

    captured_request = rag_service.requests[0]

    assert [
        message.content
        for message in captured_request.memory
    ] == [
        "What is photosynthesis?",
        (
            "It converts light energy into "
            "chemical energy."
        ),
    ]

    assert repository.calls[0][0] == "get"
    assert repository.calls[1][0] == "get_summary"
    assert repository.calls[2][0] == "list_window"
    assert repository.calls[3][0] == "list_recent"
    assert repository.calls[4][0] == "save_user"
    assert repository.calls[5][0] == "save_assistant"


def test_new_conversation_does_not_load_old_memory() -> None:
    repository = FakeRepository()
    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    request = RagOrchestrationRequest(
        user_id=USER_ID,
        question="Start a new discussion.",
    )

    asyncio.run(
        service.answer(
            request,
        )
    )

    assert rag_service.requests[0].memory == ()

    assert all(
        call[0] != "list_recent"
        for call in repository.calls
    )

def make_saved_message(
    index: int,
) -> StudyMessageResponse:
    role = (
        "user"
        if index % 2 == 0
        else "assistant"
    )

    if role == "user":
        return StudyMessageResponse(
            id=uuid4(),
            conversation_id=CONVERSATION_ID,
            role="user",
            content=f"Message {index}.",
            created_at=datetime.now(
                UTC,
            ),
        )

    return StudyMessageResponse(
        id=uuid4(),
        conversation_id=CONVERSATION_ID,
        role="assistant",
        content=f"Message {index}.",
        outcome="no_context",
        sources=[],
        created_at=datetime.now(
            UTC,
        ),
    )


def test_long_history_refreshes_summary_before_answering() -> None:
    repository = FakeRepository()
    repository.conversation = make_conversation()

    repository.messages = [
        make_saved_message(
            index,
        )
        for index in range(
            11
        )
    ]

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    asyncio.run(
        service.answer(
            RagOrchestrationRequest(
                user_id=USER_ID,
                question="Continue.",
                conversation_id=CONVERSATION_ID,
            )
        )
    )

    assert repository.summary_state is not None
    assert repository.summary_state.summary_text is not None

    assert (
        repository.summary_state.summarized_message_count
        == 2
    )

    captured_memory = rag_service.requests[0].memory

    assert len(
        captured_memory,
    ) == 10

    assert captured_memory[0].content.startswith(
        "Earlier conversation summary"
    )

    assert [
        item.content
        for item in captured_memory[1:]
    ] == [
        f"Message {index}."
        for index in range(
            2,
            11,
        )
    ]

    call_names = [
        call[0]
        for call in repository.calls
    ]

    assert call_names.index(
        "save_summary",
    ) < call_names.index(
        "save_user",
    )


def test_existing_summary_refreshes_only_new_oldest_message() -> None:
    repository = FakeRepository()
    repository.conversation = make_conversation()

    repository.summary_state = (
        StudyConversationSummaryState(
            conversation_id=CONVERSATION_ID,
            summary_text=(
                "Earlier conversation summary "
                "(not factual study evidence):\n"
                "User: Message 0.\n"
                "Assistant: Message 1."
            ),
            summarized_message_count=2,
            summary_updated_at=datetime.now(
                UTC,
            ),
            summary_version=1,
        )
    )

    repository.messages = [
        make_saved_message(
            index,
        )
        for index in range(
            12
        )
    ]

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    asyncio.run(
        service.answer(
            RagOrchestrationRequest(
                user_id=USER_ID,
                question="Continue again.",
                conversation_id=CONVERSATION_ID,
            )
        )
    )

    assert repository.summary_state is not None

    assert (
        repository.summary_state.summarized_message_count
        == 3
    )

    assert (
        "User: Message 2."
        in repository.summary_state.summary_text
    )

    captured_memory = rag_service.requests[0].memory

    assert [
        item.content
        for item in captured_memory[1:]
    ] == [
        f"Message {index}."
        for index in range(
            3,
            12,
        )
    ]


def test_ten_messages_do_not_create_summary() -> None:
    repository = FakeRepository()
    repository.conversation = make_conversation()

    repository.messages = [
        make_saved_message(
            index,
        )
        for index in range(
            10
        )
    ]

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    asyncio.run(
        service.answer(
            RagOrchestrationRequest(
                user_id=USER_ID,
                question="Continue.",
                conversation_id=CONVERSATION_ID,
            )
        )
    )

    assert repository.summary_state is not None
    assert repository.summary_state.summary_text is None

    assert all(
        call[0] != "save_summary"
        for call in repository.calls
    )

    assert len(
        rag_service.requests[0].memory,
    ) == 10


def test_summary_refresh_window_preserves_newest_nine() -> None:
    repository = FakeRepository()
    repository.conversation = make_conversation()

    repository.messages = [
        make_saved_message(
            index,
        )
        for index in range(
            501
        )
    ]

    rag_service = FakeRagService()

    service = StudyConversationRagService(
        repository=repository,
        rag_service=rag_service,
    )

    asyncio.run(
        service.answer(
            RagOrchestrationRequest(
                user_id=USER_ID,
                question="Continue the long discussion.",
                conversation_id=CONVERSATION_ID,
            )
        )
    )

    assert repository.summary_state is not None

    assert (
        repository.summary_state.summarized_message_count
        == 492
    )

    recent_memory = (
        rag_service.requests[0].memory[
            1:
        ]
    )

    assert [
        item.content
        for item in recent_memory
    ] == [
        f"Message {index}."
        for index in range(
            492,
            501,
        )
    ]
