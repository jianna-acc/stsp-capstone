# File: /backend/app/services/study_material_preparer.py
# Purpose: Coordinates deterministic text chunking and embedding-
# request preparation without calling an external AI provider.

from app.ai.chunking import ChunkingRequest
from app.ai.embedding_batcher import EmbeddingBatchPreparer
from app.ai.preparation import StudyMaterialPreparation
from app.ai.text_chunker import TextChunker
from app.core.config import Settings, get_settings


class StudyMaterialPreparer:
    """Prepare extracted study-material text for later embedding."""

    def __init__(
        self,
        settings: Settings | None = None,
        chunker: TextChunker | None = None,
        batch_preparer: EmbeddingBatchPreparer | None = None,
    ) -> None:
        """Create the preparation pipeline and its collaborators."""

        resolved_settings = settings or get_settings()

        self._chunker = chunker or TextChunker(
            settings=resolved_settings,
        )
        self._batch_preparer = batch_preparer or EmbeddingBatchPreparer(
            settings=resolved_settings,
        )

    def prepare(
        self,
        *,
        material_id: str,
        text: str,
        source_name: str | None = None,
    ) -> StudyMaterialPreparation:
        """Prepare one extracted material without external requests."""

        chunking_result = self._chunker.chunk(
            ChunkingRequest(
                material_id=material_id,
                text=text,
                source_name=source_name,
            ),
        )

        batches = self._batch_preparer.prepare(
            chunking_result,
        )

        embedding_requests = tuple(
            self._batch_preparer.build_request(batch) for batch in batches
        )

        return StudyMaterialPreparation(
            chunking_result=chunking_result,
            batches=batches,
            embedding_requests=embedding_requests,
        )
