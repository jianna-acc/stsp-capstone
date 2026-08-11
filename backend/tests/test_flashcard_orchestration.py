# File: /backend/tests/test_flashcard_orchestration.py
# Purpose: Verifies complete Flashcard source-loading,
# generation, title creation, and persistence orchestration.

from __future__ import annotations

import asyncio
from collections.abc import (
    Callable,
    Coroutine,
)
from functools import wraps
from typing import (
    Any,
    ParamSpec,
)
from uuid import UUID, uuid4

import pytest
from app.services.flashcard_orchestration import (
    FlashcardOrchestrationService,
)

from app.schemas.flashcard import (
    FlashcardContent,
    FlashcardGenerateRequest,
    FlashcardItem,
    FlashcardLocatorType,
    FlashcardScopeType,
)
from app.services.flashcard_errors import (
    FlashcardGenerationError,
    FlashcardOrchestrationError,
    FlashcardSourceNotFoundError,
)
from app.services.flashcard_generation import (
    FlashcardGenerationResult,
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
    """Run one async test using the standard library."""

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


class FakeSourceLoader:
    """Controlled Flashcard source loader."""

    def __init__(
        self,
        result: object,
        *,
        events: list[str] | None = None,
    ) -> None:
        self.result = result
        self.events = events

        self.calls: list[
            tuple[
                UUID,
                FlashcardGenerateRequest,
            ]
        ] = []

    async def load(
        self,
        *,
        user_id: UUID,
        request: FlashcardGenerateRequest,
    ) -> object:
        """Return or raise the configured source result."""

        self.calls.append(
            (
                user_id,
                request,
            )
        )

        if self.events is not None:
            self.events.append(
                "load",
            )

        if isinstance(
            self.result,
            Exception,
        ):
            raise self.result

        return self.result


class FakeGenerationService:
    """Controlled Flashcard AI generation service."""

    def __init__(
        self,
        result: object,
        *,
        events: list[str] | None = None,
    ) -> None:
        self.result = result
        self.events = events

        self.calls: list[
            tuple[
                FlashcardGenerateRequest,
                FlashcardSourceBundle,
            ]
        ] = []

    async def generate(
        self,
        *,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> object:
        """Return or raise the configured AI result."""

        self.calls.append(
            (
                request,
                source_bundle,
            )
        )

        if self.events is not None:
            self.events.append(
                "generate",
            )

        if isinstance(
            self.result,
            Exception,
        ):
            raise self.result

        return self.result


class FakeFlashcardService:
    """Record persistent Flashcard service operations."""

    def __init__(
        self,
        *,
        events: list[str] | None = None,
    ) -> None:
        self.events = events

        self.calls: list[
            dict[
                str,
                object,
            ]
        ] = []

        self.result = object()

    def create_deck(
        self,
        **kwargs: object,
    ) -> object:
        """Record one generated deck persistence call."""

        self.calls.append(
            kwargs,
        )

        if self.events is not None:
            self.events.append(
                "create_deck",
            )

        return self.result


def _cards() -> tuple[
    FlashcardItem,
    ...,
]:
    """Return one valid five-card deck."""

    return tuple(
        FlashcardItem(
            question=f"Question {index}",
            answer=f"Answer {index}",
        )
        for index in range(
            1,
            6,
        )
    )


def _bundle(
    *,
    user_id: UUID,
    subject_id: UUID,
    scope_type: FlashcardScopeType,
    file_id: UUID | None = None,
    source_name: str = "Biology Lecture.pdf",
) -> FlashcardSourceBundle:
    """Return one valid source bundle."""

    source_file_id = (
        file_id
        if file_id is not None
        else uuid4()
    )

    return FlashcardSourceBundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=scope_type,
        study_file_id=(
            source_file_id
            if scope_type is FlashcardScopeType.FILE
            else None
        ),
        chunks=(
            FlashcardSourceChunk(
                study_file_id=source_file_id,
                source_name=source_name,
                chunk_index=0,
                content=(
                    "Photosynthesis converts light energy "
                    "into chemical energy."
                ),
                locator_type=FlashcardLocatorType.PAGE,
                locator_label="Page 1",
            ),
        ),
    )


def _generation_result() -> FlashcardGenerationResult:
    """Return one valid AI generation result."""

    return FlashcardGenerationResult(
        content=FlashcardContent(
            cards=_cards(),
        ),
        provider="fake",
        model="fake-model",
        input_tokens=100,
        output_tokens=200,
        generation_attempt_count=1,
        source_character_count=60,
        source_chunk_count=1,
        source_file_count=1,
    )


@async_test
async def test_generate_deck_runs_complete_pipeline_in_order() -> None:
    """Source loading, AI generation, and save must be sequential."""

    events: list[
        str
    ] = []

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        card_count=5,
    )

    bundle = _bundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.FILE,
        file_id=file_id,
    )

    source_loader = FakeSourceLoader(
        bundle,
        events=events,
    )

    generation_service = FakeGenerationService(
        _generation_result(),
        events=events,
    )

    flashcard_service = FakeFlashcardService(
        events=events,
    )

    orchestration = FlashcardOrchestrationService(
        source_loader=source_loader,
        generation_service=generation_service,
        flashcard_service=flashcard_service,
    )

    result = await orchestration.generate_deck(
        user_id=user_id,
        request=request,
    )

    assert result is flashcard_service.result

    assert events == [
        "load",
        "generate",
        "create_deck",
    ]


@async_test
async def test_file_scope_builds_filename_based_title() -> None:
    """File decks should receive a useful deterministic title."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        card_count=5,
    )

    bundle = _bundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.FILE,
        file_id=file_id,
        source_name="Biology Lecture.pdf",
    )

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(),
        ),
        flashcard_service=persistence,
    )

    await orchestration.generate_deck(
        user_id=user_id,
        request=request,
    )

    assert persistence.calls[
        0
    ][
        "title"
    ] == "Biology Lecture Flashcards"


@async_test
async def test_subject_scope_builds_generic_title() -> None:
    """Subject decks should have a safe title without subject metadata."""

    user_id = uuid4()
    subject_id = uuid4()

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.SUBJECT,
        subject_id=subject_id,
        card_count=5,
    )

    bundle = _bundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.SUBJECT,
    )

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(),
        ),
        flashcard_service=persistence,
    )

    await orchestration.generate_deck(
        user_id=user_id,
        request=request,
    )

    assert persistence.calls[
        0
    ][
        "title"
    ] == "Study Flashcards"


@async_test
async def test_persistence_receives_generation_and_sources() -> None:
    """Only validated AI content and safe source metadata are saved."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        card_count=5,
    )

    bundle = _bundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.FILE,
        file_id=file_id,
    )

    generation = _generation_result()

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            generation,
        ),
        flashcard_service=persistence,
    )

    await orchestration.generate_deck(
        user_id=user_id,
        request=request,
    )

    payload = persistence.calls[
        0
    ]

    assert payload[
        "user_id"
    ] == user_id

    assert payload[
        "subject_id"
    ] == subject_id

    assert payload[
        "study_file_id"
    ] == file_id

    assert (
        payload[
            "scope_type"
        ]
        is FlashcardScopeType.FILE
    )

    assert payload[
        "requested_card_count"
    ] == 5

    assert payload[
        "cards"
    ] == generation.content.cards

    assert payload[
        "sources"
    ] == bundle.sources

    assert payload[
        "generation_model"
    ] == "fake-model"


@async_test
async def test_source_failure_never_runs_generation_or_save() -> None:
    """Unavailable material must fail before AI or persistence."""

    generation_service = FakeGenerationService(
        _generation_result(),
    )

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            FlashcardSourceNotFoundError(
                "No study material.",
            )
        ),
        generation_service=generation_service,
        flashcard_service=persistence,
    )

    with pytest.raises(
        FlashcardSourceNotFoundError,
    ):
        await orchestration.generate_deck(
            user_id=uuid4(),
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.SUBJECT,
                subject_id=uuid4(),
                card_count=5,
            ),
        )

    assert generation_service.calls == []
    assert persistence.calls == []


@async_test
async def test_generation_failure_never_persists_deck() -> None:
    """Failed AI generation must never save an empty deck."""

    user_id = uuid4()
    subject_id = uuid4()

    bundle = _bundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.SUBJECT,
    )

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            FlashcardGenerationError(
                "AI generation failed.",
            )
        ),
        flashcard_service=persistence,
    )

    with pytest.raises(
        FlashcardGenerationError,
    ):
        await orchestration.generate_deck(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.SUBJECT,
                subject_id=subject_id,
                card_count=5,
            ),
        )

    assert persistence.calls == []


@async_test
async def test_source_bundle_must_match_authenticated_user() -> None:
    """Orchestration must reject inconsistent source ownership."""

    authenticated_user_id = uuid4()

    bundle = _bundle(
        user_id=uuid4(),
        subject_id=uuid4(),
        scope_type=FlashcardScopeType.SUBJECT,
    )

    generation_service = FakeGenerationService(
        _generation_result(),
    )

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=generation_service,
        flashcard_service=persistence,
    )

    with pytest.raises(
        FlashcardOrchestrationError,
    ):
        await orchestration.generate_deck(
            user_id=authenticated_user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.SUBJECT,
                subject_id=bundle.subject_id,
                card_count=5,
            ),
        )

    assert generation_service.calls == []
    assert persistence.calls == []


@async_test
async def test_long_filename_title_remains_within_schema_limit() -> None:
    """Generated titles must never exceed the persisted title limit."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    request = FlashcardGenerateRequest(
        scope_type=FlashcardScopeType.FILE,
        subject_id=subject_id,
        study_file_id=file_id,
        card_count=5,
    )

    bundle = _bundle(
        user_id=user_id,
        subject_id=subject_id,
        scope_type=FlashcardScopeType.FILE,
        file_id=file_id,
        source_name=(
            "A" * 300
            + ".pdf"
        ),
    )

    persistence = FakeFlashcardService()

    orchestration = FlashcardOrchestrationService(
        source_loader=FakeSourceLoader(
            bundle,
        ),
        generation_service=FakeGenerationService(
            _generation_result(),
        ),
        flashcard_service=persistence,
    )

    await orchestration.generate_deck(
        user_id=user_id,
        request=request,
    )

    title = persistence.calls[
        0
    ][
        "title"
    ]

    assert isinstance(
        title,
        str,
    )

    assert len(
        title,
    ) <= 160

    assert title.endswith(
        " Flashcards",
    )