# File: /backend/tests/test_live_grounded_answer_smoke_script.py

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.ai.grounded_answer_contracts import (
    GroundedAnswerResult,
)
from app.ai.retrieval_contracts import (
    RetrievedStudyChunk,
)
from scripts import (
    smoke_live_grounded_answer_generation as smoke_script,
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


def make_chunk() -> RetrievedStudyChunk:
    """Create one valid retrieved chunk."""

    content = (
        "Photosynthesis converts light energy "
        "into chemical energy."
    )

    return RetrievedStudyChunk.from_rpc_row(
        {
            "chunk_id": str(
                uuid4(),
            ),
            "study_file_id": str(
                FILE_ID,
            ),
            "subject_id": str(
                SUBJECT_ID,
            ),
            "source_name": "Biology Notes.pdf",
            "chunk_index": 1,
            "content": content,
            "start_offset": 100,
            "end_offset": (
                100 + len(content)
            ),
            "chunk_metadata": {
                "page_number": 2,
            },
            "embedding_model": "gemini-embedding-2",
            "similarity_score": 0.95,
        }
    )


class FakeRetrievalService:
    """Return controlled retrieval context."""

    def __init__(
        self,
        *,
        chunks: tuple[
            RetrievedStudyChunk,
            ...,
        ],
    ) -> None:
        self.chunks = chunks
        self.requests: list[object] = []
        self.closed = False

    async def retrieve(
        self,
        request: object,
    ) -> object:
        """Return a simple supported result layout."""

        self.requests.append(
            request,
        )

        return SimpleNamespace(
            outcome=(
                "matches"
                if self.chunks
                else "no_context"
            ),
            chunks=self.chunks,
        )

    async def aclose(
        self,
    ) -> None:
        """Record retrieval-service cleanup."""

        self.closed = True


class FakeGroundedAnswerService:
    """Return a deterministic grounded answer."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    async def generate(
        self,
        request: object,
    ) -> GroundedAnswerResult:
        """Generate a controlled cited answer."""

        self.requests.append(
            request,
        )

        return GroundedAnswerResult.generated(
            request=request,
            answer=(
                "Photosynthesis converts light energy "
                "into chemical energy. [Source 1]"
            ),
            provider="gemini",
            model="fake-generation-model",
        )


def install_smoke_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Install valid process-only smoke variables."""

    monkeypatch.setenv(
        "RETRIEVAL_SMOKE_USER_ID",
        str(USER_ID),
    )

    monkeypatch.setenv(
        "RETRIEVAL_SMOKE_STUDY_FILE_ID",
        str(FILE_ID),
    )

    monkeypatch.setenv(
        "RETRIEVAL_SMOKE_SUBJECT_ID",
        str(SUBJECT_ID),
    )

    monkeypatch.setenv(
        "GROUNDED_ANSWER_SMOKE_QUESTION",
        "What is photosynthesis?",
    )

    monkeypatch.setenv(
        "RETRIEVAL_SMOKE_MATCH_COUNT",
        "5",
    )

    monkeypatch.setenv(
        "RETRIEVAL_SMOKE_SIMILARITY_THRESHOLD",
        "0.0",
    )

    monkeypatch.setenv(
        "GROUNDED_ANSWER_SMOKE_REQUIRE_MATCH",
        "true",
    )


def install_fake_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    retrieval_service: FakeRetrievalService,
    grounded_service: FakeGroundedAnswerService,
) -> None:
    """Replace live dependencies with offline fakes."""

    fake_query_embedding_service = object()

    async def query_embedding_dependency(
        _settings: object,
    ):
        yield fake_query_embedding_service

    def retrieval_dependency(
        _settings: object,
        query_embedding_service: object,
    ) -> FakeRetrievalService:
        assert (
            query_embedding_service
            is fake_query_embedding_service
        )

        return retrieval_service

    async def grounded_dependency():
        yield grounded_service

    monkeypatch.setattr(
        smoke_script,
        "get_query_embedding_service",
        query_embedding_dependency,
    )

    monkeypatch.setattr(
        smoke_script,
        "get_retrieval_orchestration_service",
        retrieval_dependency,
    )

    monkeypatch.setattr(
        smoke_script,
        "get_grounded_answer_generation_service",
        grounded_dependency,
    )


def test_disabled_script_skips_without_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dependency_called = False

    def forbidden_dependency() -> object:
        nonlocal dependency_called
        dependency_called = True
        raise AssertionError(
            "Disabled smoke must not create services."
        )

    monkeypatch.setattr(
        smoke_script,
        "get_settings",
        lambda: SimpleNamespace(
            ai_live_smoke_tests_enabled=False,
        ),
    )

    monkeypatch.setattr(
        smoke_script,
        "get_retrieval_orchestration_service",
        forbidden_dependency,
    )

    exit_code = smoke_script.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert dependency_called is False
    assert "SMOKE=SKIPPED" in output
    assert "is false" in output


def test_enabled_script_runs_safe_fake_workflow(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    chunk = make_chunk()

    retrieval_service = FakeRetrievalService(
        chunks=(
            chunk,
        ),
    )

    grounded_service = FakeGroundedAnswerService()

    monkeypatch.setattr(
        smoke_script,
        "get_settings",
        lambda: SimpleNamespace(
            ai_live_smoke_tests_enabled=True,
        ),
    )

    install_smoke_environment(
        monkeypatch,
    )

    install_fake_dependencies(
        monkeypatch,
        retrieval_service=retrieval_service,
        grounded_service=grounded_service,
    )

    exit_code = smoke_script.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SMOKE=PASS" in output
    assert "Retrieved chunks: 1" in output
    assert "Preserved sources: 1" in output
    assert "Citation markers: 1" in output

    assert len(
        retrieval_service.requests,
    ) == 1

    assert len(
        grounded_service.requests,
    ) == 1

    assert str(USER_ID) not in output
    assert str(FILE_ID) not in output
    assert str(SUBJECT_ID) not in output
    assert str(chunk.chunk_id) not in output
    assert chunk.content not in output
    assert chunk.source_name not in output
    assert "What is photosynthesis?" not in output


def test_enabled_script_fails_safely_without_match(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    retrieval_service = FakeRetrievalService(
        chunks=(),
    )

    grounded_service = FakeGroundedAnswerService()

    monkeypatch.setattr(
        smoke_script,
        "get_settings",
        lambda: SimpleNamespace(
            ai_live_smoke_tests_enabled=True,
        ),
    )

    install_smoke_environment(
        monkeypatch,
    )

    install_fake_dependencies(
        monkeypatch,
        retrieval_service=retrieval_service,
        grounded_service=grounded_service,
    )

    exit_code = smoke_script.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "SMOKE=FAILED" in output
    assert (
        "LIVE_GROUNDED_ANSWER_SMOKE_FAILED"
        in output
    )

    assert grounded_service.requests == []


def test_enabled_script_rejects_invalid_user_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        smoke_script,
        "get_settings",
        lambda: SimpleNamespace(
            ai_live_smoke_tests_enabled=True,
        ),
    )

    monkeypatch.setenv(
        "RETRIEVAL_SMOKE_USER_ID",
        "not-a-uuid",
    )

    exit_code = smoke_script.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "SMOKE=FAILED" in output
    assert (
        "LIVE_GROUNDED_ANSWER_SMOKE_"
        "CONFIGURATION_FAILED"
        in output
    )
    assert "not-a-uuid" not in output


def test_extracts_nested_retrieval_matches() -> None:
    chunk = make_chunk()

    result = SimpleNamespace(
        retrieval_result=SimpleNamespace(
            matches=(
                chunk,
            ),
        ),
    )

    assert (
        smoke_script._extract_retrieved_chunks(
            result,
        )
        == (
            chunk,
        )
    )