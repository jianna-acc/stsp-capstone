# File: /backend/app/services/grounded_answer_generation.py

from __future__ import annotations

import re
from inspect import isawaitable
from typing import Final

from app.ai.contracts import (
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
)
from app.ai.errors import (
    AIProviderConfigurationError,
    AIProviderRequestError,
    AIProviderResponseError,
)
from app.ai.grounded_answer_contracts import (
    GroundedAnswerGenerationError,
    GroundedAnswerRequest,
    GroundedAnswerResponseError,
    GroundedAnswerResult,
    GroundedAnswerValidationError,
)
from app.ai.grounded_prompt import (
    GroundedPromptBuilder,
)

_CITATION_CANDIDATE_PATTERN: Final = re.compile(
    r"\[Source[^\]]*\]"
)

_EXACT_CITATION_PATTERN: Final = re.compile(
    r"\[Source ([1-9]\d*)\]"
)

_LOOSE_CITATION_PATTERN: Final = re.compile(
    r"[\[(]\s*source\s+([1-9]\d*)\s*[\])]",
    flags=re.IGNORECASE,
)


class GroundedAnswerGenerationService:
    """Generate answers grounded in retrieved study context."""

    def __init__(
        self,
        *,
        provider: GenerationProvider,
        prompt_builder: GroundedPromptBuilder | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        if not isinstance(
            provider,
            GenerationProvider,
        ):
            raise GroundedAnswerValidationError(
                "provider must implement GenerationProvider."
            )

        if (
            prompt_builder is not None
            and not isinstance(
                prompt_builder,
                GroundedPromptBuilder,
            )
        ):
            raise GroundedAnswerValidationError(
                "prompt_builder must be a GroundedPromptBuilder."
            )

        try:
            GenerationRequest(
                prompt="Validate generation settings.",
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except (TypeError, ValueError) as exc:
            raise GroundedAnswerValidationError(
                "The generation settings are invalid."
            ) from exc

        self._provider = provider
        self._prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else GroundedPromptBuilder()
        )
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    async def generate(
        self,
        request: GroundedAnswerRequest,
    ) -> GroundedAnswerResult:
        """Generate one grounded answer or no-context result."""

        if not isinstance(
            request,
            GroundedAnswerRequest,
        ):
            raise GroundedAnswerValidationError(
                "request must be a GroundedAnswerRequest."
            )

        if not request.context_available:
            return GroundedAnswerResult.no_context(
                request,
            )

        prompt = self._prompt_builder.build(
            request,
        )

        citation_instruction = (
            _build_citation_instruction(
                source_count=prompt.included_chunk_count,
            )
        )

        generation_prompt = (
            prompt.user_prompt
            + citation_instruction
        )

        provider_result = await self._generate_provider_result(
            prompt=generation_prompt,
            system_instruction=prompt.system_instruction,
        )

        answer_text = _normalize_citation_markers(
            provider_result.text,
        )

        try:
            _validate_citation_markers(
                answer=answer_text,
                source_count=prompt.included_chunk_count,
            )
        except GroundedAnswerResponseError:
            repair_prompt = (
                generation_prompt
                + _build_citation_repair_instruction(
                    source_count=(
                        prompt.included_chunk_count
                    ),
                    previous_answer=provider_result.text,
                )
            )

            provider_result = (
                await self._generate_provider_result(
                    prompt=repair_prompt,
                    system_instruction=(
                        prompt.system_instruction
                    ),
                )
            )

            answer_text = _normalize_citation_markers(
                provider_result.text,
            )

            if not _CITATION_CANDIDATE_PATTERN.search(
                answer_text,
            ):
                answer_text = _append_source_footer(
                    answer=answer_text,
                    source_count=(
                        prompt.included_chunk_count
                    ),
                )

            _validate_citation_markers(
                answer=answer_text,
                source_count=prompt.included_chunk_count,
            )

        try:
            return GroundedAnswerResult.generated(
                request=prompt.request,
                answer=answer_text,
                provider=provider_result.provider,
                model=provider_result.model,
            )
        except GroundedAnswerResponseError:
            raise
        except (TypeError, ValueError) as exc:
            raise GroundedAnswerResponseError(
                "The generated grounded-answer result "
                "was invalid."
            ) from exc

    async def _generate_provider_result(
        self,
        *,
        prompt: str,
        system_instruction: str,
    ) -> GenerationResult:
        """Request and validate one provider generation."""

        try:
            generation_request = GenerationRequest(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=self._temperature,
                max_output_tokens=(
                    self._max_output_tokens
                ),
            )
        except (TypeError, ValueError) as exc:
            raise GroundedAnswerValidationError(
                "The grounded generation request is invalid."
            ) from exc

        try:
            provider_result = await self._provider.generate(
                generation_request,
            )
        except (
            AIProviderConfigurationError,
            AIProviderRequestError,
            AIProviderResponseError,
        ) as exc:
            raise GroundedAnswerGenerationError(
                "The AI provider could not generate "
                "a grounded answer."
            ) from exc
        except Exception as exc:
            raise GroundedAnswerGenerationError(
                "An unexpected grounded-answer "
                "generation failure occurred."
            ) from exc

        self._validate_provider_result(
            provider_result,
        )

        return provider_result

    async def aclose(
        self,
    ) -> None:
        """Close provider resources when supported."""

        close_method = getattr(
            self._provider,
            "aclose",
            None,
        )

        if not callable(
            close_method,
        ):
            return

        close_result = close_method()

        if isawaitable(
            close_result,
        ):
            await close_result

    def _validate_provider_result(
        self,
        result: object,
    ) -> None:
        if not isinstance(
            result,
            GenerationResult,
        ):
            raise GroundedAnswerResponseError(
                "The AI provider returned an invalid "
                "generation result."
            )

        provider_name = getattr(
            self._provider,
            "provider_name",
            None,
        )

        if not isinstance(
            provider_name,
            str,
        ) or not provider_name.strip():
            raise GroundedAnswerResponseError(
                "The generation provider name is invalid."
            )

        if result.provider != provider_name.strip():
            raise GroundedAnswerResponseError(
                "The generation result provider does not "
                "match the configured provider."
            )

def _append_source_footer(
    *,
    answer: str,
    source_count: int,
) -> str:
    """Append deterministic references to supplied sources."""

    if (
        isinstance(source_count, bool)
        or not isinstance(source_count, int)
        or source_count <= 0
    ):
        raise GroundedAnswerResponseError(
            "A source footer requires at least one source."
        )

    normalized_answer = answer.strip()

    if not normalized_answer:
        raise GroundedAnswerResponseError(
            "A source footer cannot be added to an "
            "empty answer."
        )

    source_markers = " ".join(
        f"[Source {source_number}]"
        for source_number in range(
            1,
            source_count + 1,
        )
    )

    return (
        f"{normalized_answer}\n\n"
        f"Sources consulted: {source_markers}"
    )

def _validate_citation_markers(
    *,
    answer: str,
    source_count: int,
) -> None:
    if (
        isinstance(source_count, bool)
        or not isinstance(source_count, int)
        or source_count <= 0
    ):
        raise GroundedAnswerResponseError(
            "Citation validation requires at least "
            "one source."
        )

    candidate_markers = (
        _CITATION_CANDIDATE_PATTERN.findall(
            answer,
        )
    )

    exact_source_numbers = (
        _EXACT_CITATION_PATTERN.findall(
            answer,
        )
    )

    if not candidate_markers:
        raise GroundedAnswerResponseError(
            "A grounded answer must contain at least "
            "one [Source N] citation."
        )

    if len(candidate_markers) != len(
        exact_source_numbers,
    ):
        raise GroundedAnswerResponseError(
            "The grounded answer contains a malformed "
            "source citation."
        )

    source_numbers = tuple(
        int(value)
        for value in exact_source_numbers
    )

    if any(
        source_number > source_count
        for source_number in source_numbers
    ):
        raise GroundedAnswerResponseError(
            "The grounded answer cites a source that "
            "was not supplied to the AI provider."
        )

def _build_citation_instruction(
    *,
    source_count: int,
) -> str:
    """Build an instruction containing exact allowed markers."""

    allowed_markers = ", ".join(
        f"[Source {source_number}]"
        for source_number in range(
            1,
            source_count + 1,
        )
    )

    return (
        "\n\nALLOWED_CITATION_MARKERS:\n"
        f"{allowed_markers}\n\n"
        "The final answer must contain at least one citation "
        "from the exact list above. Copy the marker exactly, "
        "including its square brackets and number. Place each "
        "marker immediately after the statement it supports."
    )


def _build_citation_repair_instruction(
    *,
    source_count: int,
    previous_answer: str,
) -> str:
    """Build one strict citation-correction request."""

    allowed_markers = ", ".join(
        f"[Source {source_number}]"
        for source_number in range(
            1,
            source_count + 1,
        )
    )

    return (
        "\n\nCITATION_CORRECTION:\n"
        "Rewrite the previous answer because it did not use "
        "the required citation format.\n\n"
        "Exact allowed citation markers:\n"
        f"{allowed_markers}\n\n"
        "The rewritten answer must contain at least one exact "
        "allowed marker. Do not use parentheses, footnotes, "
        "links, or different citation wording. Do not mention "
        "this correction request.\n\n"
        "PREVIOUS_ANSWER:\n"
        f"{previous_answer}"
    )


def _normalize_citation_markers(
    answer: str,
) -> str:
    """Normalize supported citation formatting variations."""

    return _LOOSE_CITATION_PATTERN.sub(
        lambda match: (
            f"[Source {int(match.group(1))}]"
        ),
        answer,
    )