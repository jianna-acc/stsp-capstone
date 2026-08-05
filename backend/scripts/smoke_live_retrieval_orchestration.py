# File: /backend/scripts/smoke_live_retrieval_orchestration.py
# Purpose: Runs one guarded live query-embedding and retrieval workflow.

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from app.ai.retrieval_contracts import (
    RETRIEVAL_EMBEDDING_DIMENSIONS,
    RetrievalError,
)
from app.ai.retrieval_persistence import (
    SupabaseRetrievalPersistence,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.services.query_embedding import (
    QueryEmbeddingError,
    QueryEmbeddingService,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
    RetrievalOrchestrationResult,
    RetrievalOrchestrationService,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)

DEFAULT_SMOKE_QUESTION = (
    "Summarize the main concepts in my uploaded study material."
)

DEFAULT_SMOKE_MATCH_COUNT = 5
DEFAULT_SMOKE_SIMILARITY_THRESHOLD = 0.0


class LiveRetrievalSmokeConfigurationError(RuntimeError):
    """Raised when smoke-test environment values are invalid."""


class LiveRetrievalSmokeValidationError(RuntimeError):
    """Raised when the live result violates the smoke contract."""


@dataclass(frozen=True, slots=True)
class LiveRetrievalSmokeConfiguration:
    """Safe configuration for one live retrieval smoke request."""

    user_id: UUID
    question: str
    match_count: int
    similarity_threshold: float
    study_file_id: UUID | None
    subject_id: UUID | None
    require_match: bool


def _load_configuration(
    environment: Mapping[str, str] | None = None,
) -> LiveRetrievalSmokeConfiguration:
    """Load smoke-only values without changing application settings."""

    source = (
        os.environ
        if environment is None
        else environment
    )

    user_id = _required_environment_uuid(
        source,
        variable_name="RETRIEVAL_SMOKE_USER_ID",
    )

    study_file_id = _optional_environment_uuid(
        source,
        variable_name="RETRIEVAL_SMOKE_FILE_ID",
    )

    subject_id = _optional_environment_uuid(
        source,
        variable_name="RETRIEVAL_SMOKE_SUBJECT_ID",
    )

    question = source.get(
        "RETRIEVAL_SMOKE_QUESTION",
        DEFAULT_SMOKE_QUESTION,
    ).strip()

    if not question:
        raise LiveRetrievalSmokeConfigurationError(
            "RETRIEVAL_SMOKE_QUESTION must not be empty."
        )

    match_count = _environment_integer(
        source,
        variable_name="RETRIEVAL_SMOKE_MATCH_COUNT",
        default=DEFAULT_SMOKE_MATCH_COUNT,
    )

    similarity_threshold = _environment_float(
        source,
        variable_name=(
            "RETRIEVAL_SMOKE_SIMILARITY_THRESHOLD"
        ),
        default=DEFAULT_SMOKE_SIMILARITY_THRESHOLD,
    )

    require_match = _environment_boolean(
        source,
        variable_name="RETRIEVAL_SMOKE_REQUIRE_MATCH",
        default=False,
    )

    request = RetrievalOrchestrationRequest(
        user_id=user_id,
        question=question,
        match_count=match_count,
        similarity_threshold=similarity_threshold,
        study_file_id=study_file_id,
        subject_id=subject_id,
    )

    return LiveRetrievalSmokeConfiguration(
        user_id=request.user_id,
        question=request.question,
        match_count=request.match_count,
        similarity_threshold=request.similarity_threshold,
        study_file_id=request.study_file_id,
        subject_id=request.subject_id,
        require_match=require_match,
    )


async def _execute_live_smoke(
    settings: Settings,
    configuration: LiveRetrievalSmokeConfiguration,
) -> RetrievalOrchestrationResult:
    """Run one real Gemini and Supabase retrieval workflow."""

    query_embedding_service = QueryEmbeddingService(
        settings=settings,
    )

    admin_service = SupabaseAdminService(
        settings=settings,
    )

    retrieval_persistence = SupabaseRetrievalPersistence(
        client=admin_service,
    )

    orchestration_service = RetrievalOrchestrationService(
        query_embedding_service=query_embedding_service,
        retrieval_persistence=retrieval_persistence,
    )

    try:
        result = await orchestration_service.retrieve(
            RetrievalOrchestrationRequest(
                user_id=configuration.user_id,
                question=configuration.question,
                match_count=configuration.match_count,
                similarity_threshold=(
                    configuration.similarity_threshold
                ),
                study_file_id=configuration.study_file_id,
                subject_id=configuration.subject_id,
            )
        )
    finally:
        await orchestration_service.aclose()

    _validate_result(
        result,
        configuration=configuration,
        settings=settings,
    )

    return result


def _validate_result(
    result: RetrievalOrchestrationResult,
    *,
    configuration: LiveRetrievalSmokeConfiguration,
    settings: Settings,
) -> None:
    """Validate safe metadata returned by the live workflow."""

    if not isinstance(
        result,
        RetrievalOrchestrationResult,
    ):
        raise LiveRetrievalSmokeValidationError(
            "The smoke workflow returned an invalid result."
        )

    if result.request.user_id != configuration.user_id:
        raise LiveRetrievalSmokeValidationError(
            "The result user does not match the smoke user."
        )

    if result.request.question != configuration.question:
        raise LiveRetrievalSmokeValidationError(
            "The result question does not match the request."
        )

    if result.request.match_count != configuration.match_count:
        raise LiveRetrievalSmokeValidationError(
            "The result match count does not match the request."
        )

    if (
        result.request.similarity_threshold
        != configuration.similarity_threshold
    ):
        raise LiveRetrievalSmokeValidationError(
            "The result threshold does not match the request."
        )

    if (
        result.request.study_file_id
        != configuration.study_file_id
    ):
        raise LiveRetrievalSmokeValidationError(
            "The result study-file filter does not match."
        )

    if result.request.subject_id != configuration.subject_id:
        raise LiveRetrievalSmokeValidationError(
            "The result subject filter does not match."
        )

    if result.embedding_provider != "gemini":
        raise LiveRetrievalSmokeValidationError(
            "The live embedding provider must be Gemini."
        )

    if (
        result.embedding_model
        != settings.gemini_embedding_model
    ):
        raise LiveRetrievalSmokeValidationError(
            "The returned embedding model does not match "
            "the configured model."
        )

    if (
        result.embedding_dimensions
        != RETRIEVAL_EMBEDDING_DIMENSIONS
    ):
        raise LiveRetrievalSmokeValidationError(
            "The result must use exactly "
            f"{RETRIEVAL_EMBEDDING_DIMENSIONS} dimensions."
        )

    if (
        result.embedding_dimensions
        != settings.gemini_embedding_dimensions
    ):
        raise LiveRetrievalSmokeValidationError(
            "The result dimensions do not match configuration."
        )

    if result.retrieved_count > configuration.match_count:
        raise LiveRetrievalSmokeValidationError(
            "The retrieval result exceeded match_count."
        )

    if (
        configuration.require_match
        and not result.context_available
    ):
        raise LiveRetrievalSmokeValidationError(
            "The smoke test required at least one matching chunk."
        )

    for chunk in result.chunks:
        if (
            chunk.similarity_score
            < configuration.similarity_threshold
        ):
            raise LiveRetrievalSmokeValidationError(
                "A returned chunk is below the requested threshold."
            )

        if (
            configuration.study_file_id is not None
            and chunk.study_file_id
            != configuration.study_file_id
        ):
            raise LiveRetrievalSmokeValidationError(
                "A returned chunk violates the study-file filter."
            )

        if (
            configuration.subject_id is not None
            and chunk.subject_id
            != configuration.subject_id
        ):
            raise LiveRetrievalSmokeValidationError(
                "A returned chunk violates the subject filter."
            )


def _print_success(
    result: RetrievalOrchestrationResult,
    configuration: LiveRetrievalSmokeConfiguration,
) -> None:
    """Print only non-sensitive smoke-test metadata."""

    print("LIVE RETRIEVAL ORCHESTRATION SMOKE=PASS")
    print(f"Outcome: {result.outcome}")
    print(f"Retrieved chunks: {result.retrieved_count}")
    print(f"Embedding provider: {result.embedding_provider}")
    print(f"Embedding model: {result.embedding_model}")
    print(
        "Embedding dimensions: "
        f"{result.embedding_dimensions}"
    )
    print(
        "Similarity threshold: "
        f"{configuration.similarity_threshold}"
    )
    print(
        "Study-file filter active: "
        f"{configuration.study_file_id is not None}"
    )
    print(
        "Subject filter active: "
        f"{configuration.subject_id is not None}"
    )
    print(
        "Require at least one match: "
        f"{configuration.require_match}"
    )
    print(
        "Question characters: "
        f"{len(configuration.question)}"
    )

    if result.chunks:
        highest_similarity = max(
            chunk.similarity_score
            for chunk in result.chunks
        )

        print(
            "Highest similarity: "
            f"{highest_similarity:.6f}"
        )


def _required_environment_uuid(
    environment: Mapping[str, str],
    *,
    variable_name: str,
) -> UUID:
    raw_value = environment.get(
        variable_name,
        "",
    ).strip()

    if not raw_value:
        raise LiveRetrievalSmokeConfigurationError(
            f"{variable_name} is required."
        )

    return _parse_uuid(
        raw_value,
        variable_name=variable_name,
    )


def _optional_environment_uuid(
    environment: Mapping[str, str],
    *,
    variable_name: str,
) -> UUID | None:
    raw_value = environment.get(
        variable_name,
        "",
    ).strip()

    if not raw_value:
        return None

    return _parse_uuid(
        raw_value,
        variable_name=variable_name,
    )


def _parse_uuid(
    raw_value: str,
    *,
    variable_name: str,
) -> UUID:
    try:
        return UUID(
            raw_value,
        )
    except ValueError as exc:
        raise LiveRetrievalSmokeConfigurationError(
            f"{variable_name} must contain a valid UUID."
        ) from exc


def _environment_integer(
    environment: Mapping[str, str],
    *,
    variable_name: str,
    default: int,
) -> int:
    raw_value = environment.get(
        variable_name,
        str(default),
    ).strip()

    try:
        return int(
            raw_value,
        )
    except ValueError as exc:
        raise LiveRetrievalSmokeConfigurationError(
            f"{variable_name} must contain an integer."
        ) from exc


def _environment_float(
    environment: Mapping[str, str],
    *,
    variable_name: str,
    default: float,
) -> float:
    raw_value = environment.get(
        variable_name,
        str(default),
    ).strip()

    try:
        return float(
            raw_value,
        )
    except ValueError as exc:
        raise LiveRetrievalSmokeConfigurationError(
            f"{variable_name} must contain a number."
        ) from exc


def _environment_boolean(
    environment: Mapping[str, str],
    *,
    variable_name: str,
    default: bool,
) -> bool:
    raw_value = environment.get(
        variable_name,
        str(default),
    ).strip().lower()

    true_values = {
        "1",
        "true",
        "yes",
        "on",
    }

    false_values = {
        "0",
        "false",
        "no",
        "off",
    }

    if raw_value in true_values:
        return True

    if raw_value in false_values:
        return False

    raise LiveRetrievalSmokeConfigurationError(
        f"{variable_name} must contain true or false."
    )


def main() -> int:
    """Run the guarded live retrieval smoke test."""

    settings = get_settings()

    if not settings.ai_live_smoke_tests_enabled:
        print("LIVE RETRIEVAL ORCHESTRATION SMOKE=SKIPPED")
        print(
            "Reason: AI_LIVE_SMOKE_TESTS_ENABLED is false."
        )
        return 0

    if not settings.gemini_api_key:
        print("LIVE RETRIEVAL ORCHESTRATION SMOKE=FAIL")
        print("Reason: Gemini API key is not configured.")
        return 1

    try:
        configuration = _load_configuration()
    except LiveRetrievalSmokeConfigurationError as exc:
        print("LIVE RETRIEVAL ORCHESTRATION SMOKE=FAIL")
        print(f"Error type: {type(exc).__name__}")
        print(f"Reason: {exc}")
        return 1

    try:
        result = asyncio.run(
            _execute_live_smoke(
                settings,
                configuration,
            )
        )
    except (
        LiveRetrievalSmokeValidationError,
        QueryEmbeddingError,
        RetrievalError,
    ) as exc:
        print("LIVE RETRIEVAL ORCHESTRATION SMOKE=FAIL")
        print(f"Error type: {type(exc).__name__}")
        print(f"Reason: {exc}")
        return 1

    _print_success(
        result,
        configuration,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )