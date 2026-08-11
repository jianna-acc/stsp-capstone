# File: /backend/app/ai/providers/gemini.py
# Purpose: Implements controlled asynchronous Gemini text-generation
# and embedding operations behind provider-independent interfaces.

from typing import Any

from google import genai
import asyncio
import logging
from google.genai import types

from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingTaskType,
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderConfigurationError,
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)
class GeminiProvider:
    """Provide Gemini generation and embedding operations."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: Any | None = None,
    ) -> None:
        """Create the provider with validated settings and an optional client."""

        self._settings = settings or get_settings()

        if not self._settings.gemini_api_key:
            raise AIProviderConfigurationError(
                "GEMINI_API_KEY is required to create the Gemini provider.",
            )

        self._owns_client = client is None

        self._client = client or genai.Client(
            api_key=self._settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=int(
                    self._settings.gemini_request_timeout_seconds * 1000,
                ),
            ),
        )

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal identifier."""

        return "gemini"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Generate text through Gemini using controlled settings."""

        temperature = (
            request.temperature
            if request.temperature is not None
            else self._settings.gemini_generation_temperature
        )
        max_output_tokens = (
            request.max_output_tokens
            if request.max_output_tokens is not None
            else self._settings.gemini_generation_max_output_tokens
        )

        config = types.GenerateContentConfig(
            system_instruction=request.system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        for attempt in range(1, 4):
            try:
                response = (
                    await self._client.aio.models.generate_content(
                        model=(
                            self._settings.gemini_generation_model
                        ),
                        contents=request.prompt,
                        config=config,
                    )
                )
                break

            except Exception as exc:
                code = getattr(
                    exc,
                    "code",
                    None,
                )
                status_code = getattr(
                    exc,
                    "status_code",
                    None,
                )

                is_transient_server_error = (
                    code in {503, 504}
                    or status_code in {503, 504}
                )

                if (
                    is_transient_server_error
                    and attempt < 3
                ):
                    delay_seconds = (
                        0.5
                        * (2 ** (attempt - 1))
                    )

                    logger.warning(
                        "Gemini generation returned a transient server error; "
                        "retrying: attempt=%s delay=%ss",
                        attempt,
                        delay_seconds,
                    )

                    await asyncio.sleep(
                        delay_seconds,
                    )
                    continue

                logger.warning(
                    "Gemini generation request failed: "
                    "exception_type=%s code=%s "
                    "status_code=%s attempt=%s",
                    type(exc).__name__,
                    code,
                    status_code,
                    attempt,
                )

                raise AIProviderRequestError(
                    "Gemini generation request failed.",
                ) from exc

        response_text = getattr(
            response,
            "text",
            None,
        )
        if (
            not isinstance(response_text, str)
            or not response_text.strip()
        ):
            candidates = getattr(
                response,
                "candidates",
                None,
            )

            first_candidate = (
                candidates[0]
                if candidates
                else None
            )

            logger.warning(
                "Gemini generation returned no usable text: "
                "finish_reason=%s usage_metadata=%s",
                getattr(
                    first_candidate,
                    "finish_reason",
                    None,
                ),
                getattr(
                    response,
                    "usage_metadata",
                    None,
                ),
            )
        if not isinstance(response_text, str) or not response_text.strip():
            raise AIProviderResponseError(
                "Gemini returned no usable generated text.",
            )

        usage_metadata = getattr(
            response,
            "usage_metadata",
            None,
        )

        return GenerationResult(
            text=response_text,
            provider=self.provider_name,
            model=self._settings.gemini_generation_model,
            input_tokens=self._read_token_count(
                usage_metadata,
                "prompt_token_count",
            ),
            output_tokens=self._read_token_count(
                usage_metadata,
                "candidates_token_count",
            ),
        )

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Generate one Gemini embedding vector for every input text."""

        formatted_texts = tuple(
            self._format_embedding_text(
                text=text,
                task_type=request.task_type,
            )
            for text in request.texts
        )

        contents = [
            types.Content(
                parts=[
                    types.Part.from_text(
                        text=formatted_text,
                    ),
                ],
            )
            for formatted_text in formatted_texts
        ]

        config = types.EmbedContentConfig(
            output_dimensionality=(self._settings.gemini_embedding_dimensions),
        )

        try:
            response = await self._client.aio.models.embed_content(
                model=self._settings.gemini_embedding_model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            raise AIProviderRequestError(
                "Gemini embedding request failed.",
            ) from exc

        embeddings = getattr(
            response,
            "embeddings",
            None,
        )

        if not embeddings:
            raise AIProviderResponseError(
                "Gemini returned no embedding vectors.",
            )

        if len(embeddings) != len(request.texts):
            raise AIProviderResponseError(
                "Gemini returned an unexpected number of embedding vectors.",
            )

        vectors: list[tuple[float, ...]] = []

        for embedding in embeddings:
            values = getattr(
                embedding,
                "values",
                None,
            )

            if values is None:
                raise AIProviderResponseError(
                    "Gemini returned an embedding without vector values.",
                )

            try:
                vector = tuple(float(value) for value in values)
            except (TypeError, ValueError) as exc:
                raise AIProviderResponseError(
                    "Gemini returned non-numeric embedding values.",
                ) from exc

            vectors.append(vector)

        try:
            return EmbeddingResult(
                vectors=tuple(vectors),
                provider=self.provider_name,
                model=self._settings.gemini_embedding_model,
                dimensions=(self._settings.gemini_embedding_dimensions),
            )
        except ValueError as exc:
            raise AIProviderResponseError(
                "Gemini returned invalid embedding vectors.",
            ) from exc

    async def aclose(self) -> None:
        """Close SDK resources when this provider created the client."""

        if self._owns_client:
            await self._client.aio.aclose()

    @staticmethod
    def _format_embedding_text(
        text: str,
        task_type: EmbeddingTaskType,
    ) -> str:
        """Apply Gemini Embedding 2 retrieval instructions."""

        if task_type is EmbeddingTaskType.RETRIEVAL_DOCUMENT:
            return f"title: none | text: {text}"

        if task_type is EmbeddingTaskType.RETRIEVAL_QUERY:
            return f"task: question answering | query: {text}"

        raise ValueError(
            f"Unsupported embedding task type: {task_type}",
        )

    @staticmethod
    def _read_token_count(
        usage_metadata: Any,
        field_name: str,
    ) -> int | None:
        """Read a non-negative SDK token count when available."""

        if usage_metadata is None:
            return None

        value = getattr(
            usage_metadata,
            field_name,
            None,
        )

        if isinstance(value, bool) or not isinstance(value, int):
            return None

        if value < 0:
            return None

        return value
