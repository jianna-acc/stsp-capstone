# File: /backend/app/services/reviewer_generation.py
# Purpose: Generates and validates structured reviewer content
# from complete study-material source bundles.

from __future__ import annotations

import json
from dataclasses import dataclass
from inspect import isawaitable
from typing import Final

from pydantic import ValidationError

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
from app.ai.reviewer_prompt import (
    ReviewerPrompt,
    ReviewerPromptBuilder,
    ReviewerPromptError,
)
from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerGenerateRequest,
    ReviewerLength,
)
from app.services.reviewer_errors import (
    ReviewerGenerationError,
    ReviewerGenerationResponseError,
    ReviewerValidationError,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
)

_REVIEWER_TEMPERATURE: Final = 0.2

_REVIEWER_OUTPUT_TOKENS: Final = {
    ReviewerLength.SHORT: 2_048,
    ReviewerLength.MEDIUM: 4_096,
    ReviewerLength.LONG: 6_144,
}


@dataclass(
    frozen=True,
    slots=True,
)
class ReviewerGenerationResult:
    """Validated reviewer content and generation metadata."""

    content: ReviewerContent
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    generation_attempt_count: int
    source_character_count: int
    source_chunk_count: int
    source_file_count: int

    def __post_init__(
        self,
    ) -> None:
        """Validate generation result metadata."""

        normalized_provider = self.provider.strip()
        normalized_model = self.model.strip()

        if not normalized_provider:
            raise ReviewerGenerationResponseError(
                "Reviewer generation provider must not be empty.",
            )

        if not normalized_model:
            raise ReviewerGenerationResponseError(
                "Reviewer generation model must not be empty.",
            )

        if self.generation_attempt_count not in {
            1,
            2,
        }:
            raise ReviewerGenerationResponseError(
                "Reviewer generation attempt count is invalid.",
            )

        if self.source_character_count < 1:
            raise ReviewerGenerationResponseError(
                "Reviewer generation source size is invalid.",
            )

        if self.source_chunk_count < 1:
            raise ReviewerGenerationResponseError(
                "Reviewer generation source chunk count is invalid.",
            )

        if self.source_file_count < 1:
            raise ReviewerGenerationResponseError(
                "Reviewer generation source file count is invalid.",
            )

        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )

        object.__setattr__(
            self,
            "model",
            normalized_model,
        )


class ReviewerGenerationService:
    """Generate structured reviewers through a text provider."""

    def __init__(
        self,
        *,
        provider: GenerationProvider,
        prompt_builder: ReviewerPromptBuilder | None = None,
        temperature: float = _REVIEWER_TEMPERATURE,
    ) -> None:
        if not isinstance(
            provider,
            GenerationProvider,
        ):
            raise ReviewerValidationError(
                "provider must implement GenerationProvider.",
            )

        if (
            prompt_builder is not None
            and not isinstance(
                prompt_builder,
                ReviewerPromptBuilder,
            )
        ):
            raise ReviewerValidationError(
                "prompt_builder must be a ReviewerPromptBuilder.",
            )

        try:
            GenerationRequest(
                prompt="Validate reviewer generation settings.",
                temperature=temperature,
                max_output_tokens=2_048,
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ReviewerValidationError(
                "Reviewer generation settings are invalid.",
            ) from exc

        self._provider = provider

        self._prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else ReviewerPromptBuilder()
        )

        self._temperature = temperature

    async def generate(
        self,
        *,
        request: ReviewerGenerateRequest,
        source_bundle: ReviewerSourceBundle,
    ) -> ReviewerGenerationResult:
        """Generate and validate one structured reviewer."""

        if not isinstance(
            request,
            ReviewerGenerateRequest,
        ):
            raise ReviewerValidationError(
                "request must be a ReviewerGenerateRequest.",
            )

        if not isinstance(
            source_bundle,
            ReviewerSourceBundle,
        ):
            raise ReviewerValidationError(
                "source_bundle must be a ReviewerSourceBundle.",
            )

        try:
            prompt = self._prompt_builder.build(
                request=request,
                source_bundle=source_bundle,
            )

        except ReviewerPromptError as exc:
            raise ReviewerValidationError(
                str(
                    exc,
                ),
            ) from exc

        first_result = await self._generate_provider_result(
            prompt=prompt,
            reviewer_length=request.reviewer_length,
        )

        try:
            content = self._parse_content(
                first_result.text,
            )

        except ReviewerGenerationResponseError:
            repair_prompt = self._build_repair_prompt(
                prompt=prompt,
                invalid_response=first_result.text,
            )

            repaired_result = (
                await self._generate_provider_result(
                    prompt=repair_prompt,
                    reviewer_length=(
                        request.reviewer_length
                    ),
                )
            )

            content = self._parse_content(
                repaired_result.text,
            )

            return self._build_result(
                content=content,
                provider_result=repaired_result,
                prompt=prompt,
                generation_attempt_count=2,
            )

        return self._build_result(
            content=content,
            provider_result=first_result,
            prompt=prompt,
            generation_attempt_count=1,
        )

    async def _generate_provider_result(
        self,
        *,
        prompt: ReviewerPrompt,
        reviewer_length: ReviewerLength,
    ) -> GenerationResult:
        """Request one reviewer response from the provider."""

        max_output_tokens = _REVIEWER_OUTPUT_TOKENS[
            reviewer_length
        ]

        try:
            generation_request = GenerationRequest(
                prompt=prompt.user_prompt,
                system_instruction=(
                    prompt.system_instruction
                ),
                temperature=self._temperature,
                max_output_tokens=max_output_tokens,
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ReviewerValidationError(
                "The reviewer generation request is invalid.",
            ) from exc

        try:
            result = await self._provider.generate(
                generation_request,
            )

        except (
            AIProviderConfigurationError,
            AIProviderRequestError,
            AIProviderResponseError,
        ) as exc:
            raise ReviewerGenerationError(
                "The AI provider could not generate "
                "the reviewer.",
            ) from exc

        except Exception as exc:
            raise ReviewerGenerationError(
                "An unexpected reviewer generation "
                "failure occurred.",
            ) from exc

        self._validate_provider_result(
            result,
        )

        return result

    def _parse_content(
        self,
        response_text: str,
    ) -> ReviewerContent:
        """Parse strict provider JSON into ReviewerContent."""

        normalized = response_text.strip()

        if not normalized:
            raise ReviewerGenerationResponseError(
                "The generated reviewer response was empty.",
            )

        try:
            payload = json.loads(
                normalized,
            )

        except json.JSONDecodeError as exc:
            raise ReviewerGenerationResponseError(
                "The generated reviewer was not valid JSON.",
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise ReviewerGenerationResponseError(
                "The generated reviewer must be a JSON object.",
            )

        try:
            return ReviewerContent.model_validate(
                payload,
            )

        except ValidationError as exc:
            raise ReviewerGenerationResponseError(
                "The generated reviewer did not match "
                "the required structure.",
            ) from exc

    def _build_repair_prompt(
        self,
        *,
        prompt: ReviewerPrompt,
        invalid_response: str,
    ) -> ReviewerPrompt:
        """Create one bounded JSON-repair generation request."""

        repair_instruction = (
            "\n\nREPAIR_REQUEST:\n"
            "Your previous response did not satisfy the required "
            "reviewer JSON contract. Generate the reviewer again "
            "from the same SOURCE_DATA_JSON. Return one valid JSON "
            "object only. Do not use Markdown code fences, comments, "
            "or explanatory text.\n\n"
            "INVALID_PREVIOUS_RESPONSE:\n"
            f"{invalid_response.strip()}"
        )

        return ReviewerPrompt(
            request=prompt.request,
            source_bundle=prompt.source_bundle,
            system_instruction=prompt.system_instruction,
            user_prompt=(
                prompt.user_prompt
                + repair_instruction
            ),
            source_character_count=(
                prompt.source_character_count
            ),
            source_chunk_count=(
                prompt.source_chunk_count
            ),
            source_file_count=(
                prompt.source_file_count
            ),
        )

    def _validate_provider_result(
        self,
        result: object,
    ) -> None:
        """Validate provider identity and response contract."""

        if not isinstance(
            result,
            GenerationResult,
        ):
            raise ReviewerGenerationResponseError(
                "The AI provider returned an invalid "
                "reviewer generation result.",
            )

        provider_name = getattr(
            self._provider,
            "provider_name",
            None,
        )

        if (
            not isinstance(
                provider_name,
                str,
            )
            or not provider_name.strip()
        ):
            raise ReviewerGenerationResponseError(
                "The reviewer generation provider name "
                "is invalid.",
            )

        if (
            result.provider
            != provider_name.strip()
        ):
            raise ReviewerGenerationResponseError(
                "The reviewer generation result provider "
                "does not match the configured provider.",
            )

    def _build_result(
        self,
        *,
        content: ReviewerContent,
        provider_result: GenerationResult,
        prompt: ReviewerPrompt,
        generation_attempt_count: int,
    ) -> ReviewerGenerationResult:
        """Build one validated generation result."""

        return ReviewerGenerationResult(
            content=content,
            provider=provider_result.provider,
            model=provider_result.model,
            input_tokens=provider_result.input_tokens,
            output_tokens=provider_result.output_tokens,
            generation_attempt_count=(
                generation_attempt_count
            ),
            source_character_count=(
                prompt.source_character_count
            ),
            source_chunk_count=(
                prompt.source_chunk_count
            ),
            source_file_count=(
                prompt.source_file_count
            ),
        )

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