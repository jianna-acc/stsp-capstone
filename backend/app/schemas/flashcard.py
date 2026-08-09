# File: /backend/app/schemas/flashcard.py
# Purpose: Defines validated API and persistence schemas for
# generated STUDY AI flashcard decks.

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

MIN_FLASHCARDS_PER_DECK = 5
DEFAULT_FLASHCARDS_PER_DECK = 20
MAX_FLASHCARDS_PER_DECK = 50

MAX_FLASHCARD_TITLE_CHARACTERS = 160
MAX_FLASHCARD_QUESTION_CHARACTERS = 2_000
MAX_FLASHCARD_ANSWER_CHARACTERS = 4_000

MAX_FLASHCARD_SOURCE_NAME_CHARACTERS = 512
MAX_FLASHCARD_LOCATOR_CHARACTERS = 300
MAX_FLASHCARD_MODEL_CHARACTERS = 120

MAX_FLASHCARD_SOURCES = 1_000


class FlashcardScopeType(StrEnum):
    """Supported source scopes for flashcard generation."""

    SUBJECT = "subject"
    FILE = "file"


class FlashcardLocatorType(StrEnum):
    """Supported study-material source locator types."""

    PAGE = "page"
    SLIDE = "slide"
    SHEET = "sheet"
    SECTION = "section"
    DOCUMENT = "document"


class FlashcardItem(BaseModel):
    """One generated flashcard question-and-answer pair."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    question: str = Field(
        min_length=1,
        max_length=MAX_FLASHCARD_QUESTION_CHARACTERS,
    )

    answer: str = Field(
        min_length=1,
        max_length=MAX_FLASHCARD_ANSWER_CHARACTERS,
    )

    @field_validator(
        "question",
        "answer",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str,
    ) -> str:
        """Trim generated flashcard text."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Flashcard text must not be empty.",
            )

        return normalized


class FlashcardContent(BaseModel):
    """Structured generated flashcard content."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    cards: tuple[
        FlashcardItem,
        ...,
    ] = Field(
        min_length=1,
        max_length=MAX_FLASHCARDS_PER_DECK,
    )


class FlashcardSource(BaseModel):
    """Safe study-material source used during generation."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    study_file_id: UUID

    source_name: str = Field(
        min_length=1,
        max_length=MAX_FLASHCARD_SOURCE_NAME_CHARACTERS,
    )

    chunk_index: int = Field(
        ge=0,
    )

    locator_type: FlashcardLocatorType | None = None

    locator_label: str | None = Field(
        default=None,
        max_length=MAX_FLASHCARD_LOCATOR_CHARACTERS,
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
                "Flashcard source name must not be empty.",
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


class FlashcardGenerateRequest(BaseModel):
    """Request to generate and save one flashcard deck."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    scope_type: FlashcardScopeType

    subject_id: UUID

    study_file_id: UUID | None = None

    card_count: int = Field(
        default=DEFAULT_FLASHCARDS_PER_DECK,
        ge=MIN_FLASHCARDS_PER_DECK,
        le=MAX_FLASHCARDS_PER_DECK,
    )

    @model_validator(
        mode="after",
    )
    def validate_scope(
        self,
    ) -> Self:
        """Ensure flashcard scope matches its selected target."""

        if (
            self.scope_type
            == FlashcardScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "Subject flashcards cannot specify "
                "study_file_id.",
            )

        if (
            self.scope_type
            == FlashcardScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "File flashcards require study_file_id.",
            )

        return self


class FlashcardDeckResponse(BaseModel):
    """Saved flashcard deck returned to the student."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: UUID

    subject_id: UUID

    study_file_id: UUID | None = None

    scope_type: FlashcardScopeType

    title: str = Field(
        min_length=1,
        max_length=MAX_FLASHCARD_TITLE_CHARACTERS,
    )

    requested_card_count: int = Field(
        ge=MIN_FLASHCARDS_PER_DECK,
        le=MAX_FLASHCARDS_PER_DECK,
    )

    cards: tuple[
        FlashcardItem,
        ...,
    ] = Field(
        min_length=1,
        max_length=MAX_FLASHCARDS_PER_DECK,
    )

    sources: tuple[
        FlashcardSource,
        ...,
    ] = Field(
        default=(),
        max_length=MAX_FLASHCARD_SOURCES,
    )

    generation_model: str = Field(
        min_length=1,
        max_length=MAX_FLASHCARD_MODEL_CHARACTERS,
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
        """Trim persisted flashcard-deck metadata."""

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Flashcard deck response text "
                "must not be empty.",
            )

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_scope(
        self,
    ) -> Self:
        """Keep saved flashcard scope internally consistent."""

        if (
            self.scope_type
            == FlashcardScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "Subject flashcard deck cannot have "
                "study_file_id.",
            )

        if (
            self.scope_type
            == FlashcardScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "File flashcard deck requires study_file_id.",
            )

        return self

class FlashcardApiErrorResponse(
    BaseModel,
):
    """Safe public error returned by Flashcard endpoints."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    error_code: str = Field(
        min_length=1,
        max_length=120,
    )

    message: str = Field(
        min_length=1,
        max_length=500,
    )