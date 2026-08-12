# File: /backend/scripts/bedrock_live_reviewer_smoke.py
# Purpose: Verifies Reviewer generation works through the configured
# generation provider using a controlled in-memory study source.

from __future__ import annotations

import asyncio
from uuid import uuid4

from app.ai.provider_factory import create_generation_provider
from app.core.config import get_settings
from app.schemas.reviewer import (
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerLocatorType,
    ReviewerScopeType,
)
from app.services.reviewer_generation import (
    ReviewerGenerationService,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
    ReviewerSourceChunk,
)


async def main() -> None:
    """Run one live Reviewer generation request."""

    settings = get_settings()

    provider = create_generation_provider(
        settings=settings,
    )

    service = ReviewerGenerationService(
        provider=provider,
    )

    user_id = uuid4()
    subject_id = uuid4()
    study_file_id = uuid4()

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.FILE,
        subject_id=subject_id,
        study_file_id=study_file_id,
        reviewer_length=ReviewerLength.SHORT,
    )

    source_bundle = ReviewerSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=ReviewerScopeType.FILE,
        study_file_id=study_file_id,
        chunks=(
            ReviewerSourceChunk(
                study_file_id=study_file_id,
                source_name="Biology Notes.pdf",
                chunk_index=0,
                content=(
                    "Photosynthesis is the process by which plants "
                    "convert light energy into chemical energy. "
                    "It occurs mainly in chloroplasts. Chlorophyll "
                    "absorbs light energy. During the light-dependent "
                    "reactions, water is split and oxygen is released. "
                    "ATP and NADPH are produced and later used in the "
                    "Calvin cycle to help convert carbon dioxide into "
                    "sugars. Photosynthesis is important because it "
                    "stores solar energy in chemical form and provides "
                    "oxygen used by many living organisms."
                ),
                locator_type=ReviewerLocatorType.PAGE,
                locator_label="Page 1",
            ),
        ),
    )

    try:
        result = await service.generate(
            request=request,
            source_bundle=source_bundle,
        )

        print("LIVE REVIEWER SMOKE=PASSED")
        print("Provider:", result.provider)
        print("Model:", result.model)
        print(
            "Generation attempts:",
            result.generation_attempt_count,
        )
        print(
            "Source chunks:",
            result.source_chunk_count,
        )
        print(
            "Source files:",
            result.source_file_count,
        )
        print(
            "Input tokens:",
            result.input_tokens,
        )
        print(
            "Output tokens:",
            result.output_tokens,
        )
        print(
            "Reviewer JSON:",
            result.content.model_dump_json(
                indent=2,
            ),
        )

    finally:
        await service.aclose()


if __name__ == "__main__":
    asyncio.run(
        main()
    )