# File: /backend/app/schemas/rag.py

from __future__ import annotations

from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

DEFAULT_RAG_MATCH_COUNT = 8
MIN_RAG_MATCH_COUNT = 1
MAX_RAG_MATCH_COUNT = 20

DEFAULT_RAG_SIMILARITY_THRESHOLD = 0.60

MAX_RAG_QUESTION_CHARACTERS = 4_000
MAX_RAG_SOURCE_NAME_CHARACTERS = 512
MAX_RAG_ERROR_CODE_CHARACTERS = 128
MAX_RAG_ERROR_MESSAGE_CHARACTERS = 500


class RagAnswerOutcome(StrEnum):
    """Public outcomes returned by the protected RAG endpoint."""

    ANSWERED = "answered"
    NO_CONTEXT = "no_context"


class RagAnswerRequest(BaseModel):
    """Authenticated student request for one grounded answer."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    question: str = Field(
        min_length=1,
        max_length=MAX_RAG_QUESTION_CHARACTERS,
        description=(
            "Question to answer using the authenticated "
            "student's eligible study materials."
        ),
    )

    study_file_id: UUID | None = Field(
        default=None,
        description=(
            "Optional study-file filter owned by the "
            "authenticated student."
        ),
    )

    subject_id: UUID | None = Field(
        default=None,
        description=(
            "Optional subject filter owned by the "
            "authenticated student."
        ),
    )

    match_count: int = Field(
        default=DEFAULT_RAG_MATCH_COUNT,
        ge=MIN_RAG_MATCH_COUNT,
        le=MAX_RAG_MATCH_COUNT,
        description=(
            "Maximum number of study chunks to retrieve."
        ),
    )

    similarity_threshold: float = Field(
        default=DEFAULT_RAG_SIMILARITY_THRESHOLD,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum cosine-similarity score accepted "
            "during retrieval."
        ),
    )

    @field_validator(
        "question",
    )
    @classmethod
    def normalize_question(
        cls,
        value: str,
    ) -> str:
        """Trim and validate the student question."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "question must not be empty."
            )

        return normalized


class RagSourceResponse(BaseModel):
    """Safe source metadata exposed to the authenticated student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    source_number: int = Field(
        ge=1,
        le=MAX_RAG_MATCH_COUNT,
        description=(
            "One-based source number used by answer citations."
        ),
    )

    source_name: str = Field(
        min_length=1,
        max_length=MAX_RAG_SOURCE_NAME_CHARACTERS,
        description=(
            "Display name of the uploaded study material."
        ),
    )

    chunk_index: int = Field(
        ge=0,
        description=(
            "Zero-based chunk position inside the indexed file."
        ),
    )

    similarity_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Retrieval similarity score for this source."
        ),
    )

    @field_validator(
        "source_name",
    )
    @classmethod
    def normalize_source_name(
        cls,
        value: str,
    ) -> str:
        """Trim and validate the source display name."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "source_name must not be empty."
            )

        return normalized


class RagAnswerResponse(BaseModel):
    """Safe grounded-answer response returned by the API."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    outcome: RagAnswerOutcome = Field(
        description=(
            "Whether the request was answered or had "
            "no relevant study context."
        ),
    )

    answer: str = Field(
        min_length=1,
        description=(
            "Grounded answer or approved no-context message."
        ),
    )

    sources: tuple[
        RagSourceResponse,
        ...,
    ] = Field(
        default=(),
        description=(
            "Safe source references used by the answer."
        ),
    )

    retrieved_count: int = Field(
        ge=0,
        le=MAX_RAG_MATCH_COUNT,
        description=(
            "Number of chunks returned by retrieval."
        ),
    )

    source_count: int = Field(
        ge=0,
        le=MAX_RAG_MATCH_COUNT,
        description=(
            "Number of source references preserved "
            "in the response."
        ),
    )

    context_available: bool = Field(
        description=(
            "Whether eligible study context was available."
        ),
    )

    @field_validator(
        "answer",
    )
    @classmethod
    def normalize_answer(
        cls,
        value: str,
    ) -> str:
        """Trim and validate the answer text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "answer must not be empty."
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_consistency(
        self,
    ) -> Self:
        """Ensure the outcome and source metadata agree."""

        source_numbers = [
            source.source_number
            for source in self.sources
        ]

        expected_source_numbers = list(
            range(
                1,
                len(self.sources) + 1,
            )
        )

        if source_numbers != expected_source_numbers:
            raise ValueError(
                "Source numbers must be consecutive "
                "and begin at one."
            )

        if self.source_count != len(
            self.sources,
        ):
            raise ValueError(
                "source_count must match the number "
                "of sources."
            )

        if self.source_count > self.retrieved_count:
            raise ValueError(
                "source_count cannot exceed retrieved_count."
            )

        if self.outcome == RagAnswerOutcome.ANSWERED:
            self._validate_answered_response()
        else:
            self._validate_no_context_response()

        return self

    def _validate_answered_response(
        self,
    ) -> None:
        if not self.context_available:
            raise ValueError(
                "An answered response requires context."
            )

        if not self.sources:
            raise ValueError(
                "An answered response requires sources."
            )

        if self.retrieved_count <= 0:
            raise ValueError(
                "An answered response requires retrieved chunks."
            )

    def _validate_no_context_response(
        self,
    ) -> None:
        if self.context_available:
            raise ValueError(
                "A no-context response cannot report context."
            )

        if self.sources:
            raise ValueError(
                "A no-context response cannot contain sources."
            )

        if self.source_count != 0:
            raise ValueError(
                "A no-context response must have "
                "source_count equal to zero."
            )

        if self.retrieved_count != 0:
            raise ValueError(
                "A no-context response must have "
                "retrieved_count equal to zero."
            )


class RagApiErrorResponse(BaseModel):
    """Stable error body for controlled RAG endpoint failures."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    error_code: str = Field(
        min_length=1,
        max_length=MAX_RAG_ERROR_CODE_CHARACTERS,
        description=(
            "Stable machine-readable RAG failure code."
        ),
    )

    message: str = Field(
        min_length=1,
        max_length=MAX_RAG_ERROR_MESSAGE_CHARACTERS,
        description=(
            "Safe student-facing explanation of the failure."
        ),
    )

    @field_validator(
        "error_code",
        "message",
    )
    @classmethod
    def normalize_error_text(
        cls,
        value: str,
    ) -> str:
        """Trim and validate controlled error text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Error fields must not be empty."
            )

        return normalized
