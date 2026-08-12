# File: /backend/tests/test_bedrock_provider.py
# Purpose: Verifies Amazon Bedrock generation provider behavior without
# making live AWS requests.

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.contracts import GenerationRequest
from app.ai.errors import (
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.ai.providers import BedrockGenerationProvider


def _settings() -> Any:
    """Return the minimum settings required by the Bedrock provider."""

    return SimpleNamespace(
        bedrock_region="ap-southeast-1",
        bedrock_generation_model=(
            "global.amazon.nova-2-lite-v1:0"
        ),
        bedrock_generation_temperature=0.2,
        bedrock_generation_max_output_tokens=1024,
        bedrock_request_timeout_seconds=60.0,
    )


class FakeBedrockClient:
    """Provide deterministic Bedrock Converse responses for tests."""

    def __init__(
        self,
        response: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    def converse(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.calls.append(
            kwargs,
        )

        if self.error is not None:
            raise self.error

        if self.response is None:
            raise RuntimeError(
                "Fake Bedrock response was not configured.",
            )

        return self.response

    def close(self) -> None:
        self.closed = True


def _successful_response(
    text: str = "Bedrock response",
) -> dict[str, Any]:
    """Return a representative successful Converse response."""

    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "text": text,
                    },
                ],
            },
        },
        "usage": {
            "inputTokens": 10,
            "outputTokens": 4,
            "totalTokens": 14,
        },
        "stopReason": "end_turn",
    }


def test_provider_name_is_bedrock() -> None:
    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=FakeBedrockClient(
            response=_successful_response(),
        ),
    )

    assert provider.provider_name == "bedrock"


def test_generate_returns_generation_result() -> None:
    client = FakeBedrockClient(
        response=_successful_response(),
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    result = asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Test prompt",
            ),
        )
    )

    assert result.text == "Bedrock response"
    assert result.provider == "bedrock"
    assert result.model == "global.amazon.nova-2-lite-v1:0"
    assert result.input_tokens == 10
    assert result.output_tokens == 4


def test_generate_builds_expected_converse_request() -> None:
    client = FakeBedrockClient(
        response=_successful_response(),
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Explain photosynthesis.",
            ),
        )
    )

    assert len(client.calls) == 1

    call = client.calls[0]

    assert call["modelId"] == (
        "global.amazon.nova-2-lite-v1:0"
    )

    assert call["messages"] == [
        {
            "role": "user",
            "content": [
                {
                    "text": "Explain photosynthesis.",
                },
            ],
        },
    ]

    assert call["inferenceConfig"] == {
        "temperature": 0.2,
        "maxTokens": 1024,
    }

    assert "system" not in call


def test_generate_maps_system_instruction() -> None:
    client = FakeBedrockClient(
        response=_successful_response(),
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Explain this concept.",
                system_instruction=(
                    "You are a helpful study assistant."
                ),
            ),
        )
    )

    assert client.calls[0]["system"] == [
        {
            "text": "You are a helpful study assistant.",
        },
    ]


def test_generate_uses_request_overrides() -> None:
    client = FakeBedrockClient(
        response=_successful_response(),
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Test",
                temperature=0.7,
                max_output_tokens=512,
            ),
        )
    )

    assert client.calls[0]["inferenceConfig"] == {
        "temperature": 0.7,
        "maxTokens": 512,
    }


def test_generate_combines_multiple_text_blocks() -> None:
    client = FakeBedrockClient(
        response={
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "First",
                        },
                        {
                            "text": "Second",
                        },
                    ],
                },
            },
            "usage": {},
        },
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    result = asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Test",
            ),
        )
    )

    assert result.text == "First\nSecond"


def test_generate_wraps_client_failure() -> None:
    client = FakeBedrockClient(
        error=RuntimeError(
            "AWS request failed",
        ),
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    with pytest.raises(
        AIProviderRequestError,
        match="Amazon Bedrock generation request failed",
    ):
        asyncio.run(
            provider.generate(
                GenerationRequest(
                    prompt="Test",
                ),
            )
        )


def test_generate_rejects_empty_content() -> None:
    client = FakeBedrockClient(
        response={
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [],
                },
            },
            "usage": {},
        },
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    with pytest.raises(
        AIProviderResponseError,
        match="no usable generated text",
    ):
        asyncio.run(
            provider.generate(
                GenerationRequest(
                    prompt="Test",
                ),
            )
        )


def test_generate_rejects_invalid_response_shape() -> None:
    client = FakeBedrockClient(
        response={
            "unexpected": "response",
        },
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    with pytest.raises(
        AIProviderResponseError,
        match="invalid generation response",
    ):
        asyncio.run(
            provider.generate(
                GenerationRequest(
                    prompt="Test",
                ),
            )
        )


def test_invalid_token_usage_becomes_none() -> None:
    client = FakeBedrockClient(
        response={
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "OK",
                        },
                    ],
                },
            },
            "usage": {
                "inputTokens": True,
                "outputTokens": -1,
            },
        },
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    result = asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="Test",
            ),
        )
    )

    assert result.input_tokens is None
    assert result.output_tokens is None


def test_aclose_does_not_close_injected_client() -> None:
    client = FakeBedrockClient(
        response=_successful_response(),
    )

    provider = BedrockGenerationProvider(
        settings=_settings(),
        client=client,
    )

    asyncio.run(
        provider.aclose()
    )

    assert client.closed is False