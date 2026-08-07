# File: /backend/tests/test_live_retrieval_orchestration_smoke_script.py

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest

from app.ai.retrieval_contracts import (
    RetrievalRequestError,
    RetrievedStudyChunk,
)
from app.services.query_embedding import (
    QueryEmbeddingProviderError,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationRequest,
    RetrievalOrchestrationResult,
)
from scripts import (
    smoke_live_retrieval_orchestration as smoke,
)

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

FILE_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

SUBJECT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)

CHUNK_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)


def make_settings(
    *,
    enabled: bool,
) -> SimpleNamespace:
    """Return safe settings used by smoke-script tests."""

    return SimpleNamespace(
        ai_live_smoke_tests_enabled=enabled,
        gemini_api_key="configured-test-key",
        gemini_embedding_model="gemini-embedding-2",
        gemini_embedding_dimensions=768,
    )


def make_configuration(
    *,
    require_match: bool = False,
) -> smoke.LiveRetrievalSmokeConfiguration:
    """Return one valid smoke configuration."""

    return smoke.LiveRetrievalSmokeConfiguration(
        user_id=USER_ID,
        question="What is photosynthesis?",
        match_count=5,
        similarity_threshold=0.60,
        study_file_id=None,
        subject_id=None,
        require_match=require_match,
    )


def make_chunk() -> RetrievedStudyChunk:
    """Return one valid retrieved study chunk."""

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                CHUNK_ID,
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": 2,
            "content": (
                "Photosynthesis converts light energy "
                "into chemical energy."
            ),
            "start_offset": 100,
            "end_offset": 165,
            "chunk_metadata": {
                "page_number": 3,
            },
            "embedding_model": "gemini-embedding-2",
            "similarity_score": 0.92,
        }
    )


def make_result(
    *,
    configuration: (
        smoke.LiveRetrievalSmokeConfiguration
    ),
    chunks: tuple[RetrievedStudyChunk, ...],
) -> RetrievalOrchestrationResult:
    """Return a valid orchestration result."""

    return RetrievalOrchestrationResult(
        request=RetrievalOrchestrationRequest(
            user_id=configuration.user_id,
            question=configuration.question,
            match_count=configuration.match_count,
            similarity_threshold=(
                configuration.similarity_threshold
            ),
            study_file_id=configuration.study_file_id,
            subject_id=configuration.subject_id,
        ),
        chunks=chunks,
        embedding_provider="gemini",
        embedding_model="gemini-embedding-2",
        embedding_dimensions=768,
    )


def test_main_skips_when_live_smoke_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Disabled mode must not load smoke configuration."""

    monkeypatch.setattr(
        smoke,
        "get_settings",
        lambda: make_settings(
            enabled=False,
        ),
    )

    def fail_if_called() -> object:
        raise AssertionError(
            "Configuration should not be loaded."
        )

    monkeypatch.setattr(
        smoke,
        "_load_configuration",
        fail_if_called,
    )

    exit_code = smoke.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SMOKE=SKIPPED" in output


def test_configuration_requires_user_id() -> None:
    """A live smoke request must identify its owner."""

    with pytest.raises(
        smoke.LiveRetrievalSmokeConfigurationError,
    ):
        smoke._load_configuration(
            {}
        )


def test_configuration_parses_filters_and_options() -> None:
    """Smoke-only environment values should be validated."""

    configuration = smoke._load_configuration(
        {
            "RETRIEVAL_SMOKE_USER_ID": str(
                USER_ID,
            ),
            "RETRIEVAL_SMOKE_FILE_ID": str(
                FILE_ID,
            ),
            "RETRIEVAL_SMOKE_SUBJECT_ID": str(
                SUBJECT_ID,
            ),
            "RETRIEVAL_SMOKE_QUESTION": (
                "  What is photosynthesis?  "
            ),
            "RETRIEVAL_SMOKE_MATCH_COUNT": "4",
            (
                "RETRIEVAL_SMOKE_SIMILARITY_THRESHOLD"
            ): "0.75",
            "RETRIEVAL_SMOKE_REQUIRE_MATCH": "true",
        }
    )

    assert configuration.user_id == USER_ID
    assert configuration.study_file_id == FILE_ID
    assert configuration.subject_id == SUBJECT_ID
    assert configuration.question == "What is photosynthesis?"
    assert configuration.match_count == 4
    assert configuration.similarity_threshold == 0.75
    assert configuration.require_match is True


def test_main_prints_safe_success_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Success output must not expose questions or vectors."""

    configuration = make_configuration()

    monkeypatch.setattr(
        smoke,
        "get_settings",
        lambda: make_settings(
            enabled=True,
        ),
    )

    monkeypatch.setattr(
        smoke,
        "_load_configuration",
        lambda: configuration,
    )

    async def fake_execute(
        settings: object,
        received_configuration: object,
    ) -> RetrievalOrchestrationResult:
        del settings

        assert received_configuration is configuration

        return make_result(
            configuration=configuration,
            chunks=(
                make_chunk(),
            ),
        )

    monkeypatch.setattr(
        smoke,
        "_execute_live_smoke",
        fake_execute,
    )

    exit_code = smoke.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SMOKE=PASS" in output
    assert "Retrieved chunks: 1" in output
    assert "Embedding dimensions: 768" in output
    assert configuration.question not in output
    assert "[0.0" not in output


def test_main_accepts_normal_no_context_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No context is valid when a match is not required."""

    configuration = make_configuration()

    monkeypatch.setattr(
        smoke,
        "get_settings",
        lambda: make_settings(
            enabled=True,
        ),
    )

    monkeypatch.setattr(
        smoke,
        "_load_configuration",
        lambda: configuration,
    )

    async def fake_execute(
        settings: object,
        received_configuration: object,
    ) -> RetrievalOrchestrationResult:
        del settings
        del received_configuration

        return make_result(
            configuration=configuration,
            chunks=(),
        )

    monkeypatch.setattr(
        smoke,
        "_execute_live_smoke",
        fake_execute,
    )

    exit_code = smoke.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SMOKE=PASS" in output
    assert "Retrieved chunks: 0" in output


def test_validation_rejects_no_context_when_match_required() -> None:
    """Require-match mode should reject an empty result."""

    configuration = make_configuration(
        require_match=True,
    )

    result = make_result(
        configuration=configuration,
        chunks=(),
    )

    with pytest.raises(
        smoke.LiveRetrievalSmokeValidationError,
    ):
        smoke._validate_result(
            result,
            configuration=configuration,
            settings=make_settings(
                enabled=True,
            ),
        )


def test_main_handles_query_embedding_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A controlled Gemini failure should return exit code one."""

    configuration = make_configuration()

    monkeypatch.setattr(
        smoke,
        "get_settings",
        lambda: make_settings(
            enabled=True,
        ),
    )

    monkeypatch.setattr(
        smoke,
        "_load_configuration",
        lambda: configuration,
    )

    async def fail_execute(
        settings: object,
        received_configuration: object,
    ) -> RetrievalOrchestrationResult:
        del settings
        del received_configuration

        raise QueryEmbeddingProviderError(
            "Controlled query-embedding failure."
        )

    monkeypatch.setattr(
        smoke,
        "_execute_live_smoke",
        fail_execute,
    )

    exit_code = smoke.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "SMOKE=FAIL" in output
    assert "QueryEmbeddingProviderError" in output


def test_main_handles_retrieval_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A controlled Supabase failure should return exit code one."""

    configuration = make_configuration()

    monkeypatch.setattr(
        smoke,
        "get_settings",
        lambda: make_settings(
            enabled=True,
        ),
    )

    monkeypatch.setattr(
        smoke,
        "_load_configuration",
        lambda: configuration,
    )

    async def fail_execute(
        settings: object,
        received_configuration: object,
    ) -> RetrievalOrchestrationResult:
        del settings
        del received_configuration

        raise RetrievalRequestError(
            "Controlled retrieval failure."
        )

    monkeypatch.setattr(
        smoke,
        "_execute_live_smoke",
        fail_execute,
    )

    exit_code = smoke.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "SMOKE=FAIL" in output
    assert "RetrievalRequestError" in output