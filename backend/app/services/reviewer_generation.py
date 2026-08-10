# File: /backend/app/services/reviewer_generation.py
# Purpose: Generates and validates structured reviewer content
# using single-pass or batched large-material generation.

from __future__ import annotations

import json
import logging
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
from app.services.reviewer_batching import (
    ReviewerSourceBatcher,
)
from app.services.reviewer_errors import (
    ReviewerGenerationError,
    ReviewerGenerationResponseError,
    ReviewerValidationError,
)
from app.services.reviewer_source_loader import (
    ReviewerSourceBundle,
)

logger = logging.getLogger(
    __name__,
)

_REVIEWER_TEMPERATURE: Final = 0.2

_REVIEWER_OUTPUT_TOKENS: Final = {
    ReviewerLength.SHORT: 4_096,
    ReviewerLength.MEDIUM: 8_192,
    ReviewerLength.LONG: 8_192,
}

_SINGLE_PASS_TOO_LARGE_MESSAGE: Final = (
    "The selected study material is too large for "
    "single-pass reviewer generation."
)


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
        source_batcher: ReviewerSourceBatcher | None = None,
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

        if (
            source_batcher is not None
            and not isinstance(
                source_batcher,
                ReviewerSourceBatcher,
            )
        ):
            raise ReviewerValidationError(
                "source_batcher must be a ReviewerSourceBatcher.",
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

        self._source_batcher = (
            source_batcher
            if source_batcher is not None
            else ReviewerSourceBatcher()
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
            if str(
                exc,
            ) != _SINGLE_PASS_TOO_LARGE_MESSAGE:
                raise ReviewerValidationError(
                    str(
                        exc,
                    ),
                ) from exc

            return await self._generate_large_material(
                request=request,
                source_bundle=source_bundle,
            )

        content, provider_result, attempt_count = (
            await self._generate_from_prompt(
                prompt=prompt,
                reviewer_length=request.reviewer_length,
            )
        )

        return self._build_result(
            content=content,
            provider_result=provider_result,
            prompt=prompt,
            generation_attempt_count=attempt_count,
        )

    async def _generate_large_material(
        self,
        *,
        request: ReviewerGenerateRequest,
        source_bundle: ReviewerSourceBundle,
    ) -> ReviewerGenerationResult:
        """Generate partial reviewers and synthesize one final result."""

        batches = self._source_batcher.partition(
            source_bundle,
        )

        partial_reviewers: list[
            ReviewerContent
        ] = []

        total_batch_count = len(
            batches,
        )

        for source_batch in batches:
            try:
                batch_prompt = (
                    self._prompt_builder.build_batch(
                        request=request,
                        source_bundle=source_bundle,
                        source_batch=source_batch,
                        total_batch_count=total_batch_count,
                    )
                )

            except ReviewerPromptError as exc:
                raise ReviewerValidationError(
                    str(
                        exc,
                    ),
                ) from exc

            (
                partial_content,
                _,
                _,
            ) = await self._generate_from_prompt(
                prompt=batch_prompt,
                reviewer_length=request.reviewer_length,
            )

            partial_reviewers.append(
                partial_content,
            )

        try:
            synthesis_prompt = (
                self._prompt_builder.build_synthesis(
                    request=request,
                    source_bundle=source_bundle,
                    partial_reviewers=tuple(
                        partial_reviewers,
                    ),
                )
            )

        except ReviewerPromptError as exc:
            raise ReviewerValidationError(
                str(
                    exc,
                ),
            ) from exc

        (
            final_content,
            final_provider_result,
            final_attempt_count,
        ) = await self._generate_from_prompt(
            prompt=synthesis_prompt,
            reviewer_length=request.reviewer_length,
        )

        return self._build_result(
            content=final_content,
            provider_result=final_provider_result,
            prompt=synthesis_prompt,
            generation_attempt_count=(
                final_attempt_count
            ),
        )

    async def _generate_from_prompt(
        self,
        *,
        prompt: ReviewerPrompt,
        reviewer_length: ReviewerLength,
    ) -> tuple[
        ReviewerContent,
        GenerationResult,
        int,
    ]:
        """Generate validated reviewer content from one prompt."""

        first_result = await self._generate_provider_result(
            prompt=prompt,
            reviewer_length=reviewer_length,
        )

        try:
            content = self._parse_content(
                first_result.text,
            )

        except ReviewerGenerationResponseError as exc:
            logger.warning(
                "Reviewer generation response rejected "
                "on attempt 1: %s",
                exc,
            )

            repair_prompt = self._build_repair_prompt(
                prompt=prompt,
                invalid_response=first_result.text,
            )

            repaired_result = (
                await self._generate_provider_result(
                    prompt=repair_prompt,
                    reviewer_length=reviewer_length,
                )
            )

            try:
                content = self._parse_content(
                    repaired_result.text,
                )

            except ReviewerGenerationResponseError as repair_exc:
                logger.warning(
                    "Reviewer generation response rejected "
                    "on attempt 2: %s",
                    repair_exc,
                )

                raise

            return (
                content,
                repaired_result,
                2,
            )

        return (
            content,
            first_result,
            1,
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

        if (
            normalized.startswith("```")
            and normalized.endswith("```")
        ):
            lines = normalized.splitlines()

            if len(
                lines,
            ) >= 3:
                normalized = "\n".join(
                    lines[
                        1:-1
                    ],
                ).strip()

        if not normalized:
            raise ReviewerGenerationResponseError(
                "The generated reviewer response was empty.",
            )

        try:
            payload = json.loads(
                normalized,
            )

        except json.JSONDecodeError as exc:
            logger.warning(
                "Reviewer JSON decode failed: "
                "message=%s line=%s column=%s position=%s "
                "response_length=%s ends_with_brace=%s",
                exc.msg,
                exc.lineno,
                exc.colno,
                exc.pos,
                len(
                    normalized,
                ),
                normalized.endswith(
                    "}",
                ),
            )

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
            validation_issues = [
                {
                    "location": ".".join(
                        str(part)
                        for part in issue["loc"]
                    ),
                    "type": issue["type"],
                    "message": issue["msg"],
                }
                for issue in exc.errors(
                    include_input=False,
                    include_url=False,
                )
            ]

            logger.warning(
                "Reviewer structure validation failed: %s",
                validation_issues,
            )

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
            "using the same supplied study information. Return one "
            "valid JSON object only. Do not use Markdown code "
            "fences, comments, or explanatory text.\n\n"
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