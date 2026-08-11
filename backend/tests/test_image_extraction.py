# File: /backend/tests/test_image_extraction.py
# Purpose: Verifies safe Gemini-based extraction of readable
# study content from PNG, JPEG, and WebP image uploads.

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

import pytest

from app.core.config import Settings
from app.services.image_extraction import (
    JPEG_MIME_TYPE,
    PNG_MIME_TYPE,
    WEBP_MIME_TYPE,
    GeminiImageExtractor,
    ImageExtractionError,
    is_supported_image_mime_type,
)


class FakeGeminiModels:
    """Controlled Gemini models API for image-extraction tests."""

    def __init__(
        self,
        results: list[
            str | None | Exception,
        ],
    ) -> None:
        self.results = list(
            results,
        )

        self.calls: list[
            dict[str, Any]
        ] = []

    async def generate_content(
        self,
        *,
        model: str,
        contents: object,
        config: object,
    ) -> object:
        """Return the next configured fake Gemini response."""

        self.calls.append(
            {
                "model": model,
                "contents": contents,
                "config": config,
            }
        )

        if not self.results:
            raise RuntimeError(
                "No fake Gemini response configured.",
            )

        result = self.results.pop(
            0,
        )

        if isinstance(
            result,
            Exception,
        ):
            raise result

        return SimpleNamespace(
            text=result,
        )


class FakeGeminiClient:
    """Minimal async Gemini client used by image tests."""

    def __init__(
        self,
        results: list[
            str | None | Exception,
        ],
    ) -> None:
        self.models = FakeGeminiModels(
            results,
        )

        self.aio = SimpleNamespace(
            models=self.models,
        )


def build_settings() -> Settings:
    """Build only settings required by image extraction."""

    return cast(
        Settings,
        SimpleNamespace(
            gemini_api_key="test-api-key",
            gemini_generation_model=(
                "gemini-3.6-flash"
            ),
            gemini_request_timeout_seconds=30.0,
        ),
    )


@pytest.mark.parametrize(
    "mime_type",
    (
        PNG_MIME_TYPE,
        JPEG_MIME_TYPE,
        WEBP_MIME_TYPE,
    ),
)
def test_supported_image_mime_types(
    mime_type: str,
) -> None:
    """PNG, JPEG, and WebP must be recognized as image sources."""

    assert (
        is_supported_image_mime_type(
            mime_type,
        )
        is True
    )


def test_image_mime_type_check_normalizes_input() -> None:
    """MIME checks must tolerate surrounding spaces and case."""

    assert (
        is_supported_image_mime_type(
            " IMAGE/PNG ",
        )
        is True
    )


def test_non_image_mime_type_is_not_supported() -> None:
    """Normal document MIME types must not enter image extraction."""

    assert (
        is_supported_image_mime_type(
            "application/pdf",
        )
        is False
    )


def test_png_image_extracts_study_content() -> None:
    """Readable image content must become an ExtractedDocument."""

    client = FakeGeminiClient(
        [
            (
                "Cell Membrane\n\n"
                "The cell membrane controls movement "
                "of substances into and out of the cell."
            ),
        ]
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    document = asyncio.run(
        extractor.extract(
            payload=b"fake-png-bytes",
            mime_type=PNG_MIME_TYPE,
            filename="cell-membrane.png",
        )
    )

    assert document.extracted_text == (
        "Cell Membrane\n\n"
        "The cell membrane controls movement "
        "of substances into and out of the cell."
    )

    assert document.character_count > 0

    assert len(
        document.sections,
    ) == 1

    section = document.sections[
        0
    ]

    assert section.locator_type == "document"
    assert section.locator_label == "Image"

    assert (
        section.content
        == document.extracted_text
    )

    assert section.metadata[
        "filename"
    ] == "cell-membrane.png"

    assert section.metadata[
        "mime_type"
    ] == PNG_MIME_TYPE

    assert document.metadata[
        "source_type"
    ] == "image"

    assert len(
        client.models.calls,
    ) == 1


@pytest.mark.parametrize(
    "mime_type",
    (
        PNG_MIME_TYPE,
        JPEG_MIME_TYPE,
        WEBP_MIME_TYPE,
    ),
)
def test_each_supported_format_reaches_gemini(
    mime_type: str,
) -> None:
    """Every supported image format must use the image model path."""

    client = FakeGeminiClient(
        [
            "Readable study notes.",
        ]
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    document = asyncio.run(
        extractor.extract(
            payload=b"fake-image",
            mime_type=mime_type,
            filename="notes-image",
        )
    )

    assert (
        document.extracted_text
        == "Readable study notes."
    )

    assert len(
        client.models.calls,
    ) == 1

    assert client.models.calls[
        0
    ][
        "model"
    ] == "gemini-3.6-flash"


def test_image_prompt_requires_grounded_extraction() -> None:
    """The model must be told not to invent unseen study content."""

    client = FakeGeminiClient(
        [
            "Visible lesson text.",
        ]
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    asyncio.run(
        extractor.extract(
            payload=b"fake-image",
            mime_type=JPEG_MIME_TYPE,
            filename="lesson.jpg",
        )
    )

    contents = client.models.calls[
        0
    ][
        "contents"
    ]

    assert isinstance(
        contents,
        list,
    )

    prompt = contents[
        0
    ]

    assert isinstance(
        prompt,
        str,
    )

    assert (
        "Do not invent"
        in prompt
    )

    assert (
        "readable text"
        in prompt
    )


def test_empty_image_payload_is_rejected() -> None:
    """An empty image cannot be sent to the provider."""

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=FakeGeminiClient(
            [],
        ),
    )

    with pytest.raises(
        ImageExtractionError,
        match="empty",
    ):
        asyncio.run(
            extractor.extract(
                payload=b"",
                mime_type=PNG_MIME_TYPE,
                filename="empty.png",
            )
        )


def test_unsupported_image_type_is_rejected() -> None:
    """Unsupported media must fail before a Gemini request."""

    client = FakeGeminiClient(
        [],
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    with pytest.raises(
        ImageExtractionError,
        match="not supported",
    ):
        asyncio.run(
            extractor.extract(
                payload=b"fake-image",
                mime_type="image/gif",
                filename="animation.gif",
            )
        )

    assert client.models.calls == []


def test_no_readable_study_content_is_rejected() -> None:
    """A blank or irrelevant image must not become a ready material."""

    client = FakeGeminiClient(
        [
            "NO_READABLE_STUDY_CONTENT",
        ]
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    with pytest.raises(
        ImageExtractionError,
        match="readable study content",
    ):
        asyncio.run(
            extractor.extract(
                payload=b"fake-image",
                mime_type=PNG_MIME_TYPE,
                filename="blank.png",
            )
        )


def test_empty_gemini_response_is_rejected() -> None:
    """Gemini must return usable extracted text."""

    client = FakeGeminiClient(
        [
            None,
        ]
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    with pytest.raises(
        ImageExtractionError,
        match="no usable",
    ):
        asyncio.run(
            extractor.extract(
                payload=b"fake-image",
                mime_type=JPEG_MIME_TYPE,
                filename="notes.jpg",
            )
        )


def test_gemini_request_failure_becomes_controlled_error() -> None:
    """Provider failures must become safe extraction errors."""

    client = FakeGeminiClient(
        [
            RuntimeError(
                "provider unavailable",
            ),
        ]
    )

    extractor = GeminiImageExtractor(
        settings=build_settings(),
        client=client,
    )

    with pytest.raises(
        ImageExtractionError,
        match="could not be read",
    ):
        asyncio.run(
            extractor.extract(
                payload=b"fake-image",
                mime_type=WEBP_MIME_TYPE,
                filename="diagram.webp",
            )
        )