# File: /backend/tests/test_quiz_source_loader.py

# Purpose: Verifies complete ordered source loading for
# file-level and subject-level Quiz generation.

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Mapping, Sequence
from functools import wraps
from typing import Any, ParamSpec
from uuid import UUID, uuid4

import pytest

from app.schemas.quiz import (
    QuizGenerateRequest,
    QuizScopeType,
)
from app.services.quiz_errors import (
    QuizSourceNotFoundError,
    QuizSourceUnavailableError,
)
from app.services.quiz_source_loader import (
    QuizSourceLoader,
)

P = ParamSpec("P")


def async_test(
    function: Callable[
        P,
        Coroutine[Any, Any, None],
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


class FakeQuizSourceAdmin:
    """Controlled source-data dependency for Quiz loader tests."""

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
    """Return one fake study-file row."""

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
    """Return one fake study-file chunk."""

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
async def test_file_scope_loads_all_chunks_in_order() -> None:
    """File Quiz generation must load the complete selected file."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeQuizSourceAdmin()

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
            chunk_index=1,
            content="Second section",
            locator_label="Page 2",
        ),
        _chunk_row(
            file_id=file_id,
            chunk_index=0,
            content="First section",
            locator_label="Page 1",
        ),
    )

    loader = QuizSourceLoader(
        admin,
    )

    result = await loader.load(
        user_id=user_id,
        request=QuizGenerateRequest(
            scope_type=QuizScopeType.FILE,
            subject_id=subject_id,
            study_file_id=file_id,
        ),
    )

    assert result.chunk_count == 2
    assert result.file_count == 1
    assert result.study_file_id == file_id

    assert [
        chunk.chunk_index
        for chunk in result.chunks
    ] == [
        0,
        1,
    ]

    assert result.chunks[
        0
    ].source_name == "Lecture.pdf"

    assert result.chunks[
        0
    ].locator_type == "page"

    assert result.chunks[
        0
    ].locator_label == "Page 1"


@async_test
async def test_subject_scope_loads_every_ready_file() -> None:
    """Subject Quiz generation must combine all ready subject files."""

    user_id = uuid4()
    subject_id = uuid4()

    first_file_id = uuid4()
    second_file_id = uuid4()

    admin = FakeQuizSourceAdmin()

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
            content="Week one content",
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
            content="Week two content",
        ),
    )

    loader = QuizSourceLoader(
        admin,
    )

    result = await loader.load(
        user_id=user_id,
        request=QuizGenerateRequest(
            scope_type=QuizScopeType.SUBJECT,
            subject_id=subject_id,
        ),
    )

    assert result.study_file_id is None
    assert result.file_count == 2
    assert result.chunk_count == 2

    assert result.character_count == (
        len(
            "Week one content",
        )
        + len(
            "Week two content",
        )
    )

    assert {
        chunk.source_name
        for chunk in result.chunks
    } == {
        "Week 1.pdf",
        "Week 2.pdf",
    }


@async_test
async def test_file_scope_rejects_other_users_file() -> None:
    """Quiz generation must never expose another student's file."""

    user_id = uuid4()
    other_user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeQuizSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=other_user_id,
        subject_id=subject_id,
    )

    loader = QuizSourceLoader(
        admin,
    )

    with pytest.raises(
        QuizSourceNotFoundError,
    ):
        await loader.load(
            user_id=user_id,
            request=QuizGenerateRequest(
                scope_type=QuizScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
            ),
        )


@async_test
async def test_file_scope_rejects_wrong_subject() -> None:
    """Quiz generation must keep source files inside the subject."""

    user_id = uuid4()
    subject_id = uuid4()
    other_subject_id = uuid4()
    file_id = uuid4()

    admin = FakeQuizSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=other_subject_id,
    )

    loader = QuizSourceLoader(
        admin,
    )

    with pytest.raises(
        QuizSourceNotFoundError,
    ):
        await loader.load(
            user_id=user_id,
            request=QuizGenerateRequest(
                scope_type=QuizScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
            ),
        )


@async_test
async def test_file_scope_requires_ready_file() -> None:
    """Quiz generation must wait until file processing is ready."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeQuizSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
        processing_status="indexing",
    )

    loader = QuizSourceLoader(
        admin,
    )

    with pytest.raises(
        QuizSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=QuizGenerateRequest(
                scope_type=QuizScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
            ),
        )


@async_test
async def test_subject_scope_requires_ready_material() -> None:
    """An empty subject must return a controlled error."""

    loader = QuizSourceLoader(
        FakeQuizSourceAdmin(),
    )

    with pytest.raises(
        QuizSourceNotFoundError,
    ):
        await loader.load(
            user_id=uuid4(),
            request=QuizGenerateRequest(
                scope_type=QuizScopeType.SUBJECT,
                subject_id=uuid4(),
            ),
        )


@async_test
async def test_ready_file_without_chunks_is_rejected() -> None:
    """Ready-state inconsistencies must not create partial Quizzes."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeQuizSourceAdmin()

    admin.files[
        file_id
    ] = _file_row(
        file_id=file_id,
        user_id=user_id,
        subject_id=subject_id,
    )

    loader = QuizSourceLoader(
        admin,
    )

    with pytest.raises(
        QuizSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=QuizGenerateRequest(
                scope_type=QuizScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
            ),
        )


@async_test
async def test_missing_chunk_index_is_rejected() -> None:
    """Incomplete source sequences must fail instead of omitting data."""

    user_id = uuid4()
    subject_id = uuid4()
    file_id = uuid4()

    admin = FakeQuizSourceAdmin()

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

    loader = QuizSourceLoader(
        admin,
    )

    with pytest.raises(
        QuizSourceUnavailableError,
    ):
        await loader.load(
            user_id=user_id,
            request=QuizGenerateRequest(
                scope_type=QuizScopeType.FILE,
                subject_id=subject_id,
                study_file_id=file_id,
            ),
        )