# File: /backend/tests/test_flashcard_large_generation.py
# Purpose: Tests multi-pass Flashcard generation for oversized
# study material using bounded batches and final synthesis.

from __future__ import annotations

import asyncio
import json
from collections.abc import (
    Callable,
    Coroutine,
)
from functools import wraps
from typing import (
    Any,
    ParamSpec,
)
from uuid import uuid4

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.schemas.flashcard import (
    FlashcardGenerateRequest,
    FlashcardScopeType,
)
from app.services.flashcard_generation import (
    FlashcardGenerationService,
)
from app.services.flashcard_source_loader import (
    FlashcardSourceBundle,
    FlashcardSourceChunk,
)

P = ParamSpec(
    "P",
)


def async_test(
    function: Callable[
        P,
        Coroutine[
            Any,
            Any,
            None,
        ],
    ],
) -> Callable[
    P,
    None,
]:
    """Run async tests with the Python standard library."""

    @wraps(
        function,
    )
    def wrapper(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        asyncio.run(
            function(
                *args,
                **kwargs,
            )
        )

    return wrapper


class FakeGenerationProvider:
    """Return controlled provider results and record requests."""

    provider_name = "fake"

    def __init__(
        self,
        results: list[
            GenerationResult
            | Exception
        ],
    ) -> None:
        self.results = list(
            results,
        )

        self.requests: list[
            GenerationRequest
        ] = []

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        self.requests.append(
            request,
        )

        if not self.results:
            raise RuntimeError(
                "No fake provider result configured.",
            )

        result = self.results.pop(
            0,
        )

        if isinstance(
            result,
            Exception,
        ):
            raise result

        return result


def make_cards_json(
    prefix: str,
) -> str:
    """Return exactly five unique Flashcards as JSON."""

    return json.dumps(
        {
            "cards": [
                {
                    "question": (
                        f"{prefix} question "
                        f"{index}?"
                    ),
                    "answer": (
                        f"{prefix} answer "
                        f"{index}."
                    ),
                }
                for index in range(
                    1,
                    6,
                )
            ],
        }
    )


def make_result(
    text: str,
    *,
    model: str = "fake-model",
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> GenerationResult:
    """Create one controlled provider result."""

    return GenerationResult(
        text=text,
        provider="fake",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def make_large_request_and_bundle() -> tuple[
    FlashcardGenerateRequest,
    FlashcardSourceBundle,
]:
    """Create source material that exceeds the single-pass limit."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = (
        FlashcardGenerateRequest(
            scope_type=(
                FlashcardScopeType.FILE
            ),
            subject_id=subject_id,
            study_file_id=file_id,
            card_count=5,
        )
    )

    bundle = (
        FlashcardSourceBundle(
            user_id=user_id,
            subject_id=subject_id,
            scope_type=(
                FlashcardScopeType.FILE
            ),
            study_file_id=file_id,
            chunks=(
                FlashcardSourceChunk(
                    study_file_id=file_id,
                    source_name=(
                        "Large Biology Notes.pdf"
                    ),
                    chunk_index=0,
                    content=(
                        "A"
                        * 50_000
                    ),
                ),
                FlashcardSourceChunk(
                    study_file_id=file_id,
                    source_name=(
                        "Large Biology Notes.pdf"
                    ),
                    chunk_index=1,
                    content=(
                        "B"
                        * 50_000
                    ),
                ),
            ),
        )
    )

    assert (
        bundle.character_count
        == 100_000
    )

    return (
        request,
        bundle,
    )


@async_test
async def test_large_material_uses_batches_then_synthesis() -> None:
    """Oversized material must generate partials before final synthesis."""

    request, bundle = (
        make_large_request_and_bundle()
    )

    provider = (
        FakeGenerationProvider(
            [
                make_result(
                    make_cards_json(
                        "Batch A",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Batch B",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Final",
                    ),
                    model="synthesis-model",
                    input_tokens=300,
                    output_tokens=120,
                ),
            ],
        )
    )

    service = (
        FlashcardGenerationService(
            provider=provider,
        )
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        provider.requests,
    ) == 3

    assert (
        "FLASHCARD_PARTIAL_BATCH"
        in provider.requests[
            0
        ].prompt
    )

    assert (
        "Batch 1 of 2"
        in provider.requests[
            0
        ].prompt
    )

    assert (
        "FLASHCARD_PARTIAL_BATCH"
        in provider.requests[
            1
        ].prompt
    )

    assert (
        "Batch 2 of 2"
        in provider.requests[
            1
        ].prompt
    )

    assert (
        "FLASHCARD_FINAL_SYNTHESIS"
        in provider.requests[
            2
        ].prompt
    )

    assert (
        result.content.cards[
            0
        ].question
        == "Final question 1?"
    )

    assert (
        result.model
        == "synthesis-model"
    )

    assert (
        result.generation_attempt_count
        == 1
    )


@async_test
async def test_large_material_result_reports_complete_source_metadata() -> None:
    """Final metadata must describe the original complete source."""

    request, bundle = (
        make_large_request_and_bundle()
    )

    provider = (
        FakeGenerationProvider(
            [
                make_result(
                    make_cards_json(
                        "Batch A",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Batch B",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Final",
                    ),
                    model="final-model",
                    input_tokens=321,
                    output_tokens=123,
                ),
            ],
        )
    )

    service = (
        FlashcardGenerationService(
            provider=provider,
        )
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert (
        result.source_character_count
        == bundle.character_count
    )

    assert (
        result.source_chunk_count
        == bundle.chunk_count
    )

    assert (
        result.source_file_count
        == bundle.file_count
    )

    assert (
        result.input_tokens
        == 321
    )

    assert (
        result.output_tokens
        == 123
    )

    assert (
        result.provider
        == "fake"
    )

    assert (
        result.model
        == "final-model"
    )


@async_test
async def test_invalid_partial_response_receives_one_repair() -> None:
    """A malformed partial batch may receive one controlled repair."""

    request, bundle = (
        make_large_request_and_bundle()
    )

    provider = (
        FakeGenerationProvider(
            [
                make_result(
                    "not valid json",
                ),
                make_result(
                    make_cards_json(
                        "Batch A repaired",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Batch B",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Final",
                    ),
                ),
            ],
        )
    )

    service = (
        FlashcardGenerationService(
            provider=provider,
        )
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        provider.requests,
    ) == 4

    repair_request = (
        provider.requests[
            1
        ]
    )

    assert (
        repair_request.prompt.startswith(
            "REPAIR_REQUEST"
        )
    )

    assert (
        "FLASHCARD_PARTIAL_BATCH"
        in repair_request.prompt
    )

    assert (
        result.content.cards[
            0
        ].question
        == "Final question 1?"
    )


@async_test
async def test_invalid_synthesis_response_receives_one_repair() -> None:
    """The final synthesis may receive one controlled repair."""

    request, bundle = (
        make_large_request_and_bundle()
    )

    provider = (
        FakeGenerationProvider(
            [
                make_result(
                    make_cards_json(
                        "Batch A",
                    ),
                ),
                make_result(
                    make_cards_json(
                        "Batch B",
                    ),
                ),
                make_result(
                    "invalid synthesis",
                ),
                make_result(
                    make_cards_json(
                        "Final repaired",
                    ),
                    model="repaired-model",
                ),
            ],
        )
    )

    service = (
        FlashcardGenerationService(
            provider=provider,
        )
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        provider.requests,
    ) == 4

    repair_request = (
        provider.requests[
            3
        ]
    )

    assert (
        repair_request.prompt.startswith(
            "REPAIR_REQUEST"
        )
    )

    assert (
        "FLASHCARD_FINAL_SYNTHESIS"
        in repair_request.prompt
    )

    assert (
        result.content.cards[
            0
        ].question
        == (
            "Final repaired "
            "question 1?"
        )
    )

    assert (
        result.model
        == "repaired-model"
    )

    assert (
        result.generation_attempt_count
        == 2
    )