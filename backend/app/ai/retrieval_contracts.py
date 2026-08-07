# File: /backend/app/ai/retrieval_contracts.py

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from math import isfinite
from numbers import Real
from typing import Any
from uuid import UUID

RETRIEVAL_EMBEDDING_DIMENSIONS = 768

DEFAULT_RETRIEVAL_MATCH_COUNT = 8
MIN_RETRIEVAL_MATCH_COUNT = 1
MAX_RETRIEVAL_MATCH_COUNT = 20

DEFAULT_RETRIEVAL_SIMILARITY_THRESHOLD = 0.60

NO_CONTEXT_MESSAGE = (
    "No study-material chunks met the current retrieval filters "
    "and similarity threshold."
)


class RetrievalFailureCode(StrEnum):
    """Stable failure codes for retrieval operations."""

    VALIDATION_FAILED = "RETRIEVAL_VALIDATION_FAILED"
    REQUEST_FAILED = "RETRIEVAL_REQUEST_FAILED"
    RESPONSE_FAILED = "RETRIEVAL_RESPONSE_FAILED"


class RetrievalOutcome(StrEnum):
    """Possible successful retrieval outcomes."""

    MATCHES = "matches"
    NO_CONTEXT = "no_context"


class RetrievalError(RuntimeError):
    """Base exception with a stable retrieval failure code."""

    def __init__(
        self,
        message: str,
        *,
        error_code: RetrievalFailureCode,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code


class RetrievalValidationError(RetrievalError):
    """Raised when retrieval input is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            error_code=RetrievalFailureCode.VALIDATION_FAILED,
        )


class RetrievalRequestError(RetrievalError):
    """Raised when the Supabase RPC request fails."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            error_code=RetrievalFailureCode.REQUEST_FAILED,
        )


class RetrievalResponseError(RetrievalError):
    """Raised when the RPC response is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            error_code=RetrievalFailureCode.RESPONSE_FAILED,
        )


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    """Validated request for search_study_file_ai_chunks."""

    user_id: UUID
    query_embedding: tuple[float, ...]
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
            error_type=RetrievalValidationError,
        )

        query_embedding = _validated_embedding(
            self.query_embedding,
        )

        match_count = _validated_integer(
            self.match_count,
            field_name="match_count",
            minimum=MIN_RETRIEVAL_MATCH_COUNT,
            maximum=MAX_RETRIEVAL_MATCH_COUNT,
            error_type=RetrievalValidationError,
        )

        similarity_threshold = _validated_number(
            self.similarity_threshold,
            field_name="similarity_threshold",
            minimum=0.0,
            maximum=1.0,
            error_type=RetrievalValidationError,
        )

        study_file_id = _optional_uuid(
            self.study_file_id,
            field_name="study_file_id",
            error_type=RetrievalValidationError,
        )

        subject_id = _optional_uuid(
            self.subject_id,
            field_name="subject_id",
            error_type=RetrievalValidationError,
        )

        object.__setattr__(
            self,
            "user_id",
            user_id,
        )
        object.__setattr__(
            self,
            "query_embedding",
            query_embedding,
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

    def to_rpc_parameters(self) -> dict[str, object]:
        """Return the exact parameter names expected by the RPC."""

        return {
            "p_user_id": str(self.user_id),
            "p_query_embedding": list(
                self.query_embedding,
            ),
            "p_match_count": self.match_count,
            "p_similarity_threshold": (
                self.similarity_threshold
            ),
            "p_study_file_id": (
                str(self.study_file_id)
                if self.study_file_id is not None
                else None
            ),
            "p_subject_id": (
                str(self.subject_id)
                if self.subject_id is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class RetrievedStudyChunk:
    """One validated row returned by the retrieval RPC."""

    chunk_id: UUID
    study_file_id: UUID
    subject_id: UUID | None
    source_name: str
    chunk_index: int
    content: str
    start_offset: int
    end_offset: int
    chunk_metadata: Mapping[str, Any]
    embedding_model: str
    similarity_score: float

    @classmethod
    def from_rpc_row(
        cls,
        row: Mapping[str, object],
    ) -> RetrievedStudyChunk:
        """Create a chunk from an RPC response row."""

        if not isinstance(row, Mapping):
            raise RetrievalResponseError(
                "Each retrieval row must be a mapping."
            )

        required_columns = {
            "chunk_id",
            "study_file_id",
            "subject_id",
            "source_name",
            "chunk_index",
            "content",
            "start_offset",
            "end_offset",
            "chunk_metadata",
            "embedding_model",
            "similarity_score",
        }

        missing_columns = sorted(
            required_columns.difference(
                row.keys(),
            )
        )

        if missing_columns:
            raise RetrievalResponseError(
                "Retrieval row is missing required columns: "
                + ", ".join(missing_columns)
            )

        chunk_id = _required_uuid(
            row["chunk_id"],
            field_name="chunk_id",
            error_type=RetrievalResponseError,
        )

        study_file_id = _required_uuid(
            row["study_file_id"],
            field_name="study_file_id",
            error_type=RetrievalResponseError,
        )

        subject_id = _optional_uuid(
            row["subject_id"],
            field_name="subject_id",
            error_type=RetrievalResponseError,
        )

        source_name = _validated_text(
            row["source_name"],
            field_name="source_name",
            preserve_whitespace=False,
        )

        chunk_index = _validated_integer(
            row["chunk_index"],
            field_name="chunk_index",
            minimum=0,
            maximum=None,
            error_type=RetrievalResponseError,
        )

        content = _validated_text(
            row["content"],
            field_name="content",
            preserve_whitespace=True,
        )

        start_offset = _validated_integer(
            row["start_offset"],
            field_name="start_offset",
            minimum=0,
            maximum=None,
            error_type=RetrievalResponseError,
        )

        end_offset = _validated_integer(
            row["end_offset"],
            field_name="end_offset",
            minimum=0,
            maximum=None,
            error_type=RetrievalResponseError,
        )

        if end_offset < start_offset:
            raise RetrievalResponseError(
                "end_offset must be greater than or equal to "
                "start_offset."
            )

        chunk_metadata = row["chunk_metadata"]

        if not isinstance(chunk_metadata, Mapping):
            raise RetrievalResponseError(
                "chunk_metadata must be a JSON object."
            )

        embedding_model = _validated_text(
            row["embedding_model"],
            field_name="embedding_model",
            preserve_whitespace=False,
        )

        similarity_score = _validated_number(
            row["similarity_score"],
            field_name="similarity_score",
            minimum=0.0,
            maximum=1.0,
            error_type=RetrievalResponseError,
        )

        return cls(
            chunk_id=chunk_id,
            study_file_id=study_file_id,
            subject_id=subject_id,
            source_name=source_name,
            chunk_index=chunk_index,
            content=content,
            start_offset=start_offset,
            end_offset=end_offset,
            chunk_metadata=dict(
                chunk_metadata,
            ),
            embedding_model=embedding_model,
            similarity_score=similarity_score,
        )


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Validated retrieval result with normal no-context handling."""

    request: RetrievalRequest
    chunks: tuple[RetrievedStudyChunk, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.request,
            RetrievalRequest,
        ):
            raise RetrievalResponseError(
                "request must be a RetrievalRequest."
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

        if len(normalized_chunks) > self.request.match_count:
            raise RetrievalResponseError(
                "The response exceeded match_count."
            )

        chunk_ids = [
            chunk.chunk_id
            for chunk in normalized_chunks
        ]

        if len(chunk_ids) != len(
            set(chunk_ids)
        ):
            raise RetrievalResponseError(
                "The response contains duplicate chunks."
            )

        for current, following in pairwise(
            normalized_chunks,
        ):

            if (
                current.similarity_score
                < following.similarity_score
            ):
                raise RetrievalResponseError(
                    "Chunks must be ordered by descending "
                    "similarity_score."
                )

        for chunk in normalized_chunks:
            if (
                self.request.study_file_id is not None
                and chunk.study_file_id
                != self.request.study_file_id
            ):
                raise RetrievalResponseError(
                    "A chunk does not match study_file_id."
                )

            if (
                self.request.subject_id is not None
                and chunk.subject_id
                != self.request.subject_id
            ):
                raise RetrievalResponseError(
                    "A chunk does not match subject_id."
                )

        object.__setattr__(
            self,
            "chunks",
            normalized_chunks,
        )

    @property
    def outcome(self) -> RetrievalOutcome:
        """Return matches or no_context."""

        if self.chunks:
            return RetrievalOutcome.MATCHES

        return RetrievalOutcome.NO_CONTEXT

    @property
    def context_available(self) -> bool:
        """Return whether at least one chunk was retrieved."""

        return bool(
            self.chunks,
        )

    @property
    def no_context_message(self) -> str | None:
        """Return a safe message only when no context exists."""

        if self.chunks:
            return None

        return NO_CONTEXT_MESSAGE


def _required_uuid(
    value: object,
    *,
    field_name: str,
    error_type: type[RetrievalError],
) -> UUID:
    if isinstance(value, UUID):
        return value

    if isinstance(value, str):
        try:
            return UUID(
                value,
            )
        except ValueError as exc:
            raise error_type(
                f"{field_name} must be a valid UUID."
            ) from exc

    raise error_type(
        f"{field_name} must be a UUID."
    )


def _optional_uuid(
    value: object,
    *,
    field_name: str,
    error_type: type[RetrievalError],
) -> UUID | None:
    if value is None:
        return None

    return _required_uuid(
        value,
        field_name=field_name,
        error_type=error_type,
    )


def _validated_embedding(
    value: object,
) -> tuple[float, ...]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
    ):
        raise RetrievalValidationError(
            "query_embedding must be a numeric sequence."
        )

    if len(value) != RETRIEVAL_EMBEDDING_DIMENSIONS:
        raise RetrievalValidationError(
            "query_embedding must contain exactly "
            f"{RETRIEVAL_EMBEDDING_DIMENSIONS} values."
        )

    normalized: list[float] = []

    for index, item in enumerate(
        value,
    ):
        if (
            isinstance(item, bool)
            or not isinstance(item, Real)
        ):
            raise RetrievalValidationError(
                "query_embedding values must be numeric; "
                f"invalid value at index {index}."
            )

        number = float(
            item,
        )

        if not isfinite(
            number,
        ):
            raise RetrievalValidationError(
                "query_embedding values must be finite; "
                f"invalid value at index {index}."
            )

        normalized.append(
            number,
        )

    if not any(
        number != 0.0
        for number in normalized
    ):
        raise RetrievalValidationError(
            "query_embedding must not be a zero vector."
        )

    return tuple(
        normalized,
    )


def _validated_integer(
    value: object,
    *,
    field_name: str,
    minimum: int,
    maximum: int | None,
    error_type: type[RetrievalError],
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
    ):
        raise error_type(
            f"{field_name} must be an integer."
        )

    if value < minimum:
        raise error_type(
            f"{field_name} must be at least {minimum}."
        )

    if maximum is not None and value > maximum:
        raise error_type(
            f"{field_name} must be at most {maximum}."
        )

    return value


def _validated_number(
    value: object,
    *,
    field_name: str,
    minimum: float,
    maximum: float,
    error_type: type[RetrievalError],
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
    ):
        raise error_type(
            f"{field_name} must be numeric."
        )

    number = float(
        value,
    )

    if not isfinite(
        number,
    ):
        raise error_type(
            f"{field_name} must be finite."
        )

    if number < minimum or number > maximum:
        raise error_type(
            f"{field_name} must be between "
            f"{minimum} and {maximum}."
        )

    return number


def _validated_text(
    value: object,
    *,
    field_name: str,
    preserve_whitespace: bool,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise RetrievalResponseError(
            f"{field_name} must be a string."
        )

    normalized = (
        value
        if preserve_whitespace
        else value.strip()
    )

    if not normalized.strip():
        raise RetrievalResponseError(
            f"{field_name} must not be empty."
        )

    return normalized
