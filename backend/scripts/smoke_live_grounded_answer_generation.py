# File: /backend/scripts/smoke_live_grounded_answer_generation.py

from __future__ import annotations

import asyncio
import os
import re
from typing import Final
from uuid import UUID

from app.ai.grounded_answer_contracts import (
    GroundedAnswerError,
    GroundedAnswerOutcome,
    GroundedAnswerRequest,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from app.api.grounded_answer_generation_dependency import (
    get_grounded_answer_generation_service,
)
from app.api.query_embedding_dependency import (
    get_query_embedding_service,
)
from app.api.retrieval_orchestration_dependency import (
    get_retrieval_orchestration_service,
)
from app.core.config import get_settings
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
)

DEFAULT_QUESTION: Final = (
    "What is one important concept explained in this "
    "study material?"
)

DEFAULT_MATCH_COUNT: Final = 5
DEFAULT_SIMILARITY_THRESHOLD: Final = 0.0

_CITATION_PATTERN: Final = re.compile(
    r"\[Source [1-9]\d*\]"
)


class LiveGroundedAnswerSmokeError(RuntimeError):
    """Controlled failure for the live smoke workflow."""

    error_code = "LIVE_GROUNDED_ANSWER_SMOKE_FAILED"


class LiveGroundedAnswerSmokeConfigurationError(
    LiveGroundedAnswerSmokeError,
):
    """Raised when smoke-test configuration is invalid."""

    error_code = (
        "LIVE_GROUNDED_ANSWER_SMOKE_CONFIGURATION_FAILED"
    )


async def run_live_smoke() -> None:
    """Run retrieval and grounded generation using live services."""

    user_id = _required_uuid(
        "RETRIEVAL_SMOKE_USER_ID",
    )

    study_file_id = _optional_uuid(
        "RETRIEVAL_SMOKE_STUDY_FILE_ID",
    )

    subject_id = _optional_uuid(
        "RETRIEVAL_SMOKE_SUBJECT_ID",
    )

    question = _environment_text(
        "GROUNDED_ANSWER_SMOKE_QUESTION",
        default=DEFAULT_QUESTION,
    )

    match_count = _environment_integer(
        "RETRIEVAL_SMOKE_MATCH_COUNT",
        default=DEFAULT_MATCH_COUNT,
        minimum=1,
        maximum=20,
    )

    similarity_threshold = _environment_float(
        "RETRIEVAL_SMOKE_SIMILARITY_THRESHOLD",
        default=DEFAULT_SIMILARITY_THRESHOLD,
        minimum=0.0,
        maximum=1.0,
    )

    require_match = _environment_boolean(
        "GROUNDED_ANSWER_SMOKE_REQUIRE_MATCH",
        default=True,
    )

    settings = get_settings()

    query_embedding_dependency = (
        get_query_embedding_service(
            settings,
        )
    )

    query_embedding_service = await anext(
        query_embedding_dependency,
    )

    retrieval_service = (
        get_retrieval_orchestration_service(
            settings,
            query_embedding_service,
        )
    )

    grounded_answer_dependency = (
        get_grounded_answer_generation_service()
    )

    grounded_answer_service = await anext(
        grounded_answer_dependency,
    )

    try:
        retrieval_result = await retrieval_service.retrieve(
            RetrievalOrchestrationRequest(
                user_id=user_id,
                question=question,
                match_count=match_count,
                similarity_threshold=(
                    similarity_threshold
                ),
                study_file_id=study_file_id,
                subject_id=subject_id,
            )
        )

        chunks = _extract_retrieved_chunks(
            retrieval_result,
        )

        if require_match and not chunks:
            raise LiveGroundedAnswerSmokeError(
                "The live retrieval returned no context."
            )

        answer_result = await grounded_answer_service.generate(
            GroundedAnswerRequest(
                question=question,
                chunks=chunks,
            )
        )

        if (
            require_match
            and answer_result.outcome
            != GroundedAnswerOutcome.ANSWERED
        ):
            raise LiveGroundedAnswerSmokeError(
                "The live workflow did not generate "
                "a grounded answer."
            )

        citation_count = len(
            _CITATION_PATTERN.findall(
                answer_result.answer,
            )
        )

        if (
            answer_result.outcome
            == GroundedAnswerOutcome.ANSWERED
            and citation_count == 0
        ):
            raise LiveGroundedAnswerSmokeError(
                "The live answer did not contain citations."
            )

        print(
            "LIVE GROUNDED ANSWER SMOKE=PASS"
        )
        print(
            "Retrieved chunks: "
            f"{len(chunks)}"
        )
        print(
            "Answer outcome: "
            f"{answer_result.outcome}"
        )
        print(
            "Preserved sources: "
            f"{answer_result.source_count}"
        )
        print(
            "Citation markers: "
            f"{citation_count}"
        )
        print(
            "Provider metadata present: "
            f"{answer_result.provider is not None}"
        )
        print(
            "Model metadata present: "
            f"{answer_result.model is not None}"
        )
    finally:
        await grounded_answer_dependency.aclose()
        await query_embedding_dependency.aclose()


def main() -> int:
    """Run the smoke script with safe error reporting."""

    settings = get_settings()

    if not settings.ai_live_smoke_tests_enabled:
        print(
            "LIVE GROUNDED ANSWER SMOKE=SKIPPED"
        )
        print(
            "Reason: AI_LIVE_SMOKE_TESTS_ENABLED "
            "is false."
        )
        return 0

    try:
        asyncio.run(
            run_live_smoke()
        )
    except (
        GroundedAnswerError,
        LiveGroundedAnswerSmokeError,
    ) as exc:
        print(
            "LIVE GROUNDED ANSWER SMOKE=FAILED"
        )
        print(
            "Failure code: "
            f"{exc.error_code}"
        )
        return 1
    except Exception:  # noqa: BLE001
        print(
            "LIVE GROUNDED ANSWER SMOKE=FAILED"
        )
        print(
            "Failure code: "
            "LIVE_GROUNDED_ANSWER_SMOKE_UNEXPECTED_FAILED"
        )
        return 1

    return 0


def _extract_retrieved_chunks(
    result: object,
) -> tuple[RetrievedStudyChunk, ...]:
    """Read chunks from supported retrieval-result layouts."""

    possible_containers = [
        result,
        getattr(
            result,
            "retrieval_result",
            None,
        ),
        getattr(
            result,
            "retrieval",
            None,
        ),
        getattr(
            result,
            "result",
            None,
        ),
    ]

    for container in possible_containers:
        if container is None:
            continue

        for attribute_name in (
            "chunks",
            "matches",
        ):
            candidate = getattr(
                container,
                attribute_name,
                None,
            )

            if candidate is None:
                continue

            try:
                chunks = tuple(
                    candidate,
                )
            except TypeError as exc:
                raise LiveGroundedAnswerSmokeError(
                    "The retrieval result contains an "
                    "invalid chunk collection."
                ) from exc

            if not all(
                isinstance(
                    chunk,
                    RetrievedStudyChunk,
                )
                for chunk in chunks
            ):
                raise LiveGroundedAnswerSmokeError(
                    "The retrieval result contains an "
                    "invalid chunk item."
                )

            return chunks

    raise LiveGroundedAnswerSmokeError(
        "The retrieval result does not expose "
        "retrieved chunks."
    )


def _required_uuid(
    variable_name: str,
) -> UUID:
    value = os.getenv(
        variable_name,
        "",
    ).strip()

    if not value:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} is required."
        )

    try:
        return UUID(
            value,
        )
    except ValueError as exc:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must be a valid UUID."
        ) from exc


def _optional_uuid(
    variable_name: str,
) -> UUID | None:
    value = os.getenv(
        variable_name,
        "",
    ).strip()

    if not value:
        return None

    try:
        return UUID(
            value,
        )
    except ValueError as exc:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must be a valid UUID."
        ) from exc


def _environment_text(
    variable_name: str,
    *,
    default: str,
) -> str:
    value = os.getenv(
        variable_name,
        default,
    ).strip()

    if not value:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must not be empty."
        )

    return value


def _environment_integer(
    variable_name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        value = int(
            raw_value,
        )
    except ValueError as exc:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must be an integer."
        ) from exc

    if value < minimum or value > maximum:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def _environment_float(
    variable_name: str,
    *,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        value = float(
            raw_value,
        )
    except ValueError as exc:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must be numeric."
        ) from exc

    if value < minimum or value > maximum:
        raise LiveGroundedAnswerSmokeConfigurationError(
            f"{variable_name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def _environment_boolean(
    variable_name: str,
    *,
    default: bool,
) -> bool:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip().lower()

    if raw_value in {
        "true",
        "1",
        "yes",
        "on",
    }:
        return True

    if raw_value in {
        "false",
        "0",
        "no",
        "off",
    }:
        return False

    raise LiveGroundedAnswerSmokeConfigurationError(
        f"{variable_name} must be a boolean."
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )