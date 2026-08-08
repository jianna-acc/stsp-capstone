# File: /backend/app/services/reviewer_source_loader.py
# Purpose: Loads complete ordered study-material chunks for
# file-level and subject-level reviewer generation.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.schemas.reviewer import (
    ReviewerGenerateRequest,
    ReviewerLocatorType,
    ReviewerScopeType,
)
from app.services.reviewer_errors import (
    ReviewerSourceNotFoundError,
    ReviewerSourceUnavailableError,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ReviewerSourceChunk:
    """One ordered source-aware chunk used by reviewer generation."""

    study_file_id: UUID
    source_name: str
    chunk_index: int
    content: str
    locator_type: ReviewerLocatorType | None = None
    locator_label: str | None = None

    def __post_init__(
        self,
    ) -> None:
        """Normalize and validate one source chunk."""

        normalized_source_name = (
            self.source_name.strip()
        )

        normalized_content = (
            self.content.strip()
        )

        if not normalized_source_name:
            raise ReviewerSourceUnavailableError(
                "Reviewer source name must not be empty.",
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
            raise ReviewerSourceUnavailableError(
                "Reviewer source chunk index is invalid.",
            )

        if not normalized_content:
            raise ReviewerSourceUnavailableError(
                "Reviewer source chunk content must not be empty.",
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
class ReviewerSourceBundle:
    """Complete validated material loaded for one reviewer request."""

    user_id: UUID
    subject_id: UUID
    scope_type: ReviewerScopeType
    study_file_id: UUID | None
    chunks: tuple[
        ReviewerSourceChunk,
        ...,
    ]

    def __post_init__(
        self,
    ) -> None:
        """Ensure the loaded bundle matches its reviewer scope."""

        if not self.chunks:
            raise ReviewerSourceNotFoundError(
                "No reviewer source chunks were available.",
            )

        if (
            self.scope_type
            == ReviewerScopeType.FILE
            and self.study_file_id is None
        ):
            raise ReviewerSourceUnavailableError(
                "A file reviewer source bundle requires "
                "study_file_id.",
            )

        if (
            self.scope_type
            == ReviewerScopeType.SUBJECT
            and self.study_file_id is not None
        ):
            raise ReviewerSourceUnavailableError(
                "A subject reviewer source bundle cannot "
                "target one study file.",
            )

    @property
    def chunk_count(
        self,
    ) -> int:
        """Return loaded source-chunk count."""

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


class ReviewerSourceAdminProtocol(
    Protocol,
):
    """Trusted database operations required by the source loader."""

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
        """Return ready study files belonging to a subject."""

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
        """Return one file's source chunks in document order."""


class ReviewerSourceLoader:
    """Load complete owned study material for reviewer generation."""

    def __init__(
        self,
        admin_service: ReviewerSourceAdminProtocol,
    ) -> None:
        self._admin = admin_service

    async def load(
        self,
        *,
        user_id: UUID,
        request: ReviewerGenerateRequest,
    ) -> ReviewerSourceBundle:
        """Load reviewer material according to the requested scope."""

        if (
            request.scope_type
            == ReviewerScopeType.FILE
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
        request: ReviewerGenerateRequest,
    ) -> ReviewerSourceBundle:
        """Load all source chunks for one selected file."""

        study_file_id = request.study_file_id

        if study_file_id is None:
            raise ReviewerSourceUnavailableError(
                "File reviewer request is missing study_file_id.",
            )

        study_file = await self._admin.get_study_file(
            study_file_id,
        )

        if study_file is None:
            raise ReviewerSourceNotFoundError(
                "The selected study file was not found.",
            )

        self._validate_file_row(
            row=study_file,
            expected_user_id=user_id,
            expected_subject_id=request.subject_id,
            expected_file_id=study_file_id,
        )

        chunks = (
            await self._load_chunks_for_file(
                user_id=user_id,
                file_row=study_file,
            )
        )

        return ReviewerSourceBundle(
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
        request: ReviewerGenerateRequest,
    ) -> ReviewerSourceBundle:
        """Load ordered chunks from every ready file in a subject."""

        file_rows = (
            await self._admin.list_ready_study_files_for_subject(
                user_id=user_id,
                subject_id=request.subject_id,
            )
        )

        if not file_rows:
            raise ReviewerSourceNotFoundError(
                "The selected subject has no ready study files.",
            )

        combined_chunks: list[
            ReviewerSourceChunk
        ] = []

        for row in file_rows:
            self._validate_file_row(
                row=row,
                expected_user_id=user_id,
                expected_subject_id=request.subject_id,
            )

            file_chunks = (
                await self._load_chunks_for_file(
                    user_id=user_id,
                    file_row=row,
                )
            )

            combined_chunks.extend(
                file_chunks,
            )

        return ReviewerSourceBundle(
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
        ReviewerSourceChunk,
        ...,
    ]:
        """Load and validate source chunks for one ready file."""

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
            raise ReviewerSourceUnavailableError(
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
        """Validate file ownership, subject, and processing state."""

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

        processing_status = (
            self._required_text(
                row,
                "processing_status",
            )
        )

        if (
            expected_file_id is not None
            and file_id != expected_file_id
        ):
            raise ReviewerSourceUnavailableError(
                "The loaded study-file ID is inconsistent.",
            )

        if user_id != expected_user_id:
            raise ReviewerSourceNotFoundError(
                "The selected study file was not found.",
            )

        if subject_id != expected_subject_id:
            raise ReviewerSourceNotFoundError(
                "The selected study file was not found "
                "in the requested subject.",
            )

        if processing_status != "ready":
            raise ReviewerSourceUnavailableError(
                "Reviewer generation requires ready study files.",
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
    ) -> ReviewerSourceChunk:
        """Parse one source-aware chunk row."""

        study_file_id = self._required_uuid(
            row,
            "study_file_id",
        )

        if study_file_id != expected_file_id:
            raise ReviewerSourceUnavailableError(
                "A reviewer source chunk belongs to "
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
            raise ReviewerSourceUnavailableError(
                "A reviewer source chunk has an invalid index.",
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

        return ReviewerSourceChunk(
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
            ReviewerSourceChunk,
        ],
    ) -> None:
        """Require deterministic chunk ordering for one file."""

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
            raise ReviewerSourceUnavailableError(
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
        """Read one required UUID field."""

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
            raise ReviewerSourceUnavailableError(
                f"Reviewer source {field_name} is invalid.",
            ) from exc

    def _required_text(
        self,
        row: Mapping[
            str,
            object,
        ],
        field_name: str,
    ) -> str:
        """Read one required non-empty text field."""

        value = row.get(
            field_name,
        )

        if not isinstance(
            value,
            str,
        ):
            raise ReviewerSourceUnavailableError(
                f"Reviewer source {field_name} is invalid.",
            )

        normalized = value.strip()

        if not normalized:
            raise ReviewerSourceUnavailableError(
                f"Reviewer source {field_name} is empty.",
            )

        return normalized

    def _optional_text(
        self,
        value: object,
    ) -> str | None:
        """Normalize optional source text."""

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ReviewerSourceUnavailableError(
                "Reviewer source locator label is invalid.",
            )

        normalized = value.strip()

        return normalized or None

    def _optional_locator_type(
        self,
        value: object,
    ) -> ReviewerLocatorType | None:
        """Parse optional source locator type."""

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ReviewerSourceUnavailableError(
                "Reviewer source locator type is invalid.",
            )

        try:
            return ReviewerLocatorType(
                value.strip(),
            )

        except ValueError as exc:
            raise ReviewerSourceUnavailableError(
                "Reviewer source locator type is unsupported.",
            ) from exc