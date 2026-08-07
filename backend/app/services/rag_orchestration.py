# File: /backend/app/services/rag_orchestration.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from inspect import isawaitable
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.ai.grounded_answer_contracts import (
    ConversationMemoryMessage,
    GroundedAnswerGenerationError,
    GroundedAnswerOutcome,
    GroundedAnswerRequest,
    GroundedAnswerResponseError,
    GroundedAnswerResult,
    GroundedAnswerValidationError,
    GroundedSourceReference,
)
from app.ai.retrieval_contracts import (
    RetrievalError,
    RetrievedStudyChunk,
)
from app.services.query_embedding import QueryEmbeddingError
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
    RetrievalOrchestrationResult,
)

DEFAULT_RAG_MATCH_COUNT = 8
DEFAULT_RAG_SIMILARITY_THRESHOLD = 0.60


class RagOrchestrationFailureCode(StrEnum):
    """Stable failure codes for combined RAG orchestration."""

    VALIDATION_FAILED = "RAG_ORCHESTRATION_VALIDATION_FAILED"
    RETRIEVAL_FAILED = "RAG_ORCHESTRATION_RETRIEVAL_FAILED"
    GENERATION_FAILED = "RAG_ORCHESTRATION_GENERATION_FAILED"
    RESPONSE_FAILED = "RAG_ORCHESTRATION_RESPONSE_FAILED"


class RagOrchestrationError(RuntimeError):
    """Base error with a stable combined RAG failure code."""

    def __init__(
        self,
        message: str,
        *,
        error_code: RagOrchestrationFailureCode,
    ) -> None:
        super().__init__(
            message,
        )
        self.error_code = error_code


class RagOrchestrationValidationError(
    RagOrchestrationError,
):
    """Raised when the combined RAG request is invalid."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                RagOrchestrationFailureCode.VALIDATION_FAILED
            ),
        )


class RagOrchestrationRetrievalError(
    RagOrchestrationError,
):
    """Raised when embedding or vector retrieval fails."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                RagOrchestrationFailureCode.RETRIEVAL_FAILED
            ),
        )


class RagOrchestrationGenerationError(
    RagOrchestrationError,
):
    """Raised when grounded-answer generation fails."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                RagOrchestrationFailureCode.GENERATION_FAILED
            ),
        )


class RagOrchestrationResponseError(
    RagOrchestrationError,
):
    """Raised when combined service results are inconsistent."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            error_code=(
                RagOrchestrationFailureCode.RESPONSE_FAILED
            ),
        )


@runtime_checkable
class RetrievalOrchestrationProtocol(Protocol):
    """Required retrieval behavior for combined RAG."""

    async def retrieve(
        self,
        request: RetrievalOrchestrationRequest,
    ) -> RetrievalOrchestrationResult:
        """Retrieve eligible study chunks."""

    async def aclose(
        self,
    ) -> None:
        """Close retrieval resources."""


@runtime_checkable
class GroundedAnswerGenerationProtocol(Protocol):
    """Required answer-generation behavior for combined RAG."""

    async def generate(
        self,
        request: GroundedAnswerRequest,
    ) -> GroundedAnswerResult:
        """Generate a grounded answer."""

    async def aclose(
        self,
    ) -> None:
        """Close generation resources."""


@dataclass(frozen=True, slots=True)
class RagOrchestrationRequest:
    """Validated input for one authenticated RAG operation."""

    user_id: UUID
    question: str
    memory: tuple[
        ConversationMemoryMessage,
        ...,
    ] = ()
    conversation_id: UUID | None = None
    study_file_id: UUID | None = None
    subject_id: UUID | None = None
    match_count: int = DEFAULT_RAG_MATCH_COUNT
    similarity_threshold: float = (
        DEFAULT_RAG_SIMILARITY_THRESHOLD
    )

    def __post_init__(self) -> None:
        if (
            self.conversation_id is not None
            and not isinstance(
                self.conversation_id,
                UUID,
            )
        ):
            raise RagOrchestrationValidationError(
                "conversation_id must be a UUID or None."
            )

        retrieval_request = _build_retrieval_request(
            user_id=self.user_id,
            question=self.question,
            study_file_id=self.study_file_id,
            subject_id=self.subject_id,
            match_count=self.match_count,
            similarity_threshold=self.similarity_threshold,
        )

        try:
            memory_request = GroundedAnswerRequest(
                question=retrieval_request.question,
                chunks=(),
                memory=self.memory,
            )
        except (
            GroundedAnswerValidationError,
            TypeError,
            ValueError,
        ) as exc:
            raise RagOrchestrationValidationError(
                "The combined RAG memory is invalid."
            ) from exc

        object.__setattr__(
            self,
            "user_id",
            retrieval_request.user_id,
        )

        object.__setattr__(
            self,
            "question",
            retrieval_request.question,
        )

        object.__setattr__(
            self,
            "memory",
            memory_request.memory,
        )

        object.__setattr__(
            self,
            "study_file_id",
            retrieval_request.study_file_id,
        )

        object.__setattr__(
            self,
            "subject_id",
            retrieval_request.subject_id,
        )

        object.__setattr__(
            self,
            "match_count",
            retrieval_request.match_count,
        )

        object.__setattr__(
            self,
            "similarity_threshold",
            retrieval_request.similarity_threshold,
        )

    def to_retrieval_request(
        self,
    ) -> RetrievalOrchestrationRequest:
        """Convert into the Phase 5C retrieval request."""

        return _build_retrieval_request(
            user_id=self.user_id,
            question=self.question,
            study_file_id=self.study_file_id,
            subject_id=self.subject_id,
            match_count=self.match_count,
            similarity_threshold=self.similarity_threshold,
        )


@dataclass(frozen=True, slots=True)
class RagOrchestrationResult:
    """Validated combined retrieval and grounded-answer result."""

    request: RagOrchestrationRequest
    retrieval: RetrievalOrchestrationResult
    grounded_answer: GroundedAnswerResult

    def __post_init__(self) -> None:
        if not isinstance(
            self.request,
            RagOrchestrationRequest,
        ):
            raise RagOrchestrationResponseError(
                "request must be a RagOrchestrationRequest."
            )

        if not isinstance(
            self.retrieval,
            RetrievalOrchestrationResult,
        ):
            raise RagOrchestrationResponseError(
                "retrieval must be a "
                "RetrievalOrchestrationResult."
            )

        if not isinstance(
            self.grounded_answer,
            GroundedAnswerResult,
        ):
            raise RagOrchestrationResponseError(
                "grounded_answer must be a "
                "GroundedAnswerResult."
            )

        expected_retrieval_request = (
            self.request.to_retrieval_request()
        )

        if self.retrieval.request != expected_retrieval_request:
            raise RagOrchestrationResponseError(
                "The retrieval result does not match "
                "the combined RAG request."
            )

        if (
            self.grounded_answer.request.question
            != self.request.question
        ):
            raise RagOrchestrationResponseError(
                "The grounded-answer question does not "
                "match the combined RAG request."
            )

        if (
            self.grounded_answer.request.memory
            != self.request.memory
        ):
            raise RagOrchestrationResponseError(
                "The grounded-answer memory does not "
                "match the combined RAG request."
            )

        self._validate_context_consistency()

    def _validate_context_consistency(
        self,
    ) -> None:
        retrieved_chunks = self.retrieval.chunks
        answer_chunks = self.grounded_answer.request.chunks

        if not retrieved_chunks:
            if (
                self.grounded_answer.outcome
                != GroundedAnswerOutcome.NO_CONTEXT
            ):
                raise RagOrchestrationResponseError(
                    "An empty retrieval result must produce "
                    "a no-context answer."
                )

            if answer_chunks:
                raise RagOrchestrationResponseError(
                    "A no-context answer cannot preserve chunks."
                )

            return

        if (
            self.grounded_answer.outcome
            != GroundedAnswerOutcome.ANSWERED
        ):
            raise RagOrchestrationResponseError(
                "Retrieved context must produce an "
                "answered result."
            )

        if not answer_chunks:
            raise RagOrchestrationResponseError(
                "An answered result must preserve at "
                "least one retrieved chunk."
            )

        retrieved_chunk_ids = tuple(
            chunk.chunk_id
            for chunk in retrieved_chunks
        )

        answer_chunk_ids = tuple(
            chunk.chunk_id
            for chunk in answer_chunks
        )

        if (
            retrieved_chunk_ids[
                : len(answer_chunk_ids)
            ]
            != answer_chunk_ids
        ):
            raise RagOrchestrationResponseError(
                "The grounded-answer context is not an "
                "ordered subset of retrieved chunks."
            )

    @property
    def outcome(
        self,
    ) -> GroundedAnswerOutcome:
        """Return the final grounded-answer outcome."""

        return self.grounded_answer.outcome

    @property
    def answer(
        self,
    ) -> str:
        """Return the final answer text."""

        return self.grounded_answer.answer

    @property
    def sources(
        self,
    ) -> tuple[GroundedSourceReference, ...]:
        """Return safe source references."""

        return self.grounded_answer.sources

    @property
    def retrieved_chunks(
        self,
    ) -> tuple[RetrievedStudyChunk, ...]:
        """Return retrieved chunks for internal processing."""

        return self.retrieval.chunks

    @property
    def retrieved_count(
        self,
    ) -> int:
        """Return the number of retrieved chunks."""

        return len(
            self.retrieval.chunks,
        )

    @property
    def source_count(
        self,
    ) -> int:
        """Return the number of preserved answer sources."""

        return self.grounded_answer.source_count

    @property
    def context_available(
        self,
    ) -> bool:
        """Return whether the operation found usable context."""

        return self.grounded_answer.context_available

    @property
    def generation_provider(
        self,
    ) -> str | None:
        """Return safe generation-provider metadata."""

        return self.grounded_answer.provider

    @property
    def generation_model(
        self,
    ) -> str | None:
        """Return safe generation-model metadata."""

        return self.grounded_answer.model

    @property
    def embedding_provider(
        self,
    ) -> str:
        """Return safe embedding-provider metadata."""

        return self.retrieval.embedding_provider

    @property
    def embedding_model(
        self,
    ) -> str:
        """Return safe embedding-model metadata."""

        return self.retrieval.embedding_model

    @property
    def embedding_dimensions(
        self,
    ) -> int:
        """Return the query-embedding dimensions."""

        return self.retrieval.embedding_dimensions


class RagOrchestrationService:
    """Run retrieval and grounded generation as one operation."""

    def __init__(
        self,
        *,
        retrieval_service: RetrievalOrchestrationProtocol,
        grounded_answer_service: (
            GroundedAnswerGenerationProtocol
        ),
    ) -> None:
        if not isinstance(
            retrieval_service,
            RetrievalOrchestrationProtocol,
        ):
            raise RagOrchestrationValidationError(
                "retrieval_service does not implement "
                "the required interface."
            )

        if not isinstance(
            grounded_answer_service,
            GroundedAnswerGenerationProtocol,
        ):
            raise RagOrchestrationValidationError(
                "grounded_answer_service does not implement "
                "the required interface."
            )

        self._retrieval_service = retrieval_service
        self._grounded_answer_service = (
            grounded_answer_service
        )

    async def answer(
        self,
        request: RagOrchestrationRequest,
    ) -> RagOrchestrationResult:
        """Retrieve study context and generate one answer."""

        if not isinstance(
            request,
            RagOrchestrationRequest,
        ):
            raise RagOrchestrationValidationError(
                "request must be a RagOrchestrationRequest."
            )

        try:
            retrieval_result = (
                await self._retrieval_service.retrieve(
                    request.to_retrieval_request(),
                )
            )
        except (
            QueryEmbeddingError,
            RetrievalError,
        ) as exc:
            raise RagOrchestrationRetrievalError(
                "Study-material retrieval failed."
            ) from exc
        except Exception as exc:
            raise RagOrchestrationRetrievalError(
                "An unexpected study-material retrieval "
                "failure occurred."
            ) from exc

        if not isinstance(
            retrieval_result,
            RetrievalOrchestrationResult,
        ):
            raise RagOrchestrationResponseError(
                "The retrieval service returned an "
                "invalid result."
            )

        grounded_request = GroundedAnswerRequest(
            question=request.question,
            chunks=retrieval_result.chunks,
            memory=request.memory,
        )

        try:
            grounded_result = (
                await self._grounded_answer_service.generate(
                    grounded_request,
                )
            )
        except GroundedAnswerGenerationError as exc:
            raise RagOrchestrationGenerationError(
                "Grounded-answer generation failed."
            ) from exc
        except (
            GroundedAnswerValidationError,
            GroundedAnswerResponseError,
        ) as exc:
            raise RagOrchestrationResponseError(
                "The grounded-answer result was invalid."
            ) from exc
        except Exception as exc:
            raise RagOrchestrationGenerationError(
                "An unexpected grounded-answer generation "
                "failure occurred."
            ) from exc

        if not isinstance(
            grounded_result,
            GroundedAnswerResult,
        ):
            raise RagOrchestrationResponseError(
                "The grounded-answer service returned "
                "an invalid result."
            )

        return RagOrchestrationResult(
            request=request,
            retrieval=retrieval_result,
            grounded_answer=grounded_result,
        )

    async def aclose(
        self,
    ) -> None:
        """Close generation and retrieval resources."""

        try:
            await _close_service(
                self._grounded_answer_service,
            )
        finally:
            await _close_service(
                self._retrieval_service,
            )


def _build_retrieval_request(
    *,
    user_id: UUID,
    question: str,
    study_file_id: UUID | None,
    subject_id: UUID | None,
    match_count: int,
    similarity_threshold: float,
) -> RetrievalOrchestrationRequest:
    try:
        return RetrievalOrchestrationRequest(
            user_id=user_id,
            question=question,
            study_file_id=study_file_id,
            subject_id=subject_id,
            match_count=match_count,
            similarity_threshold=similarity_threshold,
        )
    except (
        RetrievalError,
        TypeError,
        ValueError,
    ) as exc:
        raise RagOrchestrationValidationError(
            "The combined RAG request is invalid."
        ) from exc


async def _close_service(
    service: object,
) -> None:
    close_method = getattr(
        service,
        "aclose",
        None,
    )

    if not callable(
        close_method,
    ):
        return

    close_result = close_method()

    if isawaitable(
        close_result,
    ):
        await close_result
