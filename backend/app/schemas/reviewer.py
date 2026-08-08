# File: /backend/app/schemas/reviewer.py
# Purpose: Defines validated API and persistence schemas for
# generated STUDY AI reviewers.

from __future__ import annotations

from datetime import datetime
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

MAX_REVIEWER_TITLE_CHARACTERS = 160
MAX_REVIEWER_OVERVIEW_CHARACTERS = 20_000
MAX_REVIEWER_TOPIC_TITLE_CHARACTERS = 200
MAX_REVIEWER_TOPIC_SUMMARY_CHARACTERS = 20_000
MAX_REVIEWER_KEY_POINT_CHARACTERS = 2_000
MAX_REVIEWER_TERM_CHARACTERS = 300
MAX_REVIEWER_DEFINITION_CHARACTERS = 4_000
MAX_REVIEWER_SOURCE_NAME_CHARACTERS = 512
MAX_REVIEWER_LOCATOR_CHARACTERS = 300
MAX_REVIEWER_MODEL_CHARACTERS = 120

MAX_REVIEWER_TOPICS = 100
MAX_TOPIC_KEY_POINTS = 100
MAX_TOPIC_DEFINITIONS = 100
MAX_REVIEWER_SOURCES = 1_000


class ReviewerScopeType(StrEnum):
    """Supported source scopes for reviewer generation."""

    SUBJECT = "subject"
    FILE = "file"


class ReviewerLength(StrEnum):
    """Supported reviewer detail levels."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ReviewerLocatorType(StrEnum):
    """Supported source locator types."""

    PAGE = "page"
    SLIDE = "slide"
    SHEET = "sheet"
    SECTION = "section"
    DOCUMENT = "document"


class ReviewerDefinition(BaseModel):
    """One important term and its grounded definition."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    term: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_TERM_CHARACTERS,
    )

    definition: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_DEFINITION_CHARACTERS,
    )

    @field_validator(
        "term",
        "definition",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str,
    ) -> str:
        """Trim definition fields."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Definition fields must not be empty."
            )

        return normalized


class ReviewerTopic(BaseModel):
    """One topic contained in a generated reviewer."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    title: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_TOPIC_TITLE_CHARACTERS,
    )

    summary: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_TOPIC_SUMMARY_CHARACTERS,
    )

    key_points: tuple[
        str,
        ...,
    ] = Field(
        min_length=1,
        max_length=MAX_TOPIC_KEY_POINTS,
    )

    definitions: tuple[
        ReviewerDefinition,
        ...,
    ] = Field(
        default=(),
        max_length=MAX_TOPIC_DEFINITIONS,
    )

    @field_validator(
        "title",
        "summary",
    )
    @classmethod
    def normalize_topic_text(
        cls,
        value: str,
    ) -> str:
        """Trim topic text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Topic text must not be empty."
            )

        return normalized

    @field_validator(
        "key_points",
    )
    @classmethod
    def normalize_key_points(
        cls,
        value: tuple[
            str,
            ...,
        ],
    ) -> tuple[
        str,
        ...,
    ]:
        """Trim and validate generated key points."""

        normalized_points = tuple(
            point.strip()
            for point in value
        )

        if any(
            not point
            for point in normalized_points
        ):
            raise ValueError(
                "Reviewer key points must not be empty."
            )

        if any(
            len(point)
            > MAX_REVIEWER_KEY_POINT_CHARACTERS
            for point in normalized_points
        ):
            raise ValueError(
                "A reviewer key point is too long."
            )

        return normalized_points


class ReviewerContent(BaseModel):
    """Structured generated reviewer content."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    overview: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_OVERVIEW_CHARACTERS,
    )

    topics: tuple[
        ReviewerTopic,
        ...,
    ] = Field(
        min_length=1,
        max_length=MAX_REVIEWER_TOPICS,
    )

    @field_validator(
        "overview",
    )
    @classmethod
    def normalize_overview(
        cls,
        value: str,
    ) -> str:
        """Trim reviewer overview."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Reviewer overview must not be empty."
            )

        return normalized


class ReviewerSource(BaseModel):
    """Safe study-material source used during generation."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    study_file_id: UUID

    source_name: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_SOURCE_NAME_CHARACTERS,
    )

    chunk_index: int = Field(
        ge=0,
    )

    locator_type: ReviewerLocatorType | None = None

    locator_label: str | None = Field(
        default=None,
        max_length=MAX_REVIEWER_LOCATOR_CHARACTERS,
    )

    @field_validator(
        "source_name",
    )
    @classmethod
    def normalize_source_name(
        cls,
        value: str,
    ) -> str:
        """Trim source display name."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Reviewer source name must not be empty."
            )

        return normalized

    @field_validator(
        "locator_label",
    )
    @classmethod
    def normalize_locator_label(
        cls,
        value: str | None,
    ) -> str | None:
        """Trim optional source location text."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


class ReviewerGenerateRequest(BaseModel):
    """Request to generate and save one reviewer."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    scope_type: ReviewerScopeType

    subject_id: UUID

    study_file_id: UUID | None = None

    reviewer_length: ReviewerLength = (
        ReviewerLength.MEDIUM
    )

    @model_validator(
        mode="after",
    )
    def validate_scope(
        self,
    ) -> Self:
        """Ensure reviewer scope matches its selected target."""

        if (
            self.scope_type
            == ReviewerScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "A subject reviewer cannot specify "
                "study_file_id."
            )

        if (
            self.scope_type
            == ReviewerScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "A file reviewer requires study_file_id."
            )

        return self


class ReviewerResponse(BaseModel):
    """Saved reviewer returned to the authenticated student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    subject_id: UUID

    study_file_id: UUID | None = None

    scope_type: ReviewerScopeType

    title: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_TITLE_CHARACTERS,
    )

    reviewer_length: ReviewerLength

    content: ReviewerContent

    sources: tuple[
        ReviewerSource,
        ...,
    ] = Field(
        default=(),
        max_length=MAX_REVIEWER_SOURCES,
    )

    generation_model: str = Field(
        min_length=1,
        max_length=MAX_REVIEWER_MODEL_CHARACTERS,
    )

    generation_count: int = Field(
        ge=1,
    )

    generated_at: datetime

    created_at: datetime

    updated_at: datetime

    @field_validator(
        "title",
        "generation_model",
    )
    @classmethod
    def normalize_response_text(
        cls,
        value: str,
    ) -> str:
        """Trim persisted reviewer metadata."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Reviewer response text must not be empty."
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_scope(
        self,
    ) -> Self:
        """Keep saved reviewer scope internally consistent."""

        if (
            self.scope_type
            == ReviewerScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "A subject reviewer cannot have "
                "study_file_id."
            )

        if (
            self.scope_type
            == ReviewerScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "A file reviewer requires study_file_id."
            )

        return self


class ReviewerListResponse(BaseModel):
    """List of reviewers owned by one student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    items: tuple[
        ReviewerResponse,
        ...,
    ] = ()

class ReviewerApiErrorResponse(BaseModel):
    """Safe public error returned by reviewer endpoints."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    error_code: str = Field(
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        min_length=1,
        max_length=300,
    )