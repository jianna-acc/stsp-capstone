# File: /backend/app/ai/chunking.py
# Purpose: Defines provider-independent text-chunking requests,
# results, chunks, and embedding batches.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChunkingRequest:
    """Input required to divide one study material into text chunks."""

    material_id: str
    text: str
    source_name: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate chunking input."""

        normalized_material_id = self.material_id.strip()
        normalized_text = self.text.strip()

        if not normalized_material_id:
            raise ValueError(
                "Chunking material ID must not be empty.",
            )

        if not normalized_text:
            raise ValueError(
                "Chunking text must not be empty.",
            )

        normalized_source_name: str | None = None

        if self.source_name is not None:
            stripped_source_name = self.source_name.strip()
            normalized_source_name = stripped_source_name or None

        object.__setattr__(
            self,
            "material_id",
            normalized_material_id,
        )
        object.__setattr__(
            self,
            "text",
            normalized_text,
        )
        object.__setattr__(
            self,
            "source_name",
            normalized_source_name,
        )


@dataclass(frozen=True, slots=True)
class StudyMaterialChunk:
    """One deterministic text unit prepared for embedding."""

    material_id: str
    chunk_index: int
    text: str
    start_offset: int
    end_offset: int
    source_name: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate one study-material chunk."""

        normalized_material_id = self.material_id.strip()
        normalized_text = self.text.strip()

        if not normalized_material_id:
            raise ValueError(
                "Chunk material ID must not be empty.",
            )

        if self.chunk_index < 0:
            raise ValueError(
                "Chunk index must not be negative.",
            )

        if not normalized_text:
            raise ValueError(
                "Chunk text must not be empty.",
            )

        if self.start_offset < 0:
            raise ValueError(
                "Chunk start offset must not be negative.",
            )

        if self.end_offset <= self.start_offset:
            raise ValueError(
                "Chunk end offset must be greater than its start offset.",
            )

        normalized_source_name: str | None = None

        if self.source_name is not None:
            stripped_source_name = self.source_name.strip()
            normalized_source_name = stripped_source_name or None

        object.__setattr__(
            self,
            "material_id",
            normalized_material_id,
        )
        object.__setattr__(
            self,
            "text",
            normalized_text,
        )
        object.__setattr__(
            self,
            "source_name",
            normalized_source_name,
        )

    @property
    def character_count(self) -> int:
        """Return the normalized number of characters in this chunk."""

        return len(self.text)

    @property
    def chunk_key(self) -> str:
        """Return a deterministic material-scoped chunk identifier."""

        return f"{self.material_id}:{self.chunk_index}"


@dataclass(frozen=True, slots=True)
class ChunkingResult:
    """Complete deterministic chunking output for one material."""

    material_id: str
    original_character_count: int
    chunks: tuple[StudyMaterialChunk, ...]
    source_name: str | None = None

    def __post_init__(self) -> None:
        """Validate chunk order, identity, offsets, and source metadata."""

        normalized_material_id = self.material_id.strip()

        if not normalized_material_id:
            raise ValueError(
                "Chunking result material ID must not be empty.",
            )

        if self.original_character_count <= 0:
            raise ValueError(
                "Original character count must be positive.",
            )

        if not self.chunks:
            raise ValueError(
                "Chunking result must contain at least one chunk.",
            )

        expected_indices = tuple(
            range(len(self.chunks)),
        )
        actual_indices = tuple(chunk.chunk_index for chunk in self.chunks)

        if actual_indices != expected_indices:
            raise ValueError(
                "Chunk indices must be contiguous and start at zero.",
            )

        previous_start_offset = -1

        for chunk in self.chunks:
            if chunk.material_id != normalized_material_id:
                raise ValueError(
                    "Every chunk must use the result material ID.",
                )

            if chunk.end_offset > self.original_character_count:
                raise ValueError(
                    "Chunk offsets must remain within the original text length.",
                )

            if chunk.start_offset < previous_start_offset:
                raise ValueError(
                    "Chunk start offsets must be ordered.",
                )

            previous_start_offset = chunk.start_offset

        normalized_source_name: str | None = None

        if self.source_name is not None:
            stripped_source_name = self.source_name.strip()
            normalized_source_name = stripped_source_name or None

        object.__setattr__(
            self,
            "material_id",
            normalized_material_id,
        )
        object.__setattr__(
            self,
            "source_name",
            normalized_source_name,
        )


@dataclass(frozen=True, slots=True)
class EmbeddingBatch:
    """A controlled ordered collection of chunks for one API call."""

    batch_index: int
    chunks: tuple[StudyMaterialChunk, ...]

    def __post_init__(self) -> None:
        """Validate one prepared embedding batch."""

        if self.batch_index < 0:
            raise ValueError(
                "Embedding batch index must not be negative.",
            )

        if not self.chunks:
            raise ValueError(
                "Embedding batch must contain at least one chunk.",
            )

    @property
    def texts(self) -> tuple[str, ...]:
        """Return chunk texts in provider request order."""

        return tuple(chunk.text for chunk in self.chunks)

    @property
    def chunk_keys(self) -> tuple[str, ...]:
        """Return deterministic chunk identifiers in request order."""

        return tuple(chunk.chunk_key for chunk in self.chunks)
