# File: /backend/tests/test_grounded_answer_generation_dependency.py

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import ClassVar
from uuid import UUID, uuid4

import pytest

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.grounded_answer_contracts import (
    GroundedAnswerOutcome,
    GroundedAnswerRequest,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.api import (
    grounded_answer_generation_dependency as dependency_module,
)
from app.services import (
    GroundedAnswerGenerationService as ExportedService,
)
from app.services.grounded_answer_generation import (
    GroundedAnswerGenerationService,
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)


class FakeGenerationProvider:
    """Provide controlled generation without external requests."""

    instances: ClassVar[list[FakeGenerationProvider]] = []

    def __init__(self) -> None:
        self.requests: list[GenerationRequest] = []
        self.closed = False

        self.instances.append(
            self,
        )

    @property
    def provider_name(
        self,
    ) -> str:
        """Return a provider-independent fake name."""

        return "bedrock"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Return one deterministic grounded answer."""

        self.requests.append(
            request,
        )

        return GenerationResult(
            text=(
                "Photosynthesis converts light energy "
                "into chemical energy. [Source 1]"
            ),
            provider="bedrock",
            model="fake-bedrock-model",
            input_tokens=100,
            output_tokens=20,
        )

    async def aclose(
        self,
    ) -> None:
        """Record dependency cleanup."""

        self.closed = True


def make_chunk() -> RetrievedStudyChunk:
    """Create one valid retrieved context chunk."""

    content = (
        "Photosynthesis converts light energy "
        "into chemical energy."
    )

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                uuid4(),
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": 1,
            "content": content,
            "start_offset": 100,
            "end_offset": (
                100 + len(content)
            ),
            "chunk_metadata": {
                "page_number": 2,
            },
            "embedding_model": "gemini-embedding-2",
            "similarity_score": 0.95,
        }
    )


async def exercise_dependency() -> None:
    """Resolve, use, and close the dependency."""

    dependency = (
        dependency_module
        .get_grounded_answer_generation_service()
    )

    service = await anext(
        dependency,
    )

    provider = FakeGenerationProvider.instances[-1]

    assert isinstance(
        service,
        GroundedAnswerGenerationService,
    )

    try:
        result = await service.generate(
            GroundedAnswerRequest(
                question="What is photosynthesis?",
                chunks=(
                    make_chunk(),
                ),
            )
        )

        assert result.outcome == (
            GroundedAnswerOutcome.ANSWERED
        )

        assert result.provider == "bedrock"
        assert result.model == "fake-bedrock-model"
        assert result.source_count == 1
        assert "[Source 1]" in result.answer

        assert len(
            provider.requests,
        ) == 1

        generation_request = provider.requests[0]

        assert generation_request.temperature is None
        assert generation_request.max_output_tokens is None
        assert generation_request.system_instruction
        assert "REQUEST_JSON" in generation_request.prompt

    finally:
        await dependency.aclose()

    assert provider.closed is True


def test_service_is_exported() -> None:
    """The public service package must export the service."""

    assert ExportedService is GroundedAnswerGenerationService


def test_dependency_wires_and_closes_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dependency must use the configured generation-provider factory."""

    settings = SimpleNamespace(
        ai_provider="bedrock",
    )

    provider = FakeGenerationProvider()

    captured_settings: list[object] = []

    def fake_create_generation_provider(
        *,
        settings: object,
    ) -> FakeGenerationProvider:
        captured_settings.append(
            settings,
        )

        return provider

    FakeGenerationProvider.instances.clear()
    FakeGenerationProvider.instances.append(
        provider,
    )

    monkeypatch.setattr(
        dependency_module,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        dependency_module,
        "create_generation_provider",
        fake_create_generation_provider,
    )

    asyncio.run(
        exercise_dependency()
    )

    assert captured_settings == [
        settings,
    ]

    assert provider.closed is True