# File: /backend/tests/test_analytics_router_registration.py
# Purpose: Verifies that the Track E Analytics API is registered.

from app.main import app


def test_analytics_overview_route_is_registered() -> None:
    """The application must expose the authenticated Analytics endpoint."""

    schema = app.openapi()

    assert "/api/analytics/overview" in schema[
        "paths"
    ]
    assert "get" in schema[
        "paths"
    ][
        "/api/analytics/overview"
    ]