# File: /backend/app/ai/smoke/generation.py
# Purpose: Performs one explicitly authorized live Gemini generation
# smoke test without exposing credentials or private project data.

import argparse
import asyncio
import sys

from app.ai import (
    AIProviderError,
    GenerationRequest,
    GenerationResult,
)
from app.ai.providers import GeminiProvider
from app.core.config import Settings, get_settings

EXPECTED_MARKER = "STUDY_AI_GENERATION_OK"

SYSTEM_INSTRUCTION = (
    "You are running a controlled API connectivity test. "
    "Return only the exact marker requested by the user. "
    "Do not add punctuation, formatting, or explanation."
)

GENERATION_PROMPT = f"Return exactly this marker and nothing else: {EXPECTED_MARKER}"


def build_argument_parser() -> argparse.ArgumentParser:
    """Create command-line arguments for explicit live authorization."""

    parser = argparse.ArgumentParser(
        description=("Run one controlled live Gemini generation smoke test."),
    )
    parser.add_argument(
        "--confirm-live-call",
        action="store_true",
        help=(
            "Confirm that one controlled live provider request may "
            "consume quota or incur provider charges."
        ),
    )

    return parser


def validate_live_test_authorization(
    settings: Settings,
    *,
    confirmed: bool,
) -> list[str]:
    """Return every reason why the live request must not run."""

    blockers: list[str] = []

    if not confirmed:
        blockers.append(
            "The --confirm-live-call option was not provided.",
        )

    if not settings.ai_live_smoke_tests_enabled:
        blockers.append(
            "AI_LIVE_SMOKE_TESTS_ENABLED is false.",
        )

    if not settings.gemini_api_key:
        blockers.append(
            "GEMINI_API_KEY is not configured.",
        )

    return blockers


def normalize_generated_text(
    text: str,
) -> str:
    """Remove harmless Markdown fencing from a marker response."""

    normalized = text.strip()

    if normalized.startswith("```") and normalized.endswith("```"):
        lines = normalized.splitlines()

        if len(lines) >= 3:
            normalized = "\n".join(
                lines[1:-1],
            ).strip()

    return normalized


def validate_generation_result(
    result: GenerationResult,
    *,
    settings: Settings,
) -> str:
    """Validate the controlled generation response and metadata."""

    if result.provider != "gemini":
        raise RuntimeError(
            "Generation result used an unexpected provider.",
        )

    if result.model != settings.gemini_generation_model:
        raise RuntimeError(
            "Generation result used an unexpected model.",
        )

    normalized_text = normalize_generated_text(
        result.text,
    )

    if normalized_text != EXPECTED_MARKER:
        raise RuntimeError(
            "Gemini did not return the expected smoke-test marker.",
        )

    if len(result.text) > 500:
        raise RuntimeError(
            "Gemini returned an unexpectedly long smoke-test response.",
        )

    return normalized_text


async def run_live_generation_smoke(
    settings: Settings,
) -> None:
    """Perform one controlled Gemini text-generation request."""

    provider = GeminiProvider(
        settings=settings,
    )

    try:
        result = await provider.generate(
            GenerationRequest(
                prompt=GENERATION_PROMPT,
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.0,
                max_output_tokens=256,
            ),
        )

        normalized_text = validate_generation_result(
            result,
            settings=settings,
        )

        print("Controlled Gemini generation smoke test passed.")
        print(f"Provider: {result.provider}")
        print(f"Model: {result.model}")
        print(f"Expected marker returned: {normalized_text == EXPECTED_MARKER}")
        print(f"Response characters: {len(result.text)}")

        if result.input_tokens is None:
            print("Input tokens: unavailable")
        else:
            print(f"Input tokens: {result.input_tokens}")

        if result.output_tokens is None:
            print("Output tokens: unavailable")
        else:
            print(f"Output tokens: {result.output_tokens}")

        print("No credentials or private project data were printed.")
    finally:
        await provider.aclose()


def main() -> int:
    """Authorize and run the controlled generation smoke test."""

    parser = build_argument_parser()
    arguments = parser.parse_args()
    settings = get_settings()

    blockers = validate_live_test_authorization(
        settings,
        confirmed=arguments.confirm_live_call,
    )

    if blockers:
        print(
            "Live Gemini generation smoke test was not run.",
            file=sys.stderr,
        )

        for blocker in blockers:
            print(
                f"- {blocker}",
                file=sys.stderr,
            )

        return 2

    print(
        "Starting one controlled live Gemini generation smoke test.",
    )
    print(
        "No credentials or private project data will be sent.",
    )

    try:
        asyncio.run(
            run_live_generation_smoke(settings),
        )
    except AIProviderError as exc:
        print(
            f"Controlled provider failure: {exc}",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as exc:
        print(
            f"Smoke-test validation failure: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
