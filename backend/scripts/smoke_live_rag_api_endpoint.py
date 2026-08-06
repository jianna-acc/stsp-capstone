# File: /backend/scripts/smoke_live_rag_api_endpoint.py

from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

DEFAULT_SMOKE_QUESTION = (
    "What is one important concept explained in my "
    "uploaded study materials?"
)

DEFAULT_MATCH_COUNT = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.60

SMOKE_FAILURE_CODE = "LIVE_RAG_API_SMOKE_FAILED"


class LiveRagApiSmokeConfigurationError(
    ValueError,
):
    """Raised when live-smoke settings are invalid."""


@dataclass(frozen=True, slots=True)
class LiveRagApiSmokeConfig:
    """Process-only settings for one live API smoke request."""

    access_token: str
    question: str
    study_file_id: UUID | None
    subject_id: UUID | None
    match_count: int
    similarity_threshold: float
    require_context: bool


def main() -> int:
    """Run one guarded protected RAG API request."""

    settings = get_settings()

    if not settings.ai_live_smoke_tests_enabled:
        print("LIVE RAG API SMOKE=SKIPPED")
        print(
            "Reason: AI_LIVE_SMOKE_TESTS_ENABLED "
            "is false."
        )
        return 0

    try:
        config = _load_smoke_config()

        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as client:
            response = client.post(
                "/api/rag/answer",
                headers={
                    "Authorization": (
                        f"Bearer {config.access_token}"
                    ),
                },
                json=_build_request_payload(
                    config,
                ),
            )

        return _report_response(
            status_code=response.status_code,
            response_body=_read_response_body(
                response,
            ),
            require_context=config.require_context,
        )
    except LiveRagApiSmokeConfigurationError:
        print("LIVE RAG API SMOKE=FAILED")
        print(
            "Failure code: "
            "LIVE_RAG_API_SMOKE_CONFIGURATION_FAILED"
        )
        return 1
    except Exception:  # noqa: BLE001
        print("LIVE RAG API SMOKE=FAILED")
        print(
            f"Failure code: {SMOKE_FAILURE_CODE}"
        )
        return 1


def _load_smoke_config() -> LiveRagApiSmokeConfig:
    access_token = os.getenv(
        "RAG_API_SMOKE_ACCESS_TOKEN",
        "",
    ).strip()

    if not access_token:
        raise LiveRagApiSmokeConfigurationError(
            "A process-only bearer token is required."
        )

    question = os.getenv(
        "RAG_API_SMOKE_QUESTION",
        DEFAULT_SMOKE_QUESTION,
    ).strip()

    if not question:
        raise LiveRagApiSmokeConfigurationError(
            "The smoke question cannot be empty."
        )

    return LiveRagApiSmokeConfig(
        access_token=access_token,
        question=question,
        study_file_id=_read_optional_uuid(
            "RAG_API_SMOKE_STUDY_FILE_ID",
        ),
        subject_id=_read_optional_uuid(
            "RAG_API_SMOKE_SUBJECT_ID",
        ),
        match_count=_read_int(
            "RAG_API_SMOKE_MATCH_COUNT",
            default=DEFAULT_MATCH_COUNT,
            minimum=1,
            maximum=20,
        ),
        similarity_threshold=_read_float(
            "RAG_API_SMOKE_SIMILARITY_THRESHOLD",
            default=DEFAULT_SIMILARITY_THRESHOLD,
            minimum=0.0,
            maximum=1.0,
        ),
        require_context=_read_bool(
            "RAG_API_SMOKE_REQUIRE_CONTEXT",
            default=False,
        ),
    )


def _build_request_payload(
    config: LiveRagApiSmokeConfig,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "question": config.question,
        "match_count": config.match_count,
        "similarity_threshold": (
            config.similarity_threshold
        ),
    }

    if config.study_file_id is not None:
        payload["study_file_id"] = str(
            config.study_file_id,
        )

    if config.subject_id is not None:
        payload["subject_id"] = str(
            config.subject_id,
        )

    return payload


def _read_response_body(
    response: object,
) -> object:
    json_method = getattr(
        response,
        "json",
        None,
    )

    if not callable(
        json_method,
    ):
        return None

    try:
        return json_method()
    except Exception:  # noqa: BLE001
        return None


def _report_response(
    *,
    status_code: int,
    response_body: object,
    require_context: bool,
) -> int:
    if status_code != 200:
        print("LIVE RAG API SMOKE=FAILED")
        print(
            f"HTTP status: {status_code}"
        )

        error_code = _safe_error_code(
            response_body,
        )

        if error_code is not None:
            print(
                f"Failure code: {error_code}"
            )
        else:
            print(
                f"Failure code: {SMOKE_FAILURE_CODE}"
            )

        return 1

    if not isinstance(
        response_body,
        dict,
    ):
        return _report_invalid_response()

    outcome = response_body.get(
        "outcome",
    )

    context_available = response_body.get(
        "context_available",
    )

    retrieved_count = response_body.get(
        "retrieved_count",
    )

    source_count = response_body.get(
        "source_count",
    )

    answer = response_body.get(
        "answer",
    )

    sources = response_body.get(
        "sources",
    )

    if outcome not in {
        "answered",
        "no_context",
    }:
        return _report_invalid_response()

    if not isinstance(
        context_available,
        bool,
    ):
        return _report_invalid_response()

    if (
        isinstance(retrieved_count, bool)
        or not isinstance(retrieved_count, int)
        or retrieved_count < 0
    ):
        return _report_invalid_response()

    if (
        isinstance(source_count, bool)
        or not isinstance(source_count, int)
        or source_count < 0
    ):
        return _report_invalid_response()

    if (
        not isinstance(answer, str)
        or not answer.strip()
    ):
        return _report_invalid_response()

    if not isinstance(
        sources,
        list,
    ):
        return _report_invalid_response()

    if source_count != len(
        sources,
    ):
        return _report_invalid_response()

    if require_context and not context_available:
        print("LIVE RAG API SMOKE=FAILED")
        print(
            "Failure code: "
            "LIVE_RAG_API_SMOKE_CONTEXT_REQUIRED"
        )
        return 1

    print("LIVE RAG API SMOKE=PASS")
    print(
        f"HTTP status: {status_code}"
    )
    print(
        f"Outcome: {outcome}"
    )
    print(
        "Context available: "
        f"{context_available}"
    )
    print(
        f"Retrieved count: {retrieved_count}"
    )
    print(
        f"Source count: {source_count}"
    )
    print("Answer present: True")

    return 0


def _report_invalid_response() -> int:
    print("LIVE RAG API SMOKE=FAILED")
    print(
        "Failure code: "
        "LIVE_RAG_API_SMOKE_INVALID_RESPONSE"
    )
    return 1


def _safe_error_code(
    response_body: object,
) -> str | None:
    if not isinstance(
        response_body,
        dict,
    ):
        return None

    error_code = response_body.get(
        "error_code",
    )

    if (
        not isinstance(error_code, str)
        or not error_code
        or len(error_code) > 128
    ):
        return None

    if not all(
        character.isupper()
        or character.isdigit()
        or character == "_"
        for character in error_code
    ):
        return None

    return error_code


def _read_optional_uuid(
    variable_name: str,
) -> UUID | None:
    raw_value = os.getenv(
        variable_name,
        "",
    ).strip()

    if not raw_value:
        return None

    try:
        return UUID(
            raw_value,
        )
    except ValueError as exc:
        raise LiveRagApiSmokeConfigurationError(
            f"{variable_name} must be a UUID."
        ) from exc


def _read_int(
    variable_name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw_value = os.getenv(
        variable_name,
        str(
            default,
        ),
    ).strip()

    try:
        value = int(
            raw_value,
        )
    except ValueError as exc:
        raise LiveRagApiSmokeConfigurationError(
            f"{variable_name} must be an integer."
        ) from exc

    if value < minimum or value > maximum:
        raise LiveRagApiSmokeConfigurationError(
            f"{variable_name} is outside its allowed range."
        )

    return value


def _read_float(
    variable_name: str,
    *,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    raw_value = os.getenv(
        variable_name,
        str(
            default,
        ),
    ).strip()

    try:
        value = float(
            raw_value,
        )
    except ValueError as exc:
        raise LiveRagApiSmokeConfigurationError(
            f"{variable_name} must be numeric."
        ) from exc

    if value < minimum or value > maximum:
        raise LiveRagApiSmokeConfigurationError(
            f"{variable_name} is outside its allowed range."
        )

    return value


def _read_bool(
    variable_name: str,
    *,
    default: bool,
) -> bool:
    raw_value = os.getenv(
        variable_name,
        str(
            default,
        ),
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

    raise LiveRagApiSmokeConfigurationError(
        f"{variable_name} must be a boolean."
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )