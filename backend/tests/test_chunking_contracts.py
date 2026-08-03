# File: /backend/tests/test_chunking_contracts.py
# Purpose: Verifies provider-independent chunking requests, chunks,
# results, identifiers, offsets, and embedding batches.

import pytest

from app.ai import (
    ChunkingRequest,
    ChunkingResult,
    EmbeddingBatch,
    StudyMaterialChunk,
)


def build_chunk(
    *,
    material_id: str = "material-1",
    chunk_index: int = 0,
    text: str = "A valid study-material chunk.",
    start_offset: int = 0,
    end_offset: int = 29,
    source_name: str | None = "biology.pdf",
) -> StudyMaterialChunk:
    """Create one valid chunk for contract tests."""

    return StudyMaterialChunk(
        material_id=material_id,
        chunk_index=chunk_index,
        text=text,
        start_offset=start_offset,
        end_offset=end_offset,
        source_name=source_name,
    )


def test_chunking_request_normalizes_values() -> None:
    """Chunking input values must be normalized."""

    request = ChunkingRequest(
        material_id="  material-1  ",
        text="  Photosynthesis uses sunlight.  ",
        source_name="  biology.pdf  ",
    )

    assert request.material_id == "material-1"
    assert request.text == "Photosynthesis uses sunlight."
    assert request.source_name == "biology.pdf"


def test_chunking_request_rejects_blank_material_id() -> None:
    """A chunking request must identify its material."""

    with pytest.raises(
        ValueError,
        match="material ID",
    ):
        ChunkingRequest(
            material_id="   ",
            text="Valid text",
        )


def test_chunking_request_rejects_blank_text() -> None:
    """A chunking request must contain extracted text."""

    with pytest.raises(
        ValueError,
        match="text must not be empty",
    ):
        ChunkingRequest(
            material_id="material-1",
            text="   ",
        )


def test_chunk_normalizes_values_and_builds_key() -> None:
    """Chunks must expose normalized metadata and stable identifiers."""

    chunk = StudyMaterialChunk(
        material_id="  material-1 ",
        chunk_index=2,
        text="  Cellular respiration releases energy.  ",
        start_offset=100,
        end_offset=137,
        source_name="  biology.pdf ",
    )

    assert chunk.material_id == "material-1"
    assert chunk.text == "Cellular respiration releases energy."
    assert chunk.source_name == "biology.pdf"
    assert chunk.chunk_key == "material-1:2"
    assert chunk.character_count == len(chunk.text)


def test_chunk_rejects_negative_index() -> None:
    """Chunk indices must begin at zero or greater."""

    with pytest.raises(
        ValueError,
        match="index must not be negative",
    ):
        build_chunk(
            chunk_index=-1,
        )


def test_chunk_rejects_blank_text() -> None:
    """A chunk must contain usable text."""

    with pytest.raises(
        ValueError,
        match="Chunk text must not be empty",
    ):
        build_chunk(
            text="   ",
        )


def test_chunk_rejects_negative_start_offset() -> None:
    """Chunk start offsets must not be negative."""

    with pytest.raises(
        ValueError,
        match="start offset",
    ):
        build_chunk(
            start_offset=-1,
        )


@pytest.mark.parametrize(
    ("start_offset", "end_offset"),
    [
        (10, 10),
        (10, 9),
    ],
)
def test_chunk_rejects_invalid_end_offset(
    start_offset: int,
    end_offset: int,
) -> None:
    """Chunk end offsets must follow start offsets."""

    with pytest.raises(
        ValueError,
        match="end offset",
    ):
        build_chunk(
            start_offset=start_offset,
            end_offset=end_offset,
        )


def test_chunking_result_accepts_ordered_chunks() -> None:
    """A valid result must preserve ordered overlapping chunks."""

    first = build_chunk(
        chunk_index=0,
        text="First chunk",
        start_offset=0,
        end_offset=20,
    )
    second = build_chunk(
        chunk_index=1,
        text="Second chunk",
        start_offset=15,
        end_offset=35,
    )

    result = ChunkingResult(
        material_id="material-1",
        original_character_count=35,
        chunks=(
            first,
            second,
        ),
        source_name="biology.pdf",
    )

    assert result.material_id == "material-1"
    assert len(result.chunks) == 2


def test_chunking_result_requires_chunks() -> None:
    """A chunking result must contain at least one chunk."""

    with pytest.raises(
        ValueError,
        match="at least one chunk",
    ):
        ChunkingResult(
            material_id="material-1",
            original_character_count=100,
            chunks=(),
        )


def test_chunking_result_rejects_wrong_material_id() -> None:
    """Every result chunk must belong to the same material."""

    with pytest.raises(
        ValueError,
        match="result material ID",
    ):
        ChunkingResult(
            material_id="material-1",
            original_character_count=100,
            chunks=(
                build_chunk(
                    material_id="material-2",
                ),
            ),
        )


def test_chunking_result_requires_contiguous_indices() -> None:
    """Chunk indices must start at zero without gaps."""

    with pytest.raises(
        ValueError,
        match="contiguous",
    ):
        ChunkingResult(
            material_id="material-1",
            original_character_count=100,
            chunks=(
                build_chunk(
                    chunk_index=1,
                ),
            ),
        )


def test_chunking_result_rejects_out_of_range_offset() -> None:
    """Chunk offsets must remain inside the original text."""

    with pytest.raises(
        ValueError,
        match="original text length",
    ):
        ChunkingResult(
            material_id="material-1",
            original_character_count=20,
            chunks=(
                build_chunk(
                    end_offset=30,
                ),
            ),
        )


def test_chunking_result_rejects_unordered_starts() -> None:
    """Chunk start offsets must not move backwards."""

    first = build_chunk(
        chunk_index=0,
        start_offset=10,
        end_offset=30,
    )
    second = build_chunk(
        chunk_index=1,
        start_offset=5,
        end_offset=25,
    )

    with pytest.raises(
        ValueError,
        match="start offsets must be ordered",
    ):
        ChunkingResult(
            material_id="material-1",
            original_character_count=30,
            chunks=(
                first,
                second,
            ),
        )


def test_embedding_batch_exposes_ordered_values() -> None:
    """Embedding batches must preserve chunk and text order."""

    first = build_chunk(
        chunk_index=0,
        text="First chunk",
        start_offset=0,
        end_offset=20,
    )
    second = build_chunk(
        chunk_index=1,
        text="Second chunk",
        start_offset=15,
        end_offset=35,
    )

    batch = EmbeddingBatch(
        batch_index=0,
        chunks=(
            first,
            second,
        ),
    )

    assert batch.texts == (
        "First chunk",
        "Second chunk",
    )
    assert batch.chunk_keys == (
        "material-1:0",
        "material-1:1",
    )


def test_embedding_batch_rejects_negative_index() -> None:
    """Embedding batch indices must not be negative."""

    with pytest.raises(
        ValueError,
        match="batch index",
    ):
        EmbeddingBatch(
            batch_index=-1,
            chunks=(
                build_chunk(),
            ),
        )


def test_embedding_batch_requires_chunks() -> None:
    """An embedding batch must contain at least one chunk."""

    with pytest.raises(
        ValueError,
        match="at least one chunk",
    ):
        EmbeddingBatch(
            batch_index=0,
            chunks=(),
        )