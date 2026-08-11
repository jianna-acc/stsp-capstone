# File: /backend/tests/test_flashcard_generation.py
# Purpose: Verifies structured Flashcard AI generation,
# exact-count validation, repair behavior, and provider errors.

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

import pytest

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderRequestError,
)
from app.schemas.flashcard import (
    FlashcardGenerateRequest,
    FlashcardLocatorType,
    FlashcardScopeType,
)
from app.services.flashcard_errors import (
    FlashcardGenerationError,
    FlashcardGenerationResponseError,
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
    """Run async tests using the standard library."""

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
    """Controlled provider used by Flashcard tests."""

    provider_name = "fake"

    def __init__(
        self,
        results: list[
            object,
        ],
    ) -> None:
        self.results = list(
            results,
        )

        self.requests: list[
            GenerationRequest
        ] = []

        self.closed = False

    async def generate(
        self,
        request: GenerationRequest,
    ) -> object:
        """Return the next configured provider result."""

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

    async def aclose(
        self,
    ) -> None:
        """Record provider cleanup."""

        self.closed = True


def _cards_payload(
    count: int = 5,
) -> dict[
    str,
    object,
]:
    """Return valid structured Flashcard output."""

    return {
        "cards": [
            {
                "question": (
                    f"What is concept {index}?"
                ),
                "answer": (
                    f"Concept {index} is explained "
                    "by the supplied study material."
                ),
            }
            for index in range(
                1,
                count + 1,
            )
        ]
    }


def _valid_json(
    count: int = 5,
) -> str:
    """Return valid Flashcard JSON."""

    return json.dumps(
        _cards_payload(
            count,
        )
    )


def _request_and_bundle(
    *,
    card_count: int = 5,
) -> tuple[
    FlashcardGenerateRequest,
    FlashcardSourceBundle,
]:
    """Return matching Flashcard request and source bundle."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        card_count=card_count,
    )

    bundle = FlashcardSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.FILE,
        study_file_id=file_id,
        chunks=(
            FlashcardSourceChunk(
                study_file_id=file_id,
                source_name="Biology.pdf",
                chunk_index=0,
                content=(
                    "Photosynthesis converts light energy "
                    "into chemical energy. Chlorophyll "
                    "absorbs light inside chloroplasts."
                ),
                locator_type=FlashcardLocatorType.PAGE,
                locator_label="Page 1",
            ),
        ),
    )

    return (
        request,
        bundle,
    )


@async_test
async def test_valid_json_generates_flashcards() -> None:
    """Valid provider JSON must become FlashcardContent."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
                input_tokens=100,
                output_tokens=150,
            )
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        result.content.cards,
    ) == 5

    assert (
        result.content.cards[
            0
        ].question
        == "What is concept 1?"
    )

    assert result.provider == "fake"
    assert result.model == "fake-model"

    assert result.input_tokens == 100
    assert result.output_tokens == 150

    assert result.generation_attempt_count == 1

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

    assert len(
        provider.requests,
    ) == 1

    generation_request = provider.requests[
        0
    ]

    assert (
        generation_request.temperature
        == 0.2
    )

    assert (
        generation_request.max_output_tokens
        == 4_096
    )

    assert (
        "Generate exactly 5 flashcards."
        in generation_request.prompt
    )

    assert (
        generation_request.system_instruction
        is not None
    )


@async_test
async def test_markdown_fenced_json_is_accepted() -> None:
    """A fenced JSON response may still be parsed safely."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=(
                    "```json\n"
                    f"{_valid_json()}\n"
                    "```"
                ),
                provider="fake",
                model="fake-model",
            )
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        result.content.cards,
    ) == 5

    assert result.generation_attempt_count == 1
    assert len(provider.requests) == 1


@async_test
async def test_invalid_json_is_repaired_once() -> None:
    """Malformed first output must receive one repair attempt."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text="not json",
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert result.generation_attempt_count == 2
    assert len(provider.requests) == 2

    repair_request = provider.requests[
        1
    ]

    assert (
        "REPAIR_REQUEST"
        in repair_request.prompt
    )

    assert (
        "not json"
        in repair_request.prompt
    )

    assert (
        "Generate exactly 5 flashcards."
        in repair_request.prompt
    )


@async_test
async def test_wrong_card_count_is_repaired() -> None:
    """Valid JSON with the wrong card count must be repaired."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(
                    4,
                ),
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text=_valid_json(
                    5,
                ),
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle(
        card_count=5,
    )

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert len(
        result.content.cards,
    ) == 5

    assert result.generation_attempt_count == 2
    assert len(provider.requests) == 2


@async_test
async def test_duplicate_cards_are_repaired() -> None:
    """Exact duplicate Flashcards must trigger repair."""

    duplicate_payload = _cards_payload(
        5,
    )

    cards = duplicate_payload[
        "cards"
    ]

    assert isinstance(
        cards,
        list,
    )

    cards[
        4
    ] = cards[
        0
    ]

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=json.dumps(
                    duplicate_payload,
                ),
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text=_valid_json(),
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    result = await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert result.generation_attempt_count == 2
    assert len(provider.requests) == 2


@async_test
async def test_invalid_repair_response_fails() -> None:
    """Only one repair attempt may be performed."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text="first invalid response",
                provider="fake",
                model="fake-model",
            ),
            GenerationResult(
                text="second invalid response",
                provider="fake",
                model="fake-model",
            ),
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    with pytest.raises(
        FlashcardGenerationResponseError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )

    assert len(provider.requests) == 2


@pytest.mark.parametrize(
    (
        "card_count",
        "expected_tokens",
    ),
    (
        (
            5,
            4_096,
        ),
        (
            20,
            4_096,
        ),
        (
            21,
            8_192,
        ),
        (
            50,
            8_192,
        ),
    ),
)
@async_test
async def test_card_count_controls_output_budget(
    card_count: int,
    expected_tokens: int,
) -> None:
    """Larger decks must receive enough output budget."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(
                    card_count,
                ),
                provider="fake",
                model="fake-model",
            )
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle(
        card_count=card_count,
    )

    await service.generate(
        request=request,
        source_bundle=bundle,
    )

    assert (
        provider.requests[
            0
        ].max_output_tokens
        == expected_tokens
    )


@async_test
async def test_provider_failure_becomes_controlled_error() -> None:
    """Raw provider request failures must not escape."""

    provider = FakeGenerationProvider(
        [
            AIProviderRequestError(
                "provider unavailable",
            )
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    with pytest.raises(
        FlashcardGenerationError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )


@async_test
async def test_provider_identity_must_match_result() -> None:
    """GenerationResult must belong to configured provider."""

    provider = FakeGenerationProvider(
        [
            GenerationResult(
                text=_valid_json(),
                provider="different-provider",
                model="fake-model",
            )
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    with pytest.raises(
        FlashcardGenerationResponseError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )


@async_test
async def test_invalid_provider_result_is_rejected() -> None:
    """Provider must return the shared GenerationResult contract."""

    provider = FakeGenerationProvider(
        [
            object(),
        ]
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    request, bundle = _request_and_bundle()

    with pytest.raises(
        FlashcardGenerationResponseError,
    ):
        await service.generate(
            request=request,
            source_bundle=bundle,
        )


@async_test
async def test_close_closes_supported_provider() -> None:
    """Generation service must release provider resources."""

    provider = FakeGenerationProvider(
        [],
    )

    service = FlashcardGenerationService(
        provider=provider,
    )

    await service.aclose()

    assert provider.closed is True