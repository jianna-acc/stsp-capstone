# File: /backend/app/ai/providers/bedrock.py
# Purpose: Implements controlled asynchronous Amazon Bedrock
# text generation behind the provider-independent generation interface.

import asyncio
from typing import Any

import boto3
from botocore.config import Config

from app.ai.contracts import (
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.core.config import Settings, get_settings


class BedrockGenerationProvider:
    """Provide Amazon Bedrock text-generation operations."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: Any | None = None,
    ) -> None:
        """Create the provider with settings and an optional injected client."""

        self._settings = settings or get_settings()
        self._owns_client = client is None

        self._client = client or boto3.client(
            "bedrock-runtime",
            region_name=self._settings.bedrock_region,
            config=Config(
                connect_timeout=(
                    self._settings.bedrock_request_timeout_seconds
                ),
                read_timeout=(
                    self._settings.bedrock_request_timeout_seconds
                ),
                retries={
                    "mode": "standard",
                    "max_attempts": 3,
                },
            ),
        )

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal identifier."""

        return "bedrock"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Generate text through Amazon Bedrock using Converse."""

        temperature = (
            request.temperature
            if request.temperature is not None
            else self._settings.bedrock_generation_temperature
        )

        max_output_tokens = (
            request.max_output_tokens
            if request.max_output_tokens is not None
            else self._settings.bedrock_generation_max_output_tokens
        )

        converse_request: dict[str, Any] = {
            "modelId": self._settings.bedrock_generation_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": request.prompt,
                        },
                    ],
                },
            ],
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": max_output_tokens,
            },
        }

        if request.system_instruction is not None:
            converse_request["system"] = [
                {
                    "text": request.system_instruction,
                },
            ]

        try:
            response = await asyncio.to_thread(
                self._client.converse,
                **converse_request,
            )
        except Exception as exc:
            raise AIProviderRequestError(
                "Amazon Bedrock generation request failed.",
            ) from exc

        response_text = self._extract_response_text(
            response,
        )

        usage = response.get(
            "usage",
            {},
        )

        return GenerationResult(
            text=response_text,
            provider=self.provider_name,
            model=self._settings.bedrock_generation_model,
            input_tokens=self._read_token_count(
                usage,
                "inputTokens",
            ),
            output_tokens=self._read_token_count(
                usage,
                "outputTokens",
            ),
        )

    async def aclose(self) -> None:
        """Close SDK resources when this provider created the client."""

        if not self._owns_client:
            return

        close = getattr(
            self._client,
            "close",
            None,
        )

        if callable(close):
            await asyncio.to_thread(
                close,
            )

    @staticmethod
    def _extract_response_text(
        response: Any,
    ) -> str:
        """Extract generated text from a Bedrock Converse response."""

        if not isinstance(response, dict):
            raise AIProviderResponseError(
                "Amazon Bedrock returned an invalid generation response.",
            )

        output = response.get(
            "output",
        )

        if not isinstance(output, dict):
            raise AIProviderResponseError(
                "Amazon Bedrock returned an invalid generation response.",
            )

        message = output.get(
            "message",
        )

        if not isinstance(message, dict):
            raise AIProviderResponseError(
                "Amazon Bedrock returned an invalid generation response.",
            )

        content = message.get(
            "content",
        )

        if not isinstance(content, list):
            raise AIProviderResponseError(
                "Amazon Bedrock returned an invalid generation response.",
            )

        text_parts: list[str] = []

        for block in content:
            if not isinstance(block, dict):
                continue

            text = block.get(
                "text",
            )

            if isinstance(text, str) and text.strip():
                text_parts.append(
                    text.strip(),
                )

        response_text = "\n".join(
            text_parts,
        ).strip()

        if not response_text:
            raise AIProviderResponseError(
                "Amazon Bedrock returned no usable generated text.",
            )

        return response_text

    @staticmethod
    def _read_token_count(
        usage: Any,
        field_name: str,
    ) -> int | None:
        """Read a non-negative Bedrock token count when available."""

        if not isinstance(usage, dict):
            return None

        value = usage.get(
            field_name,
        )

        if isinstance(value, bool) or not isinstance(value, int):
            return None

        if value < 0:
            return None

        return value