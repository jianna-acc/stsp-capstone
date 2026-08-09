# File: /backend/app/schemas/flashcard_summary.py
# Purpose: Defines lightweight Flashcard deck metadata returned
# when listing a student's saved Flashcard decks.

from __future__ import annotations

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.flashcard import (
    MAX_FLASHCARD_MODEL_CHARACTERS,
    MAX_FLASHCARD_SOURCES,
    MAX_FLASHCARD_TITLE_CHARACTERS,
    MAX_FLASHCARDS_PER_DECK,
    MIN_FLASHCARDS_PER_DECK,
    FlashcardScopeType,
    FlashcardSource,
)


class FlashcardDeckSummary(
    BaseModel,
):
    """Lightweight metadata for one saved Flashcard deck."""

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
        mode="before",
    )
    @classmethod
    def normalize_text(
        cls,
        value: object,
    ) -> object:
        """Trim stored summary text before validation."""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        return value

    @model_validator(
        mode="after",
    )
    def validate_scope(
        self,
    ) -> Self:
        """Keep subject/file scope internally consistent."""

        if (
            self.scope_type
            is FlashcardScopeType.FILE
            and self.study_file_id is None
        ):
            raise ValueError(
                "File-scope Flashcard decks require "
                "a study file.",
            )

        if (
            self.scope_type
            is FlashcardScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ValueError(
                "Subject-scope Flashcard decks cannot "
                "store a study file.",
            )

        return self

class FlashcardListResponse(
    BaseModel,
):
    """Saved Flashcard decks returned by the list endpoint."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    items: tuple[
        FlashcardDeckSummary,
        ...,
    ] = ()