# File: /backend/tests/test_live_rag_api_smoke_script.py

from __future__ import annotations

from types import SimpleNamespace
from typing import Self

import pytest

from scripts import (
    smoke_live_rag_api_endpoint as smoke_module,
)

ACCESS_TOKEN = "private-live-access-token"

QUESTION = "Private smoke-test question."


class FakeResponse:
    """Controlled HTTP response returned by the fake client."""

    def __init__(
        self,
        *,
        status_code: int,
        body: object,
    ) -> None:
        self.status_code = status_code
        self.body = body

    def json(
        self,
    ) -> object:
        """Return the controlled JSON body."""

        return self.body


def install_fake_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    response: FakeResponse,
) -> dict[str, object]:
    """Install a fake TestClient and capture its request."""

    captured: dict[str, object] = {}

    class FakeTestClient:
        def __init__(
            self,
            application: object,
            *,
            raise_server_exceptions: bool,
        ) -> None:
            captured["application"] = application
            captured["raise_server_exceptions"] = (
                raise_server_exceptions
            )

        def __enter__(
            self,
        ) -> Self:
            return self

        def __exit__(
            self,
            _exception_type: object,
            _exception: object,
            _traceback: object,
        ) -> None:
            return None

        def post(
            self,
            path: str,
            *,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> FakeResponse:
            captured["path"] = path
            captured["headers"] = headers
            captured["json"] = json

            return response

    monkeypatch.setattr(
        smoke_module,
        "TestClient",
        FakeTestClient,
    )

    return captured


def enable_live_smoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Enable the guarded script without reading real settings."""

    monkeypatch.setattr(
        smoke_module,
        "get_settings",
        lambda: SimpleNamespace(
            ai_live_smoke_tests_enabled=True,
        ),
    )


def set_required_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Set process-only fake smoke values."""

    monkeypatch.setenv(
        "RAG_API_SMOKE_ACCESS_TOKEN",
        ACCESS_TOKEN,
    )

    monkeypatch.setenv(
        "RAG_API_SMOKE_QUESTION",
        QUESTION,
    )


def test_script_skips_when_live_testing_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        smoke_module,
        "get_settings",
        lambda: SimpleNamespace(
            ai_live_smoke_tests_enabled=False,
        ),
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "LIVE RAG API SMOKE=SKIPPED" in output


def test_script_runs_answered_request_safely(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    enable_live_smoke(
        monkeypatch,
    )

    set_required_environment(
        monkeypatch,
    )

    captured = install_fake_client(
        monkeypatch,
        response=FakeResponse(
            status_code=200,
            body={
                "outcome": "answered",
                "answer": (
                    "Private generated answer. [Source 1]"
                ),
                "sources": [
                    {
                        "source_number": 1,
                        "source_name": "Private File.pdf",
                        "chunk_index": 0,
                        "similarity_score": 0.93,
                    }
                ],
                "retrieved_count": 1,
                "source_count": 1,
                "context_available": True,
            },
        ),
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "LIVE RAG API SMOKE=PASS" in output
    assert "Outcome: answered" in output
    assert "Answer present: True" in output

    assert captured["path"] == "/api/rag/answer"

    assert captured[
        "raise_server_exceptions"
    ] is False

    assert captured["headers"] == {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    assert captured["json"] == {
        "question": QUESTION,
        "match_count": 5,
        "similarity_threshold": 0.60,
    }

    assert ACCESS_TOKEN not in output
    assert QUESTION not in output
    assert "Private generated answer" not in output
    assert "Private File.pdf" not in output


def test_script_accepts_no_context_when_not_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    enable_live_smoke(
        monkeypatch,
    )

    set_required_environment(
        monkeypatch,
    )

    install_fake_client(
        monkeypatch,
        response=FakeResponse(
            status_code=200,
            body={
                "outcome": "no_context",
                "answer": "Approved no-context answer.",
                "sources": [],
                "retrieved_count": 0,
                "source_count": 0,
                "context_available": False,
            },
        ),
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "LIVE RAG API SMOKE=PASS" in output
    assert "Outcome: no_context" in output


def test_script_fails_when_context_is_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    enable_live_smoke(
        monkeypatch,
    )

    set_required_environment(
        monkeypatch,
    )

    monkeypatch.setenv(
        "RAG_API_SMOKE_REQUIRE_CONTEXT",
        "true",
    )

    install_fake_client(
        monkeypatch,
        response=FakeResponse(
            status_code=200,
            body={
                "outcome": "no_context",
                "answer": "Approved no-context answer.",
                "sources": [],
                "retrieved_count": 0,
                "source_count": 0,
                "context_available": False,
            },
        ),
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 1

    assert (
        "LIVE_RAG_API_SMOKE_CONTEXT_REQUIRED"
        in output
    )


def test_script_reports_non_success_without_private_data(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    enable_live_smoke(
        monkeypatch,
    )

    set_required_environment(
        monkeypatch,
    )

    install_fake_client(
        monkeypatch,
        response=FakeResponse(
            status_code=503,
            body={
                "error_code": (
                    "RAG_ORCHESTRATION_RETRIEVAL_FAILED"
                ),
                "message": "Private provider details.",
            },
        ),
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "HTTP status: 503" in output

    assert (
        "RAG_ORCHESTRATION_RETRIEVAL_FAILED"
        in output
    )

    assert ACCESS_TOKEN not in output
    assert QUESTION not in output
    assert "Private provider details" not in output


def test_script_rejects_invalid_success_response(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    enable_live_smoke(
        monkeypatch,
    )

    set_required_environment(
        monkeypatch,
    )

    install_fake_client(
        monkeypatch,
        response=FakeResponse(
            status_code=200,
            body={
                "outcome": "answered",
                "answer": "",
                "sources": [],
                "retrieved_count": 1,
                "source_count": 0,
                "context_available": True,
            },
        ),
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 1

    assert (
        "LIVE_RAG_API_SMOKE_INVALID_RESPONSE"
        in output
    )


def test_script_rejects_missing_access_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    enable_live_smoke(
        monkeypatch,
    )

    monkeypatch.delenv(
        "RAG_API_SMOKE_ACCESS_TOKEN",
        raising=False,
    )

    exit_code = smoke_module.main()

    output = capsys.readouterr().out

    assert exit_code == 1

    assert (
        "LIVE_RAG_API_SMOKE_CONFIGURATION_FAILED"
        in output
    )