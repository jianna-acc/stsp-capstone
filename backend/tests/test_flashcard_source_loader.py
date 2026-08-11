# File: /backend/tests/test_flashcard_source_loader.py
# Purpose: Verifies complete, ordered, owned study-material
# loading for file-level and subject-level Flashcard generation.

from __future__ import annotations

import asyncio
from collections.abc import (
    Callable,
    Coroutine,
    Mapping,
    Sequence,
)
from functools import wraps
from typing import Any, ParamSpec
from uuid import UUID, uuid4

import pytest

from app.schemas.flashcard import (
    FlashcardGenerateRequest,
    FlashcardLocatorType,
    FlashcardScopeType,
)
from app.services.flashcard_errors import (
    FlashcardSourceNotFoundError,
    FlashcardSourceUnavailableError,
)
from app.services.flashcard_source_loader import (
    FlashcardSourceLoader,
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


class FakeFlashcardSourceAdmin:
    """Controlled trusted source dependency for loader tests."""

    def __init__(
        self,
    ) -> None:
        self.files: dict[
            UUID,
            Mapping[
                str,
                object,
            ],
        ] = {}

        self.subject_files: dict[
            tuple[
                UUID,
                UUID,
            ],
            Sequence[
                Mapping[
                    str,
                    object,
                ]
            ],
        ] = {}

        self.chunks: dict[
            tuple[
                UUID,
                UUID,
            ],
            Sequence[
                Mapping[
                    str,
                    object,
                ]
            ],
        ] = {}

    async def get_study_file(
        self,
        file_id: UUID,
    ) -> Mapping[
        str,
        object,
    ] | None:
        """Return one configured study file."""

        return self.files.get(
            file_id,
        )

    async def list_ready_study_files_for_subject(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
    ) -> Sequence[
        Mapping[
            str,
            object,
        ]
    ]:
        """Return configured ready subject files."""

        return self.subject_files.get(
            (
                user_id,
                subject_id,
            ),
            (),
        )

    async def list_study_file_chunks(
        self,
        *,
        user_id: UUID,
        study_file_id: UUID,
    ) -> Sequence[
        Mapping[
            str,
            object,
        ]
    ]:
        """Return configured chunks for one owned file."""

        return self.chunks.get(
            (
                user_id,
                study_file_id,
            ),
            (),
        )


def _file_row(
    *,
    file_id: UUID,
    user_id: UUID,
    subject_id: UUID,
    filename: str = "Lecture.pdf",
    processing_status: str = "ready",
) -> dict[
    str,
    object,
]:
    """Build one study-file row."""

    return {
        "id": str(
            file_id,
        ),
        "user_id": str(
            user_id,
        ),
        "subject_id": str(
            subject_id,
        ),
        "original_filename": filename,
        "processing_status": processing_status,
    }


def _chunk_row(
    *,
    file_id: UUID,
    chunk_index: int,
    content: str,
    locator_type: str | None = "page",
    locator_label: str | None = None,
) -> dict[
    str,
    object,
]:
    """Build one source-aware chunk row."""

    return {
        "study_file_id": str(
            file_id,
        ),
        "chunk_index": chunk_index,
        "content": content,
        "locator_type": locator_type,
        "locator_label": locator_label,
    }


@async_test
async def test_file_scope_loads_complete_file_in_order() -> None:
    """File scope must load every chunk in document order."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
        filename="Biology Lecture.pdf",
    )

    admin.chunks[
        (
            user_id,
            file_id,
        )
    ] = (
        _chunk_row(
            file_id=file_id,
            chunk_index=2,
            content="Third section",
            locator_label="Page 3",
        ),
        _chunk_row(
            file_id=file_id,
            chunk_index=0,
            content="First section",
            locator_label="Page 1",
        ),
        _chunk_row(
            file_id=file_id,
            chunk_index=1,
            content="Second section",
            locator_label="Page 2",
        ),
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    result = await loader.load(
        user_id=user_id,
        request=FlashcardGenerateRequest(
            scope_type=FlashcardScopeType.FILE,
            subject_id=subject_id,
            study_file_id=file_id,
            card_count=20,
        ),
    )

    assert result.user_id == user_id
    assert result.subject_id == subject_id
    assert result.study_file_id == file_id

    assert result.scope_type is FlashcardScopeType.FILE

    assert result.chunk_count == 3
    assert result.file_count == 1

    assert [
        chunk.chunk_index
        for chunk in result.chunks
    ] == [
        0,
        1,
        2,
    ]

    assert [
        chunk.content
        for chunk in result.chunks
    ] == [
        "First section",
        "Second section",
        "Third section",
    ]

    assert result.chunks[
        0
    ].source_name == "Biology Lecture.pdf"

    assert (
        result.chunks[
            0
        ].locator_type
        is FlashcardLocatorType.PAGE
    )

    assert (
        result.chunks[
            0
        ].locator_label
        == "Page 1"
    )


@async_test
async def test_subject_scope_loads_all_ready_files() -> None:
    """Subject scope must combine every ready owned file."""

    user_id = uuid4()
    subject_id = uuid4()

    first_file_id = uuid4()
    second_file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.subject_files[
        (
            user_id,
            subject_id,
        )
    ] = (
        _file_row(
            file_id=first_file_id,
            user_id=user_id,
            subject_id=subject_id,
            filename="Week 1.pdf",
        ),
        _file_row(
            file_id=second_file_id,
            user_id=user_id,
            subject_id=subject_id,
            filename="Week 2.pdf",
        ),
    )

    admin.chunks[
        (
            user_id,
            first_file_id,
        )
    ] = (
        _chunk_row(
            file_id=first_file_id,
            chunk_index=0,
            content="Week one section one",
        ),
        _chunk_row(
            file_id=first_file_id,
            chunk_index=1,
            content="Week one section two",
        ),
    )

    admin.chunks[
        (
            user_id,
            second_file_id,
        )
    ] = (
        _chunk_row(
            file_id=second_file_id,
            chunk_index=0,
            content="Week two section one",
        ),
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    result = await loader.load(
        user_id=user_id,
        request=FlashcardGenerateRequest(
            scope_type=FlashcardScopeType.SUBJECT,
            subject_id=subject_id,
            card_count=20,
        ),
    )

    assert result.study_file_id is None
    assert result.scope_type is FlashcardScopeType.SUBJECT

    assert result.file_count == 2
    assert result.chunk_count == 3

    assert [
        chunk.source_name
        for chunk in result.chunks
    ] == [
        "Week 1.pdf",
        "Week 1.pdf",
        "Week 2.pdf",
    ]

    assert [
        chunk.content
        for chunk in result.chunks
    ] == [
        "Week one section one",
        "Week one section two",
        "Week two section one",
    ]


@async_test
async def test_file_scope_rejects_other_users_file() -> None:
    """Flashcards must never expose another student's file."""

    user_id = uuid4()
    other_user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=other_user_id,
        subject_id=subject_id,
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceNotFoundError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_file_scope_rejects_wrong_subject() -> None:
    """Selected file must belong to the requested subject."""

    user_id = uuid4()
    subject_id = uuid4()
    other_subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=other_subject_id,
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceNotFoundError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_file_scope_requires_ready_file() -> None:
    """Flashcard generation must wait for processing completion."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
        processing_status="indexing",
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_subject_scope_requires_ready_material() -> None:
    """A subject without ready files must fail safely."""

    loader = FlashcardSourceLoader(
        FakeFlashcardSourceAdmin(),
    )

    with pytest.raises(
        FlashcardSourceNotFoundError,
    ):
        await loader.load(
            user_id=uuid4(),
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.SUBJECT,
                subject_id=uuid4(),
                card_count=20,
            ),
        )


@async_test
async def test_ready_file_without_chunks_is_rejected() -> None:
    """A ready file without chunks must not generate cards."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_missing_chunk_index_is_rejected() -> None:
    """Incomplete chunk sequences must fail instead of dropping material."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
    )

    admin.chunks[
        (
            user_id,
            file_id,
        )
    ] = (
        _chunk_row(
            file_id=file_id,
            chunk_index=0,
            content="First",
        ),
        _chunk_row(
            file_id=file_id,
            chunk_index=2,
            content="Third",
        ),
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_chunk_from_unexpected_file_is_rejected() -> None:
    """Every loaded chunk must belong to the selected study file."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()
    unexpected_file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
    )

    admin.chunks[
        (
            user_id,
            file_id,
        )
    ] = (
        _chunk_row(
            file_id=unexpected_file_id,
            chunk_index=0,
            content="Unexpected content",
        ),
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_unsupported_locator_type_is_rejected() -> None:
    """Unsupported locator metadata must fail controlled validation."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
    )

    admin.chunks[
        (
            user_id,
            file_id,
        )
    ] = (
        _chunk_row(
            file_id=file_id,
            chunk_index=0,
            content="Section content",
            locator_type="unsupported",
        ),
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    with pytest.raises(
        FlashcardSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=FlashcardGenerateRequest(
                scope_type=FlashcardScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
                card_count=20,
            ),
        )


@async_test
async def test_bundle_exposes_safe_source_metadata() -> None:
    """Loaded chunks must convert to safe persistence source metadata."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeFlashcardSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
        filename="Biology.pdf",
    )

    admin.chunks[
        (
            user_id,
            file_id,
        )
    ] = (
        _chunk_row(
            file_id=file_id,
            chunk_index=0,
            content="Photosynthesis",
            locator_type="page",
            locator_label="Page 4",
        ),
        _chunk_row(
            file_id=file_id,
            chunk_index=1,
            content="Cellular respiration",
            locator_type="page",
            locator_label="Page 5",
        ),
    )

    loader = FlashcardSourceLoader(
        admin,
    )

    result = await loader.load(
        user_id=user_id,
        request=FlashcardGenerateRequest(
            scope_type=FlashcardScopeType.FILE,
            subject_id=subject_id,
            study_file_id=file_id,
            card_count=20,
        ),
    )

    assert result.character_count == (
        len(
            "Photosynthesis",
        )
        + len(
            "Cellular respiration",
        )
    )

    assert len(
        result.sources,
    ) == 2

    assert result.sources[
        0
    ].study_file_id == file_id

    assert result.sources[
        0
    ].source_name == "Biology.pdf"

    assert result.sources[
        0
    ].chunk_index == 0

    assert (
        result.sources[
            0
        ].locator_type
        is FlashcardLocatorType.PAGE
    )

    assert (
        result.sources[
            0
        ].locator_label
        == "Page 4"
    )