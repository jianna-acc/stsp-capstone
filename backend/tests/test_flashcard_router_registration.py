# File: /backend/tests/test_flashcard_router_registration.py
# Purpose: Verifies that the protected Flashcard API is exposed
# by the real FastAPI application under the shared /api prefix.

from __future__ import annotations

from app.main import app


def test_flashcard_paths_are_exposed_in_openapi() -> None:
    """OpenAPI must expose all student-facing Flashcard paths."""

    paths = app.openapi()[
        "paths"
    ]

    assert (
        "/api/flashcards/generate"
        in paths
    )

    assert (
        "/api/flashcards"
        in paths
    )

    assert (
        "/api/flashcards/{deck_id}"
        in paths
    )


def test_flashcard_openapi_exposes_expected_methods() -> None:
    """Public Flashcard operations must match the API contract."""

    paths = app.openapi()[
        "paths"
    ]

    generate_operations = paths[
        "/api/flashcards/generate"
    ]

    assert "post" in generate_operations

    list_operations = paths[
        "/api/flashcards"
    ]

    assert "get" in list_operations

    deck_operations = paths[
        "/api/flashcards/{deck_id}"
    ]

    assert "get" in deck_operations
    assert "delete" in deck_operations