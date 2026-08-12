# File: /backend/tests/test_study_activity_router_registration.py
# Purpose: Protects Study Activity timer endpoint registration
# in the shared FastAPI OpenAPI contract.

from app.main import app


def test_study_activity_routes_are_registered() -> None:
    """All Study Activity lifecycle routes must remain exposed."""

    schema = app.openapi()

    paths = schema[
        "paths"
    ]

    expected = {
        "/api/study-activity/active": "get",
        "/api/study-activity/start": "post",
        "/api/study-activity/{activity_id}/pause": "post",
        "/api/study-activity/{activity_id}/resume": "post",
        "/api/study-activity/{activity_id}/break/start": "post",
        "/api/study-activity/{activity_id}/break/end": "post",
        "/api/study-activity/{activity_id}/end": "post",
    }

    for path, method in expected.items():
        assert path in paths
        assert method in paths[
            path
        ]