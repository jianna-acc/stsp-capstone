# File: /backend/tests/test_chunking_config.py
# Purpose: Verifies chunking and embedding-batch settings without
# loading private credentials or making external requests.

from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(
    **overrides: Any,
) -> Settings:
    """Create isolated valid settings without loading private .env."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "_env_file": None,
    }
    values.update(overrides)

    return Settings(**values)


def test_chunking_settings_have_controlled_defaults() -> None:
    """Chunking defaults must support bounded deterministic work."""

    settings = build_settings()

    assert settings.ai_chunk_target_characters == 2400
    assert settings.ai_chunk_overlap_characters == 300
    assert settings.ai_chunk_min_characters == 200
    assert settings.ai_embedding_batch_size == 16
    assert settings.ai_max_chunks_per_material == 1000


@pytest.mark.parametrize(
    "value",
    [
        499,
        12001,
    ],
)
def test_invalid_chunk_target_is_rejected(
    value: int,
) -> None:
    """Chunk targets must remain within practical limits."""

    with pytest.raises(
        ValidationError,
        match="AI_CHUNK_TARGET_CHARACTERS",
    ):
        build_settings(
            ai_chunk_target_characters=value,
        )


@pytest.mark.parametrize(
    "value",
    [
        -1,
        4001,
    ],
)
def test_invalid_chunk_overlap_is_rejected(
    value: int,
) -> None:
    """Chunk overlap must be non-negative and controlled."""

    with pytest.raises(
        ValidationError,
        match="AI_CHUNK_OVERLAP_CHARACTERS",
    ):
        build_settings(
            ai_chunk_overlap_characters=value,
        )


def test_overlap_must_be_smaller_than_target() -> None:
    """Overlap must not consume the complete target chunk."""

    with pytest.raises(
        ValidationError,
        match="must be smaller",
    ):
        build_settings(
            ai_chunk_target_characters=1000,
            ai_chunk_overlap_characters=1000,
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        12001,
    ],
)
def test_invalid_minimum_chunk_size_is_rejected(
    value: int,
) -> None:
    """Minimum chunks must remain positive and bounded."""

    with pytest.raises(
        ValidationError,
        match="AI_CHUNK_MIN_CHARACTERS",
    ):
        build_settings(
            ai_chunk_min_characters=value,
        )


def test_minimum_chunk_must_not_exceed_target() -> None:
    """Minimum chunk size cannot exceed the target size."""

    with pytest.raises(
        ValidationError,
        match="must not exceed",
    ):
        build_settings(
            ai_chunk_target_characters=1000,
            ai_chunk_min_characters=1001,
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        101,
    ],
)
def test_invalid_embedding_batch_size_is_rejected(
    value: int,
) -> None:
    """Embedding batches must remain within a controlled range."""

    with pytest.raises(
        ValidationError,
        match="AI_EMBEDDING_BATCH_SIZE",
    ):
        build_settings(
            ai_embedding_batch_size=value,
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        10001,
    ],
)
def test_invalid_max_chunks_is_rejected(
    value: int,
) -> None:
    """One material must not create an unbounded number of chunks."""

    with pytest.raises(
        ValidationError,
        match="AI_MAX_CHUNKS_PER_MATERIAL",
    ):
        build_settings(
            ai_max_chunks_per_material=value,
        )