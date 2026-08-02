# File: /backend/tests/test_text_chunker.py
# Purpose: Verifies deterministic text normalization, boundary-aware
# chunking, overlap, offsets, limits, and final-fragment handling.

from itertools import pairwise
from typing import Any

import pytest

from app.ai import (
    AIChunkingError,
    ChunkingRequest,
    TextChunker,
)
from app.core.config import Settings


def build_chunker(
    **overrides: Any,
) -> TextChunker:
    """Create a chunker with isolated valid settings."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "ai_chunk_target_characters": 500,
        "ai_chunk_overlap_characters": 0,
        "ai_chunk_min_characters": 100,
        "ai_embedding_batch_size": 16,
        "ai_max_chunks_per_material": 1000,
        "_env_file": None,
    }
    values.update(overrides)

    return TextChunker(
        settings=Settings(**values),
    )


def test_normalize_text_is_deterministic() -> None:
    """Text normalization must standardize spacing and blank lines."""

    raw_text = "  First\t line\r\n\r\n\r\nSecond\u00a0line  "

    normalized = TextChunker.normalize_text(
        raw_text,
    )

    assert normalized == "First line\n\nSecond line"


def test_short_text_creates_one_chunk() -> None:
    """Text below the target size must remain one chunk."""

    chunker = build_chunker()
    request = ChunkingRequest(
        material_id="material-1",
        text="Short study note.",
        source_name="notes.txt",
    )

    result = chunker.chunk(request)

    assert result.original_character_count == 17
    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_index == 0
    assert result.chunks[0].start_offset == 0
    assert result.chunks[0].end_offset == 17
    assert result.chunks[0].text == "Short study note."


def test_chunking_is_deterministic() -> None:
    """Identical requests and settings must produce equal results."""

    chunker = build_chunker(
        ai_chunk_overlap_characters=50,
    )
    request = ChunkingRequest(
        material_id="material-1",
        text=" ".join(f"word-{index}" for index in range(200)),
    )

    first_result = chunker.chunk(request)
    second_result = chunker.chunk(request)

    assert first_result == second_result


def test_chunker_prefers_paragraph_boundary() -> None:
    """Paragraph breaks must be preferred over hard character cuts."""

    first_paragraph = "A" * 420
    second_paragraph = "B" * 300

    chunker = build_chunker()
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text=(f"{first_paragraph}\n\n{second_paragraph}"),
        ),
    )

    assert len(result.chunks) == 2
    assert result.chunks[0].text == first_paragraph
    assert result.chunks[0].end_offset == 420
    assert result.chunks[1].text == second_paragraph


def test_chunker_prefers_sentence_boundary() -> None:
    """Sentence endings must be preferred when no paragraph ends."""

    first_sentence = f"{'A' * 420}."
    second_sentence = "B" * 300

    chunker = build_chunker()
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text=f"{first_sentence} {second_sentence}",
        ),
    )

    assert len(result.chunks) == 2
    assert result.chunks[0].text == first_sentence
    assert result.chunks[0].text.endswith(".")


def test_chunker_uses_hard_split_for_long_token() -> None:
    """Text without boundaries must still respect target limits."""

    chunker = build_chunker()
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text="x" * 1200,
        ),
    )

    assert [chunk.character_count for chunk in result.chunks] == [
        500,
        500,
        200,
    ]


def test_chunker_creates_controlled_overlap() -> None:
    """Adjacent chunks must overlap without reversing offsets."""

    overlap = 100
    chunker = build_chunker(
        ai_chunk_overlap_characters=overlap,
    )
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text=" ".join(f"word{index:03d}" for index in range(200)),
        ),
    )

    assert len(result.chunks) > 1

    for previous, current in pairwise(result.chunks):
        actual_overlap = previous.end_offset - current.start_offset

        assert actual_overlap > 0
        assert actual_overlap <= overlap


def test_zero_overlap_does_not_duplicate_text_ranges() -> None:
    """Zero-overlap chunks must not share character ranges."""

    chunker = build_chunker(
        ai_chunk_overlap_characters=0,
    )
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text=" ".join(f"word{index:03d}" for index in range(200)),
        ),
    )

    for previous, current in pairwise(result.chunks):
        assert current.start_offset >= previous.end_offset


def test_small_final_fragment_is_merged() -> None:
    """A final fragment below the minimum must join the last chunk."""

    chunker = build_chunker(
        ai_chunk_target_characters=500,
        ai_chunk_min_characters=200,
    )
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text=f"{'a' * 500} {'b' * 50}",
        ),
    )

    assert len(result.chunks) == 1
    assert result.chunks[0].character_count == 551


def test_maximum_chunk_limit_is_enforced() -> None:
    """One material must not produce more than its configured limit."""

    chunker = build_chunker(
        ai_max_chunks_per_material=2,
    )

    with pytest.raises(
        AIChunkingError,
        match="AI_MAX_CHUNKS_PER_MATERIAL",
    ):
        chunker.chunk(
            ChunkingRequest(
                material_id="material-1",
                text=(f"{'a' * 500} {'b' * 500} {'c' * 500}"),
            ),
        )


def test_chunk_metadata_is_preserved() -> None:
    """Every chunk must retain material and source metadata."""

    chunker = build_chunker()
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-42",
            text="x" * 700,
            source_name="biology.pdf",
        ),
    )

    assert result.material_id == "material-42"
    assert result.source_name == "biology.pdf"

    for chunk in result.chunks:
        assert chunk.material_id == "material-42"
        assert chunk.source_name == "biology.pdf"


def test_chunk_offsets_match_normalized_text() -> None:
    """Stored offsets must select the exact normalized chunk text."""

    raw_text = (
        "  First\t paragraph.  \r\n"
        "\r\n"
        "Second paragraph contains more study material. " * 20
    )

    chunker = build_chunker(
        ai_chunk_overlap_characters=50,
    )
    request = ChunkingRequest(
        material_id="material-1",
        text=raw_text,
    )
    normalized_text = chunker.normalize_text(
        request.text,
    )

    result = chunker.chunk(request)

    assert result.original_character_count == len(
        normalized_text,
    )

    for chunk in result.chunks:
        assert normalized_text[chunk.start_offset : chunk.end_offset] == chunk.text


def test_chunk_indices_are_contiguous() -> None:
    """Chunk indices must remain ordered and gap-free."""

    chunker = build_chunker(
        ai_chunk_overlap_characters=50,
    )
    result = chunker.chunk(
        ChunkingRequest(
            material_id="material-1",
            text=" ".join(f"term-{index}" for index in range(300)),
        ),
    )

    assert [chunk.chunk_index for chunk in result.chunks] == list(
        range(len(result.chunks)),
    )
