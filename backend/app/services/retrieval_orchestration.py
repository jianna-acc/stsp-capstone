# File: /backend/app/services/retrieval_orchestration.py

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from inspect import isawaitable
from math import isfinite
from numbers import Real
from typing import Protocol
from uuid import UUID

from app.ai.retrieval_contracts import (
    DEFAULT_RETRIEVAL_MATCH_COUNT,
    DEFAULT_RETRIEVAL_SIMILARITY_THRESHOLD,
    MAX_RETRIEVAL_MATCH_COUNT,
    MIN_RETRIEVAL_MATCH_COUNT,
    NO_CONTEXT_MESSAGE,
    RetrievalOutcome,
    RetrievalRequest,
    RetrievalResponseError,
    RetrievalResult,
    RetrievalValidationError,
    RetrievedStudyChunk,
)
from app.ai.retrieval_persistence import RetrievalPersistence
from app.services.query_embedding import (
    QueryEmbeddingResult,
)


class QueryEmbeddingServiceProtocol(Protocol):
    """Query-embedding behavior needed by orchestration."""

    async def embed_query(
        self,
        question: str,
    ) -> QueryEmbeddingResult:
        """Generate one validated query embedding."""


@dataclass(frozen=True, slots=True)
class RetrievalOrchestrationRequest:
    """High-level study-material retrieval request."""

    user_id: UUID
    question: str
    match_count: int = DEFAULT_RETRIEVAL_MATCH_COUNT
    similarity_threshold: float = (
        DEFAULT_RETRIEVAL_SIMILARITY_THRESHOLD
    )
    study_file_id: UUID | None = None
    subject_id: UUID | None = None

    def __post_init__(self) -> None:
        user_id = _required_uuid(
            self.user_id,
            field_name="user_id",
        )

        question = _validated_question(
            self.question,
        )

        match_count = _validated_match_count(
            self.match_count,
        )

        similarity_threshold = _validated_threshold(
            self.similarity_threshold,
        )

        study_file_id = _optional_uuid(
            self.study_file_id,
            field_name="study_file_id",
        )

        subject_id = _optional_uuid(
            self.subject_id,
            field_name="subject_id",
        )

        object.__setattr__(
            self,
            "user_id",
            user_id,
        )
        object.__setattr__(
            self,
            "question",
            question,
        )
        object.__setattr__(
            self,
            "match_count",
            match_count,
        )
        object.__setattr__(
            self,
            "similarity_threshold",
            similarity_threshold,
        )
        object.__setattr__(
            self,
            "study_file_id",
            study_file_id,
        )
        object.__setattr__(
            self,
            "subject_id",
            subject_id,
        )


@dataclass(frozen=True, slots=True)
class RetrievalOrchestrationResult:
    """Safe retrieval result without the raw query vector."""

    request: RetrievalOrchestrationRequest
    chunks: tuple[RetrievedStudyChunk, ...]
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.request,
            RetrievalOrchestrationRequest,
        ):
            raise RetrievalResponseError(
                "request must be a "
                "RetrievalOrchestrationRequest."
            )

        if (
            isinstance(self.chunks, (str, bytes))
            or not isinstance(self.chunks, Sequence)
        ):
            raise RetrievalResponseError(
                "chunks must be a sequence."
            )

        normalized_chunks = tuple(
            self.chunks,
        )

        if not all(
            isinstance(
                chunk,
                RetrievedStudyChunk,
            )
            for chunk in normalized_chunks
        ):
            raise RetrievalResponseError(
                "Every result item must be a "
                "RetrievedStudyChunk."
            )

        embedding_provider = _validated_metadata_text(
            self.embedding_provider,
            field_name="embedding_provider",
        )

        embedding_model = _validated_metadata_text(
            self.embedding_model,
            field_name="embedding_model",
        )

        if (
            isinstance(self.embedding_dimensions, bool)
            or not isinstance(self.embedding_dimensions, int)
            or self.embedding_dimensions <= 0
        ):
            raise RetrievalResponseError(
                "embedding_dimensions must be a "
                "positive integer."
            )

        object.__setattr__(
            self,
            "chunks",
            normalized_chunks,
        )
        object.__setattr__(
            self,
            "embedding_provider",
            embedding_provider,
        )
        object.__setattr__(
            self,
            "embedding_model",
            embedding_model,
        )

    @property
    def outcome(self) -> RetrievalOutcome:
        """Return matches or no_context."""

        if self.chunks:
            return RetrievalOutcome.MATCHES

        return RetrievalOutcome.NO_CONTEXT

    @property
    def context_available(self) -> bool:
        """Return whether usable study context exists."""

        return bool(
            self.chunks,
        )

    @property
    def retrieved_count(self) -> int:
        """Return the number of retrieved chunks."""

        return len(
            self.chunks,
        )

    @property
    def no_context_message(self) -> str | None:
        """Return a safe message when retrieval found nothing."""

        if self.chunks:
            return None

        return NO_CONTEXT_MESSAGE


class RetrievalOrchestrationService:
    """Embed a question and retrieve relevant study chunks."""

    def __init__(
        self,
        *,
        query_embedding_service: QueryEmbeddingServiceProtocol,
        retrieval_persistence: RetrievalPersistence,
    ) -> None:
        self._query_embedding_service = (
            query_embedding_service
        )
        self._retrieval_persistence = (
            retrieval_persistence
        )

    async def retrieve(
        self,
        request: RetrievalOrchestrationRequest,
    ) -> RetrievalOrchestrationResult:
        """Generate a query vector and retrieve study chunks."""

        if not isinstance(
            request,
            RetrievalOrchestrationRequest,
        ):
            raise RetrievalValidationError(
                "request must be a "
                "RetrievalOrchestrationRequest."
            )

        embedding_result = (
            await self._query_embedding_service.embed_query(
                request.question,
            )
        )

        if not isinstance(
            embedding_result,
            QueryEmbeddingResult,
        ):
            raise RetrievalResponseError(
                "The query-embedding service returned "
                "an invalid result."
            )

        retrieval_request = RetrievalRequest(
            user_id=request.user_id,
            query_embedding=embedding_result.embedding,
            match_count=request.match_count,
            similarity_threshold=(
                request.similarity_threshold
            ),
            study_file_id=request.study_file_id,
            subject_id=request.subject_id,
        )

        retrieval_result = (
            await self._retrieval_persistence.search(
                retrieval_request,
            )
        )

        if not isinstance(
            retrieval_result,
            RetrievalResult,
        ):
            raise RetrievalResponseError(
                "The retrieval persistence layer returned "
                "an invalid result."
            )

        if retrieval_result.request != retrieval_request:
            raise RetrievalResponseError(
                "The retrieval response does not match "
                "the generated request."
            )

        return RetrievalOrchestrationResult(
            request=request,
            chunks=retrieval_result.chunks,
            embedding_provider=embedding_result.provider,
            embedding_model=(
                embedding_result.embedding_model
            ),
            embedding_dimensions=(
                embedding_result.embedding_dimensions
            ),
        )

    async def aclose(self) -> None:
        """Close the owned query-embedding service if supported."""

        close_method = getattr(
            self._query_embedding_service,
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


def _required_uuid(
    value: object,
    *,
    field_name: str,
) -> UUID:
    if isinstance(
        value,
        UUID,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        try:
            return UUID(
                value,
            )
        except ValueError as exc:
            raise RetrievalValidationError(
                f"{field_name} must be a valid UUID."
            ) from exc

    raise RetrievalValidationError(
        f"{field_name} must be a UUID."
    )


def _optional_uuid(
    value: object,
    *,
    field_name: str,
) -> UUID | None:
    if value is None:
        return None

    return _required_uuid(
        value,
        field_name=field_name,
    )


def _validated_question(
    value: object,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise RetrievalValidationError(
            "question must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise RetrievalValidationError(
            "question must not be empty."
        )

    return normalized


def _validated_match_count(
    value: object,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
    ):
        raise RetrievalValidationError(
            "match_count must be an integer."
        )

    if (
        value < MIN_RETRIEVAL_MATCH_COUNT
        or value > MAX_RETRIEVAL_MATCH_COUNT
    ):
        raise RetrievalValidationError(
            "match_count must be between "
            f"{MIN_RETRIEVAL_MATCH_COUNT} and "
            f"{MAX_RETRIEVAL_MATCH_COUNT}."
        )

    return value


def _validated_threshold(
    value: object,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
    ):
        raise RetrievalValidationError(
            "similarity_threshold must be numeric."
        )

    number = float(
        value,
    )

    if not isfinite(
        number,
    ):
        raise RetrievalValidationError(
            "similarity_threshold must be finite."
        )

    if number < 0.0 or number > 1.0:
        raise RetrievalValidationError(
            "similarity_threshold must be between "
            "0.0 and 1.0."
        )

    return number


def _validated_metadata_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise RetrievalResponseError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise RetrievalResponseError(
            f"{field_name} must not be empty."
        )

    return normalized