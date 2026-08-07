# File: /backend/tests/test_live_query_embedding_smoke_script.py
# Purpose: Tests the guarded live query-embedding smoke script
# without calling Gemini or exposing credentials and vectors.

from __future__ import annotations

import importlib.util
from math import inf
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest

from app.ai.contracts import EmbeddingTaskType
from app.core.config import Settings
from app.services.query_embedding import (
    QueryEmbeddingProviderError,
    QueryEmbeddingResult,
)

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "smoke_live_query_embedding.py"
)

EMBEDDING_DIMENSIONS = 768
EMBEDDING_MODEL = "gemini-embedding-2"


def load_smoke_module() -> ModuleType:
    """Load the smoke script as an importable test module."""

    specification = importlib.util.spec_from_file_location(
        "smoke_live_query_embedding",
        SCRIPT_PATH,
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(
        specification,
    )

    specification.loader.exec_module(
        module,
    )

    return module


def make_settings(
    *,
    enabled: bool,
    api_key: str = "test-live-gemini-key",
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> Settings:
    """Create smoke-test settings without reading .env."""

    return cast(
        Settings,
        SimpleNamespace(
            ai_live_smoke_tests_enabled=enabled,
            gemini_api_key=api_key,
            gemini_embedding_model=EMBEDDING_MODEL,
            gemini_embedding_dimensions=dimensions,
        ),
    )


def make_vector(
    value: float = 0.125,
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> tuple[float, ...]:
    """Create one deterministic vector."""

    return tuple(
        value
        for _ in range(
            dimensions,
        )
    )


def make_result(
    module: ModuleType,
    *,
    embedding: tuple[float, ...] | None = None,
    declared_dimensions: int = EMBEDDING_DIMENSIONS,
) -> QueryEmbeddingResult:
    """Create one query-embedding result for smoke validation."""

    return QueryEmbeddingResult(
        question=module.SMOKE_QUESTION,
        embedding=(embedding if embedding is not None else make_vector()),
        provider="gemini",
        embedding_model=EMBEDDING_MODEL,
        embedding_dimensions=declared_dimensions,
        task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
    )


def test_script_has_correct_file_path_comment() -> None:
    """The script should begin with its repository filepath."""

    first_line = SCRIPT_PATH.read_text(
        encoding="utf-8",
    ).splitlines()[0]

    assert first_line == ("# File: /backend/scripts/smoke_live_query_embedding.py")


def test_disabled_smoke_skips_without_creating_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The disabled default must never construct a live service."""

    module = load_smoke_module()

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: make_settings(
            enabled=False,
        ),
    )

    class ForbiddenService:
        """Fail if the disabled path constructs a service."""

        def __init__(
            self,
            settings: Settings,
        ) -> None:
            raise AssertionError(
                "Disabled smoke test created a service.",
            )

    monkeypatch.setattr(
        module,
        "QueryEmbeddingService",
        ForbiddenService,
    )

    exit_code = module.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "LIVE QUERY EMBEDDING SMOKE=SKIPPED" in output
    assert "AI_LIVE_SMOKE_TESTS_ENABLED" in output


def test_successful_smoke_validates_and_closes_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A valid live result should pass and always close."""

    module = load_smoke_module()
    created_services: list[Any] = []

    class SuccessfulService:
        """Return one valid vector and record cleanup."""

        def __init__(
            self,
            settings: Settings,
        ) -> None:
            self.settings = settings
            self.closed = False

            created_services.append(
                self,
            )

        async def embed_query(
            self,
            question: str,
        ) -> QueryEmbeddingResult:
            assert question == module.SMOKE_QUESTION

            return make_result(
                module,
            )

        async def aclose(
            self,
        ) -> None:
            self.closed = True

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: make_settings(
            enabled=True,
        ),
    )

    monkeypatch.setattr(
        module,
        "QueryEmbeddingService",
        SuccessfulService,
    )

    exit_code = module.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "LIVE QUERY EMBEDDING SMOKE=PASS" in output
    assert "Task type: retrieval_query" in output
    assert "Embedding dimensions: 768" in output

    assert (
        len(
            created_services,
        )
        == 1
    )

    assert created_services[0].closed is True


def test_failed_live_call_returns_failure_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live failures should return one and still close resources."""

    module = load_smoke_module()
    created_services: list[Any] = []

    class FailingService:
        """Raise during embedding and record cleanup."""

        def __init__(
            self,
            settings: Settings,
        ) -> None:
            self.closed = False

            created_services.append(
                self,
            )

        async def embed_query(
            self,
            question: str,
        ) -> QueryEmbeddingResult:
            raise QueryEmbeddingProviderError(
                "Controlled live failure.",
            )

        async def aclose(
            self,
        ) -> None:
            self.closed = True

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: make_settings(
            enabled=True,
        ),
    )

    monkeypatch.setattr(
        module,
        "QueryEmbeddingService",
        FailingService,
    )

    exit_code = module.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "LIVE QUERY EMBEDDING SMOKE=FAIL" in output
    assert "Error type: QueryEmbeddingProviderError" in output

    assert (
        len(
            created_services,
        )
        == 1
    )

    assert created_services[0].closed is True


def test_validation_rejects_wrong_dimensions() -> None:
    """The smoke contract requires exactly 768 dimensions."""

    module = load_smoke_module()

    with pytest.raises(
        module.LiveQueryEmbeddingSmokeValidationError,
        match="768 dimensions",
    ):
        module._validate_result(
            result=make_result(
                module,
                embedding=make_vector(
                    dimensions=767,
                ),
                declared_dimensions=767,
            ),
            settings=make_settings(
                enabled=True,
            ),
        )


def test_validation_rejects_non_finite_vector() -> None:
    """Infinite values must fail the smoke contract."""

    module = load_smoke_module()

    invalid_vector = (
        inf,
        *make_vector(
            dimensions=767,
        ),
    )

    with pytest.raises(
        module.LiveQueryEmbeddingSmokeValidationError,
        match="finite",
    ):
        module._validate_result(
            result=make_result(
                module,
                embedding=invalid_vector,
            ),
            settings=make_settings(
                enabled=True,
            ),
        )


def test_validation_rejects_zero_vector() -> None:
    """A zero vector is invalid for cosine similarity."""

    module = load_smoke_module()

    with pytest.raises(
        module.LiveQueryEmbeddingSmokeValidationError,
        match="zero vector",
    ):
        module._validate_result(
            result=make_result(
                module,
                embedding=make_vector(
                    value=0.0,
                ),
            ),
            settings=make_settings(
                enabled=True,
            ),
        )


def test_success_output_omits_sensitive_values(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Output must not include keys, questions, or raw vectors."""

    module = load_smoke_module()

    secret_key = "secret-key-that-must-not-print"

    class SafeOutputService:
        """Return one valid result."""

        def __init__(
            self,
            settings: Settings,
        ) -> None:
            self.settings = settings

        async def embed_query(
            self,
            question: str,
        ) -> QueryEmbeddingResult:
            return make_result(
                module,
            )

        async def aclose(
            self,
        ) -> None:
            return None

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: make_settings(
            enabled=True,
            api_key=secret_key,
        ),
    )

    monkeypatch.setattr(
        module,
        "QueryEmbeddingService",
        SafeOutputService,
    )

    assert module.main() == 0

    output = capsys.readouterr().out

    assert secret_key not in output
    assert module.SMOKE_QUESTION not in output
    assert "0.125" not in output
    assert "Vector finite: True" in output
    assert "Vector nonzero: True" in output
