# File: /backend/scripts/bedrock_live_smoke.py
# Purpose: Performs one live Amazon Bedrock generation request through
# the project's configured generation-provider factory.

import asyncio

from app.ai.contracts import GenerationRequest
from app.ai.provider_factory import create_generation_provider


async def main() -> None:
    provider = create_generation_provider()

    try:
        result = await provider.generate(
            GenerationRequest(
                prompt=(
                    "Reply with exactly BEDROCK_CORE_OK "
                    "and nothing else."
                ),
                temperature=0.0,
                max_output_tokens=32,
            ),
        )

        print("Provider:", result.provider)
        print("Model:", result.model)
        print("Input tokens:", result.input_tokens)
        print("Output tokens:", result.output_tokens)
        print("Response:", result.text)
    finally:
        close = getattr(
            provider,
            "aclose",
            None,
        )

        if callable(close):
            await close()


if __name__ == "__main__":
    asyncio.run(main())