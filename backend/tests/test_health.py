# File: /backend/tests/test_health.py
# Purpose: Verifies the health endpoint's status code and response data.

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_healthy_status() -> None:
    """The health endpoint should report a working backend."""

    response = client.get("/api/health")

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["status"] == "healthy"
    assert response_data["service"] == "STS Capstone API"
    assert response_data["version"] == "0.1.0"
    assert response_data["environment"] == "development"


def test_health_endpoint_allows_frontend_origin() -> None:
    """CORS should allow requests from the configured frontend."""

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
