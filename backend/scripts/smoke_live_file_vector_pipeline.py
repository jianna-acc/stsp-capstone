# File: /backend/scripts/smoke_live_file_vector_pipeline.py
# Purpose: Runs one explicitly enabled live file-processing,
# Gemini-embedding, and Supabase vector-persistence smoke test.

from __future__ import annotations

import argparse
import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.services.file_processor import (
    FileProcessorError,
    FileProcessorService,
)
from app.services.study_material_embedder import (
    StudyMaterialEmbedder,
)
from app.services.study_material_vector_indexer import (
    StudyMaterialVectorIndexer,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)


def parse_arguments() -> argparse.Namespace:
    """Read the disposable study-file ID."""

    parser = argparse.ArgumentParser(
        description=("Run one explicitly enabled live file-to-vector smoke test."),
    )

    parser.add_argument(
        "--file-id",
        required=True,
        type=UUID,
        help=("Queued disposable study_files.id to process."),
    )

    return parser.parse_args()


async def run_smoke_test(
    *,
    file_id: UUID,
) -> None:
    """Run the complete production vector pipeline once."""

    settings = get_settings()

    if not settings.ai_live_smoke_tests_enabled:
        raise RuntimeError(
            "Live AI smoke tests are disabled. "
            "Set AI_LIVE_SMOKE_TESTS_ENABLED=true "
            "only for this controlled test.",
        )

    admin_service = SupabaseAdminService(
        settings=settings,
    )

    embedder = StudyMaterialEmbedder(
        settings=settings,
    )

    vector_indexer = StudyMaterialVectorIndexer(
        embedder=embedder,
        persistence=admin_service,
    )

    processor = FileProcessorService(
        settings=settings,
        admin_service=admin_service,
        vector_indexer=vector_indexer,
    )

    print("LIVE FILE VECTOR SMOKE TEST")
    print("===========================")
    print(f"study_file_id={file_id}")
    print(f"live_smoke_enabled={settings.ai_live_smoke_tests_enabled}")
    print(f"embedding_model={settings.gemini_embedding_model}")
    print(f"embedding_dimensions={settings.gemini_embedding_dimensions}")
    print()

    try:
        result = await processor.process_file(
            file_id=file_id,
        )

    except FileProcessorError as error:
        print("RESULT=FAIL")
        print(f"error_type={type(error).__name__}")
        print(f"error_message={error}")

        raise SystemExit(1) from error

    processing_status = getattr(
        result,
        "processing_status",
        None,
    )

    job_status = getattr(
        result,
        "job_status",
        None,
    )

    print(f"processing_status={processing_status}")

    print(f"job_status={job_status}")

    for field_name in (
        "character_count",
        "chunk_count",
        "page_count",
        "slide_count",
        "sheet_count",
    ):
        if hasattr(
            result,
            field_name,
        ):
            print(f"{field_name}={getattr(result, field_name)}")

    if processing_status != "ready":
        raise RuntimeError(
            "The disposable study file was not marked ready.",
        )

    if job_status != "completed":
        raise RuntimeError(
            "The disposable processing job was not marked completed.",
        )

    print()
    print("RESULT=PASS")


def main() -> int:
    """Run the live smoke-test command."""

    arguments = parse_arguments()

    asyncio.run(
        run_smoke_test(
            file_id=arguments.file_id,
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(),
    )
