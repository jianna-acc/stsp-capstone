# File: /backend/app/services/flashcard_source_loader.py
# Purpose: Loads complete ordered study-material chunks for
# file-level and subject-level Flashcard generation.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.schemas.flashcard import (
    FlashcardGenerateRequest,
    FlashcardLocatorType,
    FlashcardScopeType,
    FlashcardSource,
)
from app.services.flashcard_errors import (
    FlashcardSourceNotFoundError,
    FlashcardSourceUnavailableError,
)


@dataclass(
    frozen=True,
    slots=True,
)
class FlashcardSourceChunk:
    """One ordered source-aware chunk used for Flashcards."""

    study_file_id: UUID
    source_name: str
    chunk_index: int
    content: str
    locator_type: FlashcardLocatorType | None = None
    locator_label: str | None = None

    def __post_init__(
        self,
    ) -> None:
        """Normalize and validate one Flashcard source chunk."""

        normalized_source_name = (
            self.source_name.strip()
        )

        normalized_content = (
            self.content.strip()
        )

        if not normalized_source_name:
            raise FlashcardSourceUnavailableError(
                "Flashcard source name must not be empty.",
            )

        if (
            isinstance(
                self.chunk_index,
                bool,
            )
            or not isinstance(
                self.chunk_index,
                int,
            )
            or self.chunk_index < 0
        ):
            raise FlashcardSourceUnavailableError(
                "Flashcard source chunk index is invalid.",
            )

        if not normalized_content:
            raise FlashcardSourceUnavailableError(
                "Flashcard source chunk content must not be empty.",
            )

        normalized_locator_label = (
            self.locator_label.strip()
            if self.locator_label is not None
            else None
        )

        object.__setattr__(
            self,
            "source_name",
            normalized_source_name,
        )

        object.__setattr__(
            self,
            "content",
            normalized_content,
        )

        object.__setattr__(
            self,
            "locator_label",
            normalized_locator_label or None,
        )


@dataclass(
    frozen=True,
    slots=True,
)
class FlashcardSourceBundle:
    """Complete validated material for one Flashcard request."""

    user_id: UUID
    subject_id: UUID
    scope_type: FlashcardScopeType
    study_file_id: UUID | None
    chunks: tuple[
        FlashcardSourceChunk,
        ...,
    ]

    def __post_init__(
        self,
    ) -> None:
        """Ensure source bundle matches its requested scope."""

        if not self.chunks:
            raise FlashcardSourceNotFoundError(
                "No Flashcard source chunks were available.",
            )

        if (
            self.scope_type
            is FlashcardScopeType.FILE
            and self.study_file_id is None
        ):
            raise FlashcardSourceUnavailableError(
                "A file Flashcard source bundle requires "
                "study_file_id.",
            )

        if (
            self.scope_type
            is FlashcardScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise FlashcardSourceUnavailableError(
                "A subject Flashcard source bundle cannot "
                "target one study file.",
            )

    @property
    def chunk_count(
        self,
    ) -> int:
        """Return total loaded source-chunk count."""

        return len(
            self.chunks,
        )

    @property
    def file_count(
        self,
    ) -> int:
        """Return number of distinct source files."""

        return len(
            {
                chunk.study_file_id
                for chunk in self.chunks
            },
        )

    @property
    def character_count(
        self,
    ) -> int:
        """Return total usable source characters."""

        return sum(
            len(
                chunk.content,
            )
            for chunk in self.chunks
        )

    @property
    def sources(
        self,
    ) -> tuple[
        FlashcardSource,
        ...,
    ]:
        """Return safe source metadata for persistence."""

        return tuple(
            FlashcardSource(
                study_file_id=chunk.study_file_id,
                source_name=chunk.source_name,
                chunk_index=chunk.chunk_index,
                locator_type=chunk.locator_type,
                locator_label=chunk.locator_label,
            )
            for chunk in self.chunks
        )


class FlashcardSourceAdminProtocol(
    Protocol,
):
    """Trusted operations required by Flashcard source loading."""

    async def get_study_file(
        self,
        file_id: UUID,
    ) -> Mapping[
        str,
        object,
    ] | None:
        """Return one study-file row."""

    async def list_ready_study_files_for_subject(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
    ) -> Sequence[
        Mapping[
            str,
            object,
        ]
    ]:
        """Return ready files belonging to one subject."""

    async def list_study_file_chunks(
        self,
        *,
        user_id: UUID,
        study_file_id: UUID,
    ) -> Sequence[
        Mapping[
            str,
            object,
        ]
    ]:
        """Return source chunks belonging to one study file."""


class FlashcardSourceLoader:
    """Load complete owned study material for Flashcards."""

    def __init__(
        self,
        admin_service: FlashcardSourceAdminProtocol,
    ) -> None:
        self._admin = admin_service

    async def load(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> FlashcardSourceBundle:
        """Load source material according to requested scope."""

        if (
            request.scope_type
            is FlashcardScopeType.FILE
        ):
            return await self._load_file_scope(
                user_id=user_id,
                request=request,
            )

        return await self._load_subject_scope(
            user_id=user_id,
            request=request,
        )

    async def _load_file_scope(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> FlashcardSourceBundle:
        """Load all chunks from one selected owned file."""

        study_file_id = request.study_file_id

        if study_file_id is None:
            raise FlashcardSourceUnavailableError(
                "File Flashcard request is missing "
                "study_file_id.",
            )

        study_file = await self._admin.get_study_file(
            study_file_id,
        )

        if study_file is None:
            raise FlashcardSourceNotFoundError(
                "The selected study file was not found.",
            )

        self._validate_file_row(
            row=study_file,
            expected_user_id=user_id,
            expected_subject_id=request.subject_id,
            expected_file_id=study_file_id,
        )

        chunks = await self._load_chunks_for_file(
            user_id=user_id,
            file_row=study_file,
        )

        return FlashcardSourceBundle(
            user_id=user_id,
            subject_id=request.subject_id,
            scope_type=request.scope_type,
            study_file_id=study_file_id,
            chunks=chunks,
        )

    async def _load_subject_scope(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> FlashcardSourceBundle:
        """Load every ready owned file within one subject."""

        file_rows = (
            await self._admin.list_ready_study_files_for_subject(
                user_id=user_id,
                subject_id=request.subject_id,
            )
        )

        if not file_rows:
            raise FlashcardSourceNotFoundError(
                "The selected subject has no ready study files.",
            )

        combined_chunks: list[
            FlashcardSourceChunk
        ] = []

        for row in file_rows:
            self._validate_file_row(
                row=row,
                expected_user_id=user_id,
                expected_subject_id=request.subject_id,
            )

            file_chunks = await self._load_chunks_for_file(
                user_id=user_id,
                file_row=row,
            )

            combined_chunks.extend(
                file_chunks,
            )

        return FlashcardSourceBundle(
            user_id=user_id,
            subject_id=request.subject_id,
            scope_type=request.scope_type,
            study_file_id=None,
            chunks=tuple(
                combined_chunks,
            ),
        )

    async def _load_chunks_for_file(
        self,
        *,
        user_id: UUID,
        file_row: Mapping[
            str,
            object,
        ],
    ) -> tuple[
        FlashcardSourceChunk,
        ...,
    ]:
        """Load and validate every chunk from one ready file."""

        study_file_id = self._required_uuid(
            file_row,
            "id",
        )

        source_name = self._required_text(
            file_row,
            "original_filename",
        )

        chunk_rows = (
            await self._admin.list_study_file_chunks(
                user_id=user_id,
                study_file_id=study_file_id,
            )
        )

        if not chunk_rows:
            raise FlashcardSourceUnavailableError(
                "A ready study file has no source chunks.",
            )

        parsed_chunks = [
            self._parse_chunk(
                row=row,
                expected_file_id=study_file_id,
                source_name=source_name,
            )
            for row in chunk_rows
        ]

        parsed_chunks.sort(
            key=lambda chunk: chunk.chunk_index,
        )

        self._validate_contiguous_indices(
            parsed_chunks,
        )

        return tuple(
            parsed_chunks,
        )

    def _validate_file_row(
        self,
        *,
        row: Mapping[
            str,
            object,
        ],
        expected_user_id: UUID,
        expected_subject_id: UUID,
        expected_file_id: UUID | None = None,
    ) -> None:
        """Validate file ownership, subject, and ready state."""

        file_id = self._required_uuid(
            row,
            "id",
        )

        user_id = self._required_uuid(
            row,
            "user_id",
        )

        subject_id = self._required_uuid(
            row,
            "subject_id",
        )

        processing_status = self._required_text(
            row,
            "processing_status",
        )

        if (
            expected_file_id is not None
            and file_id != expected_file_id
        ):
            raise FlashcardSourceUnavailableError(
                "The loaded study-file ID is inconsistent.",
            )

        if user_id != expected_user_id:
            raise FlashcardSourceNotFoundError(
                "The selected study file was not found.",
            )

        if subject_id != expected_subject_id:
            raise FlashcardSourceNotFoundError(
                "The selected study file was not found "
                "in the requested subject.",
            )

        if processing_status != "ready":
            raise FlashcardSourceUnavailableError(
                "Flashcard generation requires ready "
                "study files.",
            )

        self._required_text(
            row,
            "original_filename",
        )

    def _parse_chunk(
        self,
        *,
        row: Mapping[
            str,
            object,
        ],
        expected_file_id: UUID,
        source_name: str,
    ) -> FlashcardSourceChunk:
        """Parse one persisted source-aware chunk."""

        study_file_id = self._required_uuid(
            row,
            "study_file_id",
        )

        if study_file_id != expected_file_id:
            raise FlashcardSourceUnavailableError(
                "A Flashcard source chunk belongs to "
                "an unexpected study file.",
            )

        chunk_index = row.get(
            "chunk_index",
        )

        if (
            isinstance(
                chunk_index,
                bool,
            )
            or not isinstance(
                chunk_index,
                int,
            )
            or chunk_index < 0
        ):
            raise FlashcardSourceUnavailableError(
                "A Flashcard source chunk has an "
                "invalid index.",
            )

        content = self._required_text(
            row,
            "content",
        )

        locator_type = self._optional_locator_type(
            row.get(
                "locator_type",
            )
        )

        locator_label = self._optional_text(
            row.get(
                "locator_label",
            )
        )

        return FlashcardSourceChunk(
            study_file_id=study_file_id,
            source_name=source_name,
            chunk_index=chunk_index,
            content=content,
            locator_type=locator_type,
            locator_label=locator_label,
        )

    def _validate_contiguous_indices(
        self,
        chunks: Sequence[
            FlashcardSourceChunk,
        ],
    ) -> None:
        """Require deterministic complete chunk ordering."""

        expected_indices = list(
            range(
                len(
                    chunks,
                )
            )
        )

        actual_indices = [
            chunk.chunk_index
            for chunk in chunks
        ]

        if actual_indices != expected_indices:
            raise FlashcardSourceUnavailableError(
                "Study-file source chunks are incomplete "
                "or out of sequence.",
            )

    def _required_uuid(
        self,
        row: Mapping[
            str,
            object,
        ],
        field_name: str,
    ) -> UUID:
        """Read one required UUID value."""

        try:
            return UUID(
                str(
                    row[
                        field_name
                    ],
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise FlashcardSourceUnavailableError(
                f"Flashcard source {field_name} is invalid.",
            ) from exc

    def _required_text(
        self,
        row: Mapping[
            str,
            object,
        ],
        field_name: str,
    ) -> str:
        """Read one required non-empty text value."""

        value = row.get(
            field_name,
        )

        if not isinstance(
            value,
            str,
        ):
            raise FlashcardSourceUnavailableError(
                f"Flashcard source {field_name} is invalid.",
            )

        normalized = value.strip()

        if not normalized:
            raise FlashcardSourceUnavailableError(
                f"Flashcard source {field_name} is empty.",
            )

        return normalized

    def _optional_text(
        self,
        value: object,
    ) -> str | None:
        """Normalize optional locator text."""

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise FlashcardSourceUnavailableError(
                "Flashcard source locator label is invalid.",
            )

        normalized = value.strip()

        return normalized or None

    def _optional_locator_type(
        self,
        value: object,
    ) -> FlashcardLocatorType | None:
        """Parse optional source locator type."""

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise FlashcardSourceUnavailableError(
                "Flashcard source locator type is invalid.",
            )

        try:
            return FlashcardLocatorType(
                value.strip(),
            )

        except ValueError as exc:
            raise FlashcardSourceUnavailableError(
                "Flashcard source locator type is unsupported.",
            ) from exc