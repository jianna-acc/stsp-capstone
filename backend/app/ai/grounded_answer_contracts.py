# File: /backend/app/ai/grounded_answer_contracts.py

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from uuid import UUID

from app.ai.retrieval_contracts import RetrievedStudyChunk

NO_CONTEXT_ANSWER = (
    "I could not find enough relevant information in your uploaded "
    "study materials to answer this question."
)

MAX_CONVERSATION_MEMORY_MESSAGES = 10
MAX_CONVERSATION_MEMORY_CHARACTERS = 8_000


class GroundedAnswerFailureCode(StrEnum):
    """Stable failure codes for grounded-answer generation."""

    VALIDATION_FAILED = (
        "GROUNDED_ANSWER_VALIDATION_FAILED"
    )
    GENERATION_FAILED = (
        "GROUNDED_ANSWER_GENERATION_FAILED"
    )
    RESPONSE_FAILED = (
        "GROUNDED_ANSWER_RESPONSE_FAILED"
    )


class GroundedAnswerOutcome(StrEnum):
    """Successful grounded-answer outcomes."""

    ANSWERED = "answered"
    NO_CONTEXT = "no_context"


class ConversationMemoryRole(StrEnum):
    """Allowed roles preserved as bounded conversation memory."""

    USER = "user"
    ASSISTANT = "assistant"


class GroundedAnswerError(RuntimeError):
    """Base exception with a stable Phase 5D error code."""

    def __init__(
        self,
        message: str,
        *,
        error_code: GroundedAnswerFailureCode,
    ) -> None:
        super().__init__(
            message,
        )
        self.error_code = error_code


class GroundedAnswerValidationError(
    GroundedAnswerError,
):
    """Raised when grounded-answer input is invalid."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                GroundedAnswerFailureCode.VALIDATION_FAILED
            ),
        )


class GroundedAnswerGenerationError(
    GroundedAnswerError,
):
    """Raised when the configured AI provider fails."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                GroundedAnswerFailureCode.GENERATION_FAILED
            ),
        )


class GroundedAnswerResponseError(
    GroundedAnswerError,
):
    """Raised when an answer result is inconsistent."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                GroundedAnswerFailureCode.RESPONSE_FAILED
            ),
        )


@dataclass(frozen=True, slots=True)
class ConversationMemoryMessage:
    """One bounded prior message supplied as conversation context."""

    role: ConversationMemoryRole
    content: str

    def __post_init__(self) -> None:
        try:
            role = ConversationMemoryRole(
                self.role,
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise GroundedAnswerValidationError(
                "Conversation memory role is invalid."
            ) from exc

        content = _validated_text(
            self.content,
            field_name="conversation memory content",
            error_type=GroundedAnswerValidationError,
        )

        object.__setattr__(
            self,
            "role",
            role,
        )

        object.__setattr__(
            self,
            "content",
            content,
        )


@dataclass(frozen=True, slots=True)
class GroundedAnswerRequest:
    """Validated question and retrieved study context."""

    question: str
    chunks: tuple[RetrievedStudyChunk, ...]
    memory: tuple[
        ConversationMemoryMessage,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        question = _validated_text(
            self.question,
            field_name="question",
            error_type=GroundedAnswerValidationError,
        )

        if (
            isinstance(self.chunks, (str, bytes))
            or not isinstance(self.chunks, Sequence)
        ):
            raise GroundedAnswerValidationError(
                "chunks must be a sequence."
            )

        chunks = tuple(
            self.chunks,
        )

        if not all(
            isinstance(
                chunk,
                RetrievedStudyChunk,
            )
            for chunk in chunks
        ):
            raise GroundedAnswerValidationError(
                "Every context item must be a "
                "RetrievedStudyChunk."
            )

        chunk_ids = [
            chunk.chunk_id
            for chunk in chunks
        ]

        if len(chunk_ids) != len(
            set(chunk_ids)
        ):
            raise GroundedAnswerValidationError(
                "The grounded-answer request contains "
                "duplicate chunks."
            )

        for current, following in pairwise(
            chunks,
        ):
            if (
                current.similarity_score
                < following.similarity_score
            ):
                raise GroundedAnswerValidationError(
                    "Context chunks must be ordered by "
                    "descending similarity score."
                )

        if (
            isinstance(
                self.memory,
                (
                    str,
                    bytes,
                ),
            )
            or not isinstance(
                self.memory,
                Sequence,
            )
        ):
            raise GroundedAnswerValidationError(
                "memory must be a sequence."
            )

        memory = tuple(
            self.memory,
        )

        if not all(
            isinstance(
                message,
                ConversationMemoryMessage,
            )
            for message in memory
        ):
            raise GroundedAnswerValidationError(
                "Every memory item must be a "
                "ConversationMemoryMessage."
            )

        if (
            len(
                memory,
            )
            > MAX_CONVERSATION_MEMORY_MESSAGES
        ):
            raise GroundedAnswerValidationError(
                "Conversation memory exceeds the "
                "message limit."
            )

        memory_character_count = sum(
            len(
                message.content,
            )
            for message in memory
        )

        if (
            memory_character_count
            > MAX_CONVERSATION_MEMORY_CHARACTERS
        ):
            raise GroundedAnswerValidationError(
                "Conversation memory exceeds the "
                "character limit."
            )

        object.__setattr__(
            self,
            "question",
            question,
        )

        object.__setattr__(
            self,
            "chunks",
            chunks,
        )

        object.__setattr__(
            self,
            "memory",
            memory,
        )

    @property
    def context_available(self) -> bool:
        """Return whether retrieved study context exists."""

        return bool(
            self.chunks,
        )

    @property
    def retrieved_count(self) -> int:
        """Return the number of retrieved chunks."""

        return len(
            self.chunks,
        )

    def build_source_references(
        self,
    ) -> tuple[GroundedSourceReference, ...]:
        """Build deterministic references for all chunks."""

        return tuple(
            GroundedSourceReference.from_chunk(
                source_number=source_number,
                chunk=chunk,
            )
            for source_number, chunk in enumerate(
                self.chunks,
                start=1,
            )
        )


@dataclass(frozen=True, slots=True)
class GroundedSourceReference:
    """Safe source metadata preserved with an answer."""

    source_number: int
    chunk_id: UUID
    study_file_id: UUID
    subject_id: UUID | None
    source_name: str
    chunk_index: int
    similarity_score: float

    @classmethod
    def from_chunk(
        cls,
        *,
        source_number: int,
        chunk: RetrievedStudyChunk,
    ) -> GroundedSourceReference:
        """Create a deterministic source reference."""

        if (
            isinstance(source_number, bool)
            or not isinstance(source_number, int)
            or source_number <= 0
        ):
            raise GroundedAnswerResponseError(
                "source_number must be a positive integer."
            )

        if not isinstance(
            chunk,
            RetrievedStudyChunk,
        ):
            raise GroundedAnswerResponseError(
                "chunk must be a RetrievedStudyChunk."
            )

        return cls(
            source_number=source_number,
            chunk_id=chunk.chunk_id,
            study_file_id=chunk.study_file_id,
            subject_id=chunk.subject_id,
            source_name=chunk.source_name,
            chunk_index=chunk.chunk_index,
            similarity_score=chunk.similarity_score,
        )

    @property
    def citation_marker(self) -> str:
        """Return the marker expected in generated answers."""

        return f"[Source {self.source_number}]"


@dataclass(frozen=True, slots=True)
class GroundedAnswerResult:
    """Validated grounded answer or normal no-context result."""

    request: GroundedAnswerRequest
    outcome: GroundedAnswerOutcome
    answer: str
    sources: tuple[GroundedSourceReference, ...]
    provider: str | None
    model: str | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.request,
            GroundedAnswerRequest,
        ):
            raise GroundedAnswerResponseError(
                "request must be a GroundedAnswerRequest."
            )

        if not isinstance(
            self.outcome,
            GroundedAnswerOutcome,
        ):
            raise GroundedAnswerResponseError(
                "outcome must be a GroundedAnswerOutcome."
            )

        answer = _validated_text(
            self.answer,
            field_name="answer",
            error_type=GroundedAnswerResponseError,
        )

        if (
            isinstance(self.sources, (str, bytes))
            or not isinstance(self.sources, Sequence)
        ):
            raise GroundedAnswerResponseError(
                "sources must be a sequence."
            )

        sources = tuple(
            self.sources,
        )

        if not all(
            isinstance(
                source,
                GroundedSourceReference,
            )
            for source in sources
        ):
            raise GroundedAnswerResponseError(
                "Every source must be a "
                "GroundedSourceReference."
            )

        source_numbers = [
            source.source_number
            for source in sources
        ]

        if source_numbers != list(
            range(
                1,
                len(sources) + 1,
            )
        ):
            raise GroundedAnswerResponseError(
                "Source numbers must be consecutive "
                "and begin at one."
            )

        source_chunk_ids = [
            source.chunk_id
            for source in sources
        ]

        if len(source_chunk_ids) != len(
            set(source_chunk_ids)
        ):
            raise GroundedAnswerResponseError(
                "The result contains duplicate sources."
            )

        if (
            self.outcome
            == GroundedAnswerOutcome.NO_CONTEXT
        ):
            _validate_no_context_result(
                request=self.request,
                answer=answer,
                sources=sources,
                provider=self.provider,
                model=self.model,
            )
        else:
            _validate_answered_result(
                request=self.request,
                sources=sources,
                provider=self.provider,
                model=self.model,
            )

        object.__setattr__(
            self,
            "answer",
            answer,
        )

        object.__setattr__(
            self,
            "sources",
            sources,
        )

        if self.provider is not None:
            object.__setattr__(
                self,
                "provider",
                self.provider.strip(),
            )

        if self.model is not None:
            object.__setattr__(
                self,
                "model",
                self.model.strip(),
            )

    @classmethod
    def no_context(
        cls,
        request: GroundedAnswerRequest,
    ) -> GroundedAnswerResult:
        """Create a normal result when no context exists."""

        return cls(
            request=request,
            outcome=GroundedAnswerOutcome.NO_CONTEXT,
            answer=NO_CONTEXT_ANSWER,
            sources=(),
            provider=None,
            model=None,
        )

    @classmethod
    def generated(
        cls,
        *,
        request: GroundedAnswerRequest,
        answer: str,
        provider: str,
        model: str,
    ) -> GroundedAnswerResult:
        """Create a generated answer with source references."""

        return cls(
            request=request,
            outcome=GroundedAnswerOutcome.ANSWERED,
            answer=answer,
            sources=request.build_source_references(),
            provider=provider,
            model=model,
        )

    @property
    def context_available(self) -> bool:
        """Return whether the answer used study context."""

        return self.outcome == GroundedAnswerOutcome.ANSWERED

    @property
    def source_count(self) -> int:
        """Return the number of preserved sources."""

        return len(
            self.sources,
        )


def _validate_no_context_result(
    *,
    request: GroundedAnswerRequest,
    answer: str,
    sources: tuple[GroundedSourceReference, ...],
    provider: str | None,
    model: str | None,
) -> None:
    if request.context_available:
        raise GroundedAnswerResponseError(
            "A no-context result cannot contain "
            "retrieved chunks."
        )

    if answer != NO_CONTEXT_ANSWER:
        raise GroundedAnswerResponseError(
            "A no-context result must use the "
            "approved no-context answer."
        )

    if sources:
        raise GroundedAnswerResponseError(
            "A no-context result cannot contain sources."
        )

    if provider is not None or model is not None:
        raise GroundedAnswerResponseError(
            "A no-context result cannot contain "
            "generation metadata."
        )


def _validate_answered_result(
    *,
    request: GroundedAnswerRequest,
    sources: tuple[GroundedSourceReference, ...],
    provider: str | None,
    model: str | None,
) -> None:
    if not request.context_available:
        raise GroundedAnswerResponseError(
            "A generated answer requires retrieved context."
        )

    if not sources:
        raise GroundedAnswerResponseError(
            "A generated answer requires source references."
        )

    provider_value = _validated_text(
        provider,
        field_name="provider",
        error_type=GroundedAnswerResponseError,
    )

    model_value = _validated_text(
        model,
        field_name="model",
        error_type=GroundedAnswerResponseError,
    )

    expected_chunk_ids = tuple(
        chunk.chunk_id
        for chunk in request.chunks
    )

    source_chunk_ids = tuple(
        source.chunk_id
        for source in sources
    )

    if source_chunk_ids != expected_chunk_ids:
        raise GroundedAnswerResponseError(
            "The result sources do not match the "
            "retrieved context."
        )

    del provider_value
    del model_value


def _validated_text(
    value: object,
    *,
    field_name: str,
    error_type: type[GroundedAnswerError],
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise error_type(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise error_type(
            f"{field_name} must not be empty."
        )

    return normalized