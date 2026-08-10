# File: /backend/app/services/flashcard_generation.py
# Purpose: Generates validated source-grounded Flashcards through
# single-pass or bounded multi-pass AI generation.

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
    AIProviderRequestError,
)
from app.ai.flashcard_prompt import (
    MAX_FLASHCARD_MAX_SOURCE_CHARACTERS,
    FlashcardPrompt,
    FlashcardPromptBuilder,
    FlashcardPromptError,
)
from app.schemas.flashcard import (
    FlashcardContent,
    FlashcardGenerateRequest,
)
from app.services.flashcard_batching import (
    FlashcardBatchingError,
    FlashcardSourceBatcher,
)
from app.services.flashcard_errors import (
    FlashcardGenerationError,
    FlashcardGenerationResponseError,
)
from app.services.flashcard_source_loader import (
    FlashcardSourceBundle,
)

DEFAULT_FLASHCARD_TEMPERATURE = 0.2

STANDARD_FLASHCARD_OUTPUT_TOKENS = 4_096
LARGE_FLASHCARD_OUTPUT_TOKENS = 8_192

STANDARD_FLASHCARD_CARD_LIMIT = 20


class ClosableGenerationProvider(
    Protocol,
):
    async def aclose(
        self,
    ) -> None:
        """Release provider resources."""


@dataclass(
    frozen=True,
    slots=True,
)
class FlashcardGenerationResult:
    """Validated result of one Flashcard generation operation."""

    content: FlashcardContent

    provider: str
    model: str

    input_tokens: int | None
    output_tokens: int | None

    generation_attempt_count: int

    source_character_count: int
    source_chunk_count: int
    source_file_count: int


class FlashcardGenerationService:
    """Generate structured Flashcards using the shared AI provider."""

    def __init__(
        self,
        *,
        provider: GenerationProvider,
        prompt_builder: FlashcardPromptBuilder | None = None,
        source_batcher: FlashcardSourceBatcher | None = None,
    ) -> None:
        self._provider = provider

        self._prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else FlashcardPromptBuilder()
        )

        self._source_batcher = (
            source_batcher
            if source_batcher is not None
            else FlashcardSourceBatcher()
        )

    async def generate(
        self,
        *,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> FlashcardGenerationResult:
        """Generate and validate one Flashcard deck."""

        if (
            source_bundle.character_count
            > MAX_FLASHCARD_MAX_SOURCE_CHARACTERS
        ):
            return await self._generate_large_material(
                request=request,
                source_bundle=source_bundle,
            )

        return await self._generate_single_pass(
            request=request,
            source_bundle=source_bundle,
        )

    async def _generate_single_pass(
        self,
        *,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> FlashcardGenerationResult:
        """Generate a deck from one complete bounded prompt."""

        try:
            prompt = self._prompt_builder.build(
                request=request,
                source_bundle=source_bundle,
            )

        except FlashcardPromptError as exc:
            raise FlashcardGenerationError(
                "Unable to build the Flashcard generation prompt.",
            ) from exc

        (
            content,
            generation_result,
            generation_attempt_count,
        ) = await self._generate_validated_content(
            prompt=prompt,
            requested_card_count=request.card_count,
        )

        return self._build_result(
            content=content,
            generation_result=generation_result,
            prompt=prompt,
            generation_attempt_count=(
                generation_attempt_count
            ),
        )

    async def _generate_large_material(
        self,
        *,
        request: FlashcardGenerateRequest,
        source_bundle: FlashcardSourceBundle,
    ) -> FlashcardGenerationResult:
        """Generate partial decks then synthesize one final deck."""

        try:
            source_batches = (
                self._source_batcher.partition(
                    source_bundle,
                )
            )

        except FlashcardBatchingError as exc:
            raise FlashcardGenerationError(
                "Unable to batch the Flashcard source material.",
            ) from exc

        partial_contents: list[
            FlashcardContent
        ] = []

        total_batch_count = len(
            source_batches,
        )

        for source_batch in source_batches:
            try:
                batch_prompt = (
                    self._prompt_builder.build_batch(
                        request=request,
                        source_bundle=source_bundle,
                        source_batch=source_batch,
                        total_batch_count=(
                            total_batch_count
                        ),
                    )
                )

            except FlashcardPromptError as exc:
                raise FlashcardGenerationError(
                    "Unable to build a Flashcard batch prompt.",
                ) from exc

            (
                partial_content,
                _,
                _,
            ) = await self._generate_validated_content(
                prompt=batch_prompt,
                requested_card_count=request.card_count,
            )

            partial_contents.append(
                partial_content,
            )

        try:
            synthesis_prompt = (
                self._prompt_builder.build_synthesis(
                    request=request,
                    source_bundle=source_bundle,
                    partial_contents=tuple(
                        partial_contents,
                    ),
                )
            )

        except FlashcardPromptError as exc:
            raise FlashcardGenerationError(
                "Unable to build the Flashcard synthesis prompt.",
            ) from exc

        (
            final_content,
            final_generation_result,
            final_attempt_count,
        ) = await self._generate_validated_content(
            prompt=synthesis_prompt,
            requested_card_count=request.card_count,
        )

        return self._build_result(
            content=final_content,
            generation_result=(
                final_generation_result
            ),
            prompt=synthesis_prompt,
            generation_attempt_count=(
                final_attempt_count
            ),
        )

    async def _generate_validated_content(
        self,
        *,
        prompt: FlashcardPrompt,
        requested_card_count: int,
    ) -> tuple[
        FlashcardContent,
        GenerationResult,
        int,
    ]:
        """Generate one validated response with one repair maximum."""

        max_output_tokens = (
            self._output_token_budget(
                requested_card_count,
            )
        )

        generation_request = (
            GenerationRequest(
                prompt=prompt.user_prompt,
                system_instruction=(
                    prompt.system_instruction
                ),
                temperature=(
                    DEFAULT_FLASHCARD_TEMPERATURE
                ),
                max_output_tokens=(
                    max_output_tokens
                ),
            )
        )

        first_result = await self._generate_once(
            generation_request,
        )

        try:
            content = (
                self._validate_generation_result(
                    result=first_result,
                    requested_card_count=(
                        requested_card_count
                    ),
                )
            )

        except FlashcardGenerationResponseError:
            repair_request = (
                GenerationRequest(
                    prompt=self._build_repair_prompt(
                        original_prompt=(
                            prompt.user_prompt
                        ),
                        invalid_response=(
                            first_result.text
                        ),
                        requested_card_count=(
                            requested_card_count
                        ),
                    ),
                    system_instruction=(
                        prompt.system_instruction
                    ),
                    temperature=(
                        DEFAULT_FLASHCARD_TEMPERATURE
                    ),
                    max_output_tokens=(
                        max_output_tokens
                    ),
                )
            )

            repaired_result = (
                await self._generate_once(
                    repair_request,
                )
            )

            try:
                repaired_content = (
                    self._validate_generation_result(
                        result=repaired_result,
                        requested_card_count=(
                            requested_card_count
                        ),
                    )
                )

            except FlashcardGenerationResponseError as exc:
                raise FlashcardGenerationResponseError(
                    "Flashcard generation returned invalid "
                    "structured output after one repair attempt.",
                ) from exc

            return (
                repaired_content,
                repaired_result,
                2,
            )

        return (
            content,
            first_result,
            1,
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

        except AIProviderRequestError as exc:
            raise FlashcardGenerationError(
                "The AI provider could not generate Flashcards.",
            ) from exc

        except Exception as exc:
            raise FlashcardGenerationError(
                "Flashcard generation failed unexpectedly.",
            ) from exc

        if not isinstance(
            result,
            GenerationResult,
        ):
            raise FlashcardGenerationResponseError(
                "The AI provider returned an invalid "
                "generation result.",
            )

        expected_provider = (
            self._provider.provider_name
        )

        if (
            result.provider
            != expected_provider
        ):
            raise FlashcardGenerationResponseError(
                "The AI generation provider identity "
                "did not match the configured provider.",
            )

        return result

    def _validate_generation_result(
        self,
        *,
        result: GenerationResult,
        requested_card_count: int,
    ) -> FlashcardContent:
        """Parse and validate one provider Flashcard response."""

        payload = self._parse_json_object(
            result.text,
        )

        try:
            content = (
                FlashcardContent.model_validate(
                    payload,
                )
            )

        except ValidationError as exc:
            raise FlashcardGenerationResponseError(
                "The AI response did not match the "
                "Flashcard output contract.",
            ) from exc

        if (
            len(
                content.cards,
            )
            != requested_card_count
        ):
            raise FlashcardGenerationResponseError(
                "The AI response did not contain the "
                "requested number of Flashcards.",
            )

        self._validate_no_exact_duplicates(
            content,
        )

        return content

    def _parse_json_object(
        self,
        raw_text: str,
    ) -> dict[
        str,
        object,
    ]:
        """Parse provider text as one JSON object."""

        if not isinstance(
            raw_text,
            str,
        ):
            raise FlashcardGenerationResponseError(
                "The AI response text was invalid.",
            )

        normalized = raw_text.strip()

        if not normalized:
            raise FlashcardGenerationResponseError(
                "The AI provider returned an empty response.",
            )

        normalized = (
            self._strip_markdown_fence(
                normalized,
            )
        )

        try:
            payload = json.loads(
                normalized,
            )

        except json.JSONDecodeError as exc:
            raise FlashcardGenerationResponseError(
                "The AI provider returned malformed JSON.",
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise FlashcardGenerationResponseError(
                "The Flashcard AI response must be "
                "a JSON object.",
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

        first_line = (
            lines[
                0
            ]
            .strip()
            .lower()
        )

        last_line = (
            lines[
                -1
            ].strip()
        )

        if (
            first_line
            not in {
                "```",
                "```json",
            }
            or last_line
            != "```"
        ):
            return normalized

        return "\n".join(
            lines[
                1:-1
            ]
        ).strip()

    def _validate_no_exact_duplicates(
        self,
        content: FlashcardContent,
    ) -> None:
        """Reject exact or whitespace/case-equivalent cards."""

        seen: set[
            tuple[
                str,
                str,
            ]
        ] = set()

        for card in content.cards:
            signature = (
                self._normalize_duplicate_text(
                    card.question,
                ),
                self._normalize_duplicate_text(
                    card.answer,
                ),
            )

            if signature in seen:
                raise FlashcardGenerationResponseError(
                    "The AI response contained duplicate "
                    "Flashcards.",
                )

            seen.add(
                signature,
            )

    def _normalize_duplicate_text(
        self,
        value: str,
    ) -> str:
        """Normalize Flashcard text for duplicate comparison."""

        return " ".join(
            value.casefold().split()
        )

    def _output_token_budget(
        self,
        card_count: int,
    ) -> int:
        """Select a safe output budget from requested deck size."""

        if (
            card_count
            <= STANDARD_FLASHCARD_CARD_LIMIT
        ):
            return (
                STANDARD_FLASHCARD_OUTPUT_TOKENS
            )

        return (
            LARGE_FLASHCARD_OUTPUT_TOKENS
        )

    def _build_repair_prompt(
        self,
        *,
        original_prompt: str,
        invalid_response: str,
        requested_card_count: int,
    ) -> str:
        """Build one bounded repair instruction."""

        return (
            "REPAIR_REQUEST\n\n"
            "The previous response did not satisfy the "
            "required Flashcard JSON contract.\n"
            f"Generate exactly {requested_card_count} flashcards.\n"
            "Return valid JSON only.\n"
            "Do not include Markdown fences or commentary.\n"
            "Do not add outside knowledge.\n"
            "Do not include duplicate Flashcards.\n\n"
            "ORIGINAL_GENERATION_REQUEST:\n"
            f"{original_prompt}\n\n"
            "INVALID_RESPONSE:\n"
            f"{invalid_response}"
        )

    def _build_result(
        self,
        *,
        content: FlashcardContent,
        generation_result: GenerationResult,
        prompt: FlashcardPrompt,
        generation_attempt_count: int,
    ) -> FlashcardGenerationResult:
        """Return normalized generation metadata."""

        return FlashcardGenerationResult(
            content=content,
            provider=(
                generation_result.provider
            ),
            model=(
                generation_result.model
            ),
            input_tokens=(
                generation_result.input_tokens
            ),
            output_tokens=(
                generation_result.output_tokens
            ),
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