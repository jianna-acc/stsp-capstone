# File: /backend/app/services/quiz_generation.py

# Purpose: Generates and validates source-grounded structured
# Quizzes through the shared provider-independent AI contract.

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

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
from app.ai.quiz_prompt import (
    QuizPrompt,
    QuizPromptBuilder,
    QuizPromptError,
)
from app.schemas.quiz import (
    QuizGeneratedContent,
    QuizGenerateRequest,
    QuizQuestionType,
    QuizType,
)
from app.services.quiz_errors import (
    QuizGenerationError,
    QuizGenerationResponseError,
)
from app.services.quiz_source_loader import (
    QuizSourceBundle,
)

DEFAULT_QUIZ_TEMPERATURE = 0.2

STANDARD_QUIZ_OUTPUT_TOKENS = 4_096
LARGE_QUIZ_OUTPUT_TOKENS = 8_192

STANDARD_QUIZ_QUESTION_LIMIT = 10


class ClosableGenerationProvider(
    Protocol,
):
    """Optional provider resource-cleanup interface."""

    async def aclose(
        self,
    ) -> None:
        """Release provider resources."""


@dataclass(
    frozen=True,
    slots=True,
)
class QuizGenerationResult:
    """Validated result of one Quiz generation operation."""

    content: QuizGeneratedContent

    provider: str
    model: str

    input_tokens: int | None
    output_tokens: int | None

    generation_attempt_count: int

    source_character_count: int
    source_chunk_count: int
    source_file_count: int


class QuizGenerationService:
    """Generate validated Quiz content through the shared provider."""

    def __init__(
        self,
        *,
        provider: GenerationProvider,
        prompt_builder: QuizPromptBuilder | None = None,
    ) -> None:
        self._provider = provider

        self._prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else QuizPromptBuilder()
        )

    async def generate(
        self,
        *,
        request: QuizGenerateRequest,
        source_bundle: QuizSourceBundle,
    ) -> QuizGenerationResult:
        """Generate and validate one Quiz."""

        try:
            prompt = self._prompt_builder.build(
                request=request,
                source_bundle=source_bundle,
            )

        except QuizPromptError as exc:
            raise QuizGenerationError(
                "Unable to build the Quiz generation prompt.",
            ) from exc

        max_output_tokens = self._output_token_budget(
            request.question_count,
        )

        generation_request = GenerationRequest(
            prompt=prompt.user_prompt,
            system_instruction=prompt.system_instruction,
            temperature=DEFAULT_QUIZ_TEMPERATURE,
            max_output_tokens=max_output_tokens,
        )

        first_result = await self._generate_once(
            generation_request,
        )

        try:
            content = self._validate_generation_result(
                result=first_result,
                request=request,
            )

        except QuizGenerationResponseError:
            content = None

        if content is not None:
            return self._build_result(
                content=content,
                generation_result=first_result,
                prompt=prompt,
                generation_attempt_count=1,
            )

        repair_request = GenerationRequest(
            prompt=self._build_repair_prompt(
                original_prompt=prompt.user_prompt,
                invalid_response=first_result.text,
                request=request,
            ),
            system_instruction=prompt.system_instruction,
            temperature=DEFAULT_QUIZ_TEMPERATURE,
            max_output_tokens=max_output_tokens,
        )

        repaired_result = await self._generate_once(
            repair_request,
        )

        try:
            repaired_content = (
                self._validate_generation_result(
                    result=repaired_result,
                    request=request,
                )
            )

        except QuizGenerationResponseError as exc:
            raise QuizGenerationResponseError(
                "Quiz generation returned invalid structured "
                "output after one repair attempt.",
            ) from exc

        return self._build_result(
            content=repaired_content,
            generation_result=repaired_result,
            prompt=prompt,
            generation_attempt_count=2,
        )

    async def aclose(
        self,
    ) -> None:
        """Release provider resources when supported."""

        close_method = getattr(
            self._provider,
            "aclose",
            None,
        )

        if close_method is None:
            return

        await close_method()

    async def _generate_once(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """Execute one controlled provider request."""

        try:
            result = await self._provider.generate(
                request,
            )

        except (
            AIProviderConfigurationError,
            AIProviderRequestError,
            AIProviderResponseError,
        ) as exc:
            raise QuizGenerationError(
                "The AI provider could not generate the Quiz.",
            ) from exc

        except Exception as exc:
            raise QuizGenerationError(
                "Quiz generation failed unexpectedly.",
            ) from exc

        if not isinstance(
            result,
            GenerationResult,
        ):
            raise QuizGenerationResponseError(
                "The AI provider returned an invalid "
                "generation result.",
            )

        expected_provider = (
            self._provider.provider_name
        )

        if result.provider != expected_provider:
            raise QuizGenerationResponseError(
                "The AI generation provider identity "
                "did not match the configured provider.",
            )

        return result

    def _validate_generation_result(
        self,
        *,
        result: GenerationResult,
        request: QuizGenerateRequest,
    ) -> QuizGeneratedContent:
        """Parse and validate one provider Quiz response."""

        payload = self._parse_json_object(
            result.text,
        )

        try:
            content = (
                QuizGeneratedContent.model_validate(
                    payload,
                )
            )

        except ValidationError as exc:
            raise QuizGenerationResponseError(
                "The AI response did not match the "
                "Quiz output contract.",
            ) from exc

        if (
            len(
                content.questions,
            )
            != request.question_count
        ):
            raise QuizGenerationResponseError(
                "The AI response did not contain the "
                "requested number of Quiz questions.",
            )

        self._validate_requested_question_types(
            content=content,
            request=request,
        )

        self._validate_no_duplicate_questions(
            content,
        )

        return content

    def _validate_requested_question_types(
        self,
        *,
        content: QuizGeneratedContent,
        request: QuizGenerateRequest,
    ) -> None:
        """Ensure generated question composition matches the request."""

        generated_types = [
            question.question_type
            for question in content.questions
        ]

        if request.quiz_type == QuizType.MIXED:
            unique_types = set(
                generated_types,
            )

            if (
                request.question_count >= 3
                and unique_types
                != {
                    QuizQuestionType.MULTIPLE_CHOICE,
                    QuizQuestionType.TRUE_FALSE,
                    QuizQuestionType.IDENTIFICATION,
                }
            ):
                raise QuizGenerationResponseError(
                    "The mixed Quiz did not contain all "
                    "required question types.",
                )

            if (
                request.question_count == 2
                and len(
                    unique_types,
                )
                < 2
            ):
                raise QuizGenerationResponseError(
                    "The mixed Quiz did not contain "
                    "two different question types.",
                )

            return

        expected_type = {
            QuizType.MULTIPLE_CHOICE: (
                QuizQuestionType.MULTIPLE_CHOICE
            ),
            QuizType.TRUE_FALSE: (
                QuizQuestionType.TRUE_FALSE
            ),
            QuizType.IDENTIFICATION: (
                QuizQuestionType.IDENTIFICATION
            ),
        }[
            request.quiz_type
        ]

        if any(
            question_type != expected_type
            for question_type in generated_types
        ):
            raise QuizGenerationResponseError(
                "The generated Quiz question types did "
                "not match the requested Quiz type.",
            )

    def _validate_no_duplicate_questions(
        self,
        content: QuizGeneratedContent,
    ) -> None:
        """Reject exact or whitespace/case-equivalent questions."""

        seen: set[
            str
        ] = set()

        for question in content.questions:
            signature = self._normalize_duplicate_text(
                question.question,
            )

            if signature in seen:
                raise QuizGenerationResponseError(
                    "The AI response contained duplicate "
                    "Quiz questions.",
                )

            seen.add(
                signature,
            )

    def _parse_json_object(
        self,
        raw_text: str,
    ) -> dict[
        str,
        object,
    ]:
        """Parse provider text as exactly one JSON object."""

        if not isinstance(
            raw_text,
            str,
        ):
            raise QuizGenerationResponseError(
                "The AI response text was invalid.",
            )

        normalized = raw_text.strip()

        if not normalized:
            raise QuizGenerationResponseError(
                "The AI provider returned an empty response.",
            )

        normalized = self._strip_markdown_fence(
            normalized,
        )

        try:
            payload = json.loads(
                normalized,
            )

        except json.JSONDecodeError as exc:
            raise QuizGenerationResponseError(
                "The AI provider returned malformed JSON.",
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise QuizGenerationResponseError(
                "The Quiz AI response must be a JSON object.",
            )

        return payload

    def _strip_markdown_fence(
        self,
        text: str,
    ) -> str:
        """Remove one complete Markdown JSON fence if present."""

        normalized = text.strip()

        if not normalized.startswith(
            "```",
        ):
            return normalized

        lines = normalized.splitlines()

        if len(
            lines,
        ) < 3:
            return normalized

        first_line = lines[
            0
        ].strip().lower()

        last_line = lines[
            -1
        ].strip()

        if (
            first_line
            not in {
                "```",
                "```json",
            }
            or last_line != "```"
        ):
            return normalized

        return "\n".join(
            lines[
                1:-1
            ]
        ).strip()

    def _normalize_duplicate_text(
        self,
        value: str,
    ) -> str:
        """Normalize question text for duplicate comparison."""

        return " ".join(
            value.casefold().split()
        )

    def _output_token_budget(
        self,
        question_count: int,
    ) -> int:
        """Choose a safe output budget for Quiz size."""

        if (
            question_count
            <= STANDARD_QUIZ_QUESTION_LIMIT
        ):
            return STANDARD_QUIZ_OUTPUT_TOKENS

        return LARGE_QUIZ_OUTPUT_TOKENS

    def _build_repair_prompt(
        self,
        *,
        original_prompt: str,
        invalid_response: str,
        request: QuizGenerateRequest,
    ) -> str:
        """Build one bounded structured-output repair request."""

        return (
            "REPAIR_REQUEST\n\n"
            "The previous response did not satisfy the "
            "required Quiz JSON contract.\n"
            f"Generate exactly {request.question_count} questions.\n"
            f"Quiz type must remain {request.quiz_type.value}.\n"
            f"Difficulty must remain {request.difficulty.value}.\n"
            "Return valid JSON only.\n"
            "Do not include Markdown fences or commentary.\n"
            "Do not add outside knowledge.\n"
            "Do not include duplicate questions.\n"
            "Ensure every question follows the required "
            "question-type structure.\n\n"
            "ORIGINAL_GENERATION_REQUEST:\n"
            f"{original_prompt}\n\n"
            "INVALID_RESPONSE:\n"
            f"{invalid_response}"
        )

    def _build_result(
        self,
        *,
        content: QuizGeneratedContent,
        generation_result: GenerationResult,
        prompt: QuizPrompt,
        generation_attempt_count: int,
    ) -> QuizGenerationResult:
        """Return normalized Quiz generation metadata."""

        return QuizGenerationResult(
            content=content,
            provider=generation_result.provider,
            model=generation_result.model,
            input_tokens=generation_result.input_tokens,
            output_tokens=generation_result.output_tokens,
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