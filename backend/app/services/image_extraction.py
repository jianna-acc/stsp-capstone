# File: /backend/app/services/image_extraction.py
# Purpose: Extracts readable study content from PNG, JPEG,
# and WebP images through Gemini multimodal understanding.

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from app.core.config import Settings, get_settings
from app.services.file_extraction import (
    ExtractedDocument,
    ExtractedSection,
    normalize_extracted_text,
)

PNG_MIME_TYPE = "image/png"
JPEG_MIME_TYPE = "image/jpeg"
WEBP_MIME_TYPE = "image/webp"

SUPPORTED_IMAGE_MIME_TYPES = frozenset(
    {
        PNG_MIME_TYPE,
        JPEG_MIME_TYPE,
        WEBP_MIME_TYPE,
    }
)

NO_READABLE_STUDY_CONTENT = (
    "NO_READABLE_STUDY_CONTENT"
)

IMAGE_EXTRACTION_PROMPT = """
Extract the readable study content from this image.

Instructions:
- Transcribe all readable educational text faithfully.
- Preserve headings, labels, bullet points, definitions,
  equations, table contents, and important diagram labels.
- Keep the original reading order whenever possible.
- Do not summarize unless the image itself contains a summary.
- Do not invent, infer, or add information that is not visible.
- Do not describe decorative or irrelevant visual elements.
- Return plain readable text only.
- If there is no readable study content, return exactly:
  NO_READABLE_STUDY_CONTENT
""".strip()


class ImageExtractionError(
    RuntimeError,
):
    """Raised when an image cannot produce readable study content."""


def is_supported_image_mime_type(
    mime_type: str,
) -> bool:
    """Return whether the MIME type is supported for image extraction."""

    normalized_mime_type = (
        mime_type.strip().lower()
    )

    return (
        normalized_mime_type
        in SUPPORTED_IMAGE_MIME_TYPES
    )


class GeminiImageExtractor:
    """Extract readable study material from uploaded images."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: Any | None = None,
    ) -> None:
        """Create the extractor with optional injected Gemini client."""

        self._settings = (
            settings
            if settings is not None
            else get_settings()
        )

        if not self._settings.gemini_api_key:
            raise ImageExtractionError(
                "GEMINI_API_KEY is required "
                "for image extraction.",
            )

        self._owns_client = (
            client is None
        )

        self._client = (
            client
            if client is not None
            else genai.Client(
                api_key=(
                    self._settings.gemini_api_key
                ),
                http_options=types.HttpOptions(
                    timeout=int(
                        self._settings
                        .gemini_request_timeout_seconds
                        * 1000
                    ),
                ),
            )
        )

    async def extract(
        self,
        *,
        payload: bytes,
        mime_type: str,
        filename: str,
    ) -> ExtractedDocument:
        """Extract normalized readable study text from an image."""

        if not payload:
            raise ImageExtractionError(
                "The uploaded image is empty.",
            )

        normalized_mime_type = (
            mime_type.strip().lower()
        )

        if not is_supported_image_mime_type(
            normalized_mime_type,
        ):
            raise ImageExtractionError(
                "This image type is not supported "
                "by the current extractor.",
            )

        try:
            response = (
                await self._client.aio.models.generate_content(
                    model=(
                        self._settings
                        .gemini_generation_model
                    ),
                    contents=[
                        IMAGE_EXTRACTION_PROMPT,
                        types.Part.from_bytes(
                            data=payload,
                            mime_type=(
                                normalized_mime_type
                            ),
                        ),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        max_output_tokens=8192,
                    ),
                )
            )

        except Exception as error:
            raise ImageExtractionError(
                "The image could not be read "
                "by the image extraction service.",
            ) from error

        response_text = getattr(
            response,
            "text",
            None,
        )

        if (
            not isinstance(
                response_text,
                str,
            )
            or not response_text.strip()
        ):
            raise ImageExtractionError(
                "The image extraction service "
                "returned no usable text.",
            )

        normalized_text = (
            normalize_extracted_text(
                response_text,
            )
        )

        if (
            normalized_text.upper()
            == NO_READABLE_STUDY_CONTENT
        ):
            raise ImageExtractionError(
                "No readable study content "
                "was found in the image.",
            )

        if not normalized_text:
            raise ImageExtractionError(
                "The image extraction service "
                "returned no usable text.",
            )

        section = ExtractedSection(
            locator_type="document",
            locator_label="Image",
            content=normalized_text,
            metadata={
                "filename": filename,
                "mime_type": (
                    normalized_mime_type
                ),
                "source_type": "image",
            },
        )

        return ExtractedDocument(
            extracted_text=(
                normalized_text
            ),
            sections=[
                section,
            ],
            metadata={
                "filename": filename,
                "mime_type": (
                    normalized_mime_type
                ),
                "source_type": "image",
                "extraction_provider": "gemini",
                "extraction_model": (
                    self._settings
                    .gemini_generation_model
                ),
            },
        )

    async def aclose(
        self,
    ) -> None:
        """Close SDK resources if this extractor created the client."""

        if self._owns_client:
            await self._client.aio.aclose()