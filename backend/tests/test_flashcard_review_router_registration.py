# File: /backend/tests/test_flashcard_review_router_registration.py
# Purpose: Protects Flashcard review route registration.

from app.main import app


def test_flashcard_review_route_is_registered() -> None:
    """FastAPI must expose the protected review endpoint."""

    schema = app.openapi()

    route = (
        "/api/flashcards/{deck_id}/reviews"
    )

    assert route in schema[
        "paths"
    ]

    assert "post" in schema[
        "paths"
    ][
        route
    ]