# File: /backend/app/ai/text_chunker.py
# Purpose: Normalizes extracted study-material text and divides it
# into deterministic, overlapping, boundary-aware chunks.

import re

from app.ai.chunking import (
    ChunkingRequest,
    ChunkingResult,
    StudyMaterialChunk,
)
from app.ai.errors import AIChunkingError
from app.core.config import Settings, get_settings

_INLINE_WHITESPACE_PATTERN = re.compile(r"[ \t\f\v]+")
_PARAGRAPH_BOUNDARY_PATTERN = re.compile(r"\n{2,}")
_SENTENCE_BOUNDARY_PATTERN = re.compile(
    r"""[.!?]["')\]]*(?:\s+|$)""",
)
_NEWLINE_BOUNDARY_PATTERN = re.compile(r"\n+")
_WORD_BOUNDARY_PATTERN = re.compile(r"\s+")


class TextChunker:
    """Create deterministic chunks from normalized extracted text."""

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """Create a chunker using validated application settings."""

        self._settings = settings or get_settings()

    @staticmethod
    def normalize_text(
        text: str,
    ) -> str:
        """Normalize line endings, spacing, and repeated blank lines."""

        normalized_line_endings = (
            text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
        )

        normalized_lines = [
            _INLINE_WHITESPACE_PATTERN.sub(
                " ",
                line,
            ).strip()
            for line in normalized_line_endings.split("\n")
        ]

        collapsed_lines: list[str] = []
        blank_line_pending = False

        for line in normalized_lines:
            if line:
                if blank_line_pending and collapsed_lines:
                    collapsed_lines.append("")

                collapsed_lines.append(line)
                blank_line_pending = False
            else:
                blank_line_pending = True

        return "\n".join(collapsed_lines).strip()

    def chunk(
        self,
        request: ChunkingRequest,
    ) -> ChunkingResult:
        """Normalize and deterministically divide one material."""

        normalized_text = self.normalize_text(
            request.text,
        )

        if not normalized_text:
            raise AIChunkingError(
                "Normalized chunking text must not be empty.",
            )

        text_length = len(normalized_text)
        chunks: list[StudyMaterialChunk] = []
        start_offset = 0

        while start_offset < text_length:
            start_offset = self._skip_whitespace(
                normalized_text,
                start_offset,
            )

            if start_offset >= text_length:
                break

            remaining_characters = text_length - start_offset

            if chunks and remaining_characters < self._settings.ai_chunk_min_characters:
                self._merge_final_fragment(
                    chunks=chunks,
                    text=normalized_text,
                    end_offset=text_length,
                )
                break

            if len(chunks) >= self._settings.ai_max_chunks_per_material:
                raise AIChunkingError(
                    "Chunking exceeded AI_MAX_CHUNKS_PER_MATERIAL.",
                )

            hard_end = min(
                start_offset + self._settings.ai_chunk_target_characters,
                text_length,
            )

            if hard_end == text_length:
                split_end = text_length
            else:
                split_end = self._find_split_end(
                    text=normalized_text,
                    start_offset=start_offset,
                    hard_end=hard_end,
                )

            chunk_start, chunk_end = self._trim_bounds(
                normalized_text,
                start_offset,
                split_end,
            )

            if chunk_end <= chunk_start:
                raise AIChunkingError(
                    "Chunking produced an empty text range.",
                )

            chunks.append(
                StudyMaterialChunk(
                    material_id=request.material_id,
                    chunk_index=len(chunks),
                    text=normalized_text[chunk_start:chunk_end],
                    start_offset=chunk_start,
                    end_offset=chunk_end,
                    source_name=request.source_name,
                ),
            )

            if split_end >= text_length:
                break

            next_start = self._find_next_start(
                text=normalized_text,
                chunk_start=chunk_start,
                chunk_end=chunk_end,
                split_end=split_end,
            )

            if next_start <= start_offset:
                raise AIChunkingError(
                    "Chunking could not advance to the next range.",
                )

            start_offset = next_start

        if not chunks:
            raise AIChunkingError(
                "Chunking did not produce any text chunks.",
            )

        return ChunkingResult(
            material_id=request.material_id,
            original_character_count=text_length,
            chunks=tuple(chunks),
            source_name=request.source_name,
        )

    def _find_split_end(
        self,
        *,
        text: str,
        start_offset: int,
        hard_end: int,
    ) -> int:
        """Choose the strongest available boundary before the limit."""

        minimum_end = min(
            start_offset + self._settings.ai_chunk_min_characters,
            hard_end,
        )
        window = text[start_offset:hard_end]
        minimum_window_end = minimum_end - start_offset

        patterns = (
            _PARAGRAPH_BOUNDARY_PATTERN,
            _SENTENCE_BOUNDARY_PATTERN,
            _NEWLINE_BOUNDARY_PATTERN,
            _WORD_BOUNDARY_PATTERN,
        )

        for pattern in patterns:
            candidate_ends = [
                match.end()
                for match in pattern.finditer(window)
                if match.end() >= minimum_window_end
            ]

            if candidate_ends:
                return start_offset + candidate_ends[-1]

        return hard_end

    def _find_next_start(
        self,
        *,
        text: str,
        chunk_start: int,
        chunk_end: int,
        split_end: int,
    ) -> int:
        """Calculate the next start while preserving safe overlap."""

        overlap = self._settings.ai_chunk_overlap_characters

        if overlap == 0:
            return self._skip_whitespace(
                text,
                split_end,
            )

        desired_start = max(
            chunk_start + 1,
            chunk_end - overlap,
        )

        if desired_start >= chunk_end:
            return split_end

        adjusted_start = desired_start

        if adjusted_start > 0 and not text[adjusted_start - 1].isspace():
            while adjusted_start < chunk_end and not text[adjusted_start].isspace():
                adjusted_start += 1

        adjusted_start = self._skip_whitespace(
            text,
            adjusted_start,
        )

        if adjusted_start >= chunk_end:
            return desired_start

        return adjusted_start

    @staticmethod
    def _skip_whitespace(
        text: str,
        offset: int,
    ) -> int:
        """Move an offset forward past whitespace."""

        while offset < len(text) and text[offset].isspace():
            offset += 1

        return offset

    @staticmethod
    def _trim_bounds(
        text: str,
        start_offset: int,
        end_offset: int,
    ) -> tuple[int, int]:
        """Trim whitespace while preserving accurate text offsets."""

        while start_offset < end_offset and text[start_offset].isspace():
            start_offset += 1

        while end_offset > start_offset and text[end_offset - 1].isspace():
            end_offset -= 1

        return start_offset, end_offset

    @staticmethod
    def _merge_final_fragment(
        *,
        chunks: list[StudyMaterialChunk],
        text: str,
        end_offset: int,
    ) -> None:
        """Merge a very small final fragment into the previous chunk."""

        previous_chunk = chunks[-1]

        merged_start, merged_end = TextChunker._trim_bounds(
            text,
            previous_chunk.start_offset,
            end_offset,
        )

        chunks[-1] = StudyMaterialChunk(
            material_id=previous_chunk.material_id,
            chunk_index=previous_chunk.chunk_index,
            text=text[merged_start:merged_end],
            start_offset=merged_start,
            end_offset=merged_end,
            source_name=previous_chunk.source_name,
        )
