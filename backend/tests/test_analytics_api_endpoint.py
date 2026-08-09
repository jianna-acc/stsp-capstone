# File: /backend/tests/test_analytics_api_endpoint.py
# Purpose: Verifies authentication and response behavior for Analytics.

from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.analytics_dependency import (
    get_analytics_service,
)
from app.api.authenticated_user_dependency import (
    require_authenticated_user,
)
from app.main import app
from app.schemas.analytics import (
    AnalyticsAvailability,
    AnalyticsCountMetric,
    AnalyticsDataState,
    AnalyticsMetric,
    AnalyticsOverviewResponse,
    AnalyticsPeriod,
)
from app.services.analytics_errors import AnalyticsRepositoryError

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)


def _authenticated_user() -> SimpleNamespace:
    """Return a deterministic authenticated user for endpoint tests."""

    return SimpleNamespace(
        user_id=USER_ID,
    )


class FakeAnalyticsService:
    """Return deterministic Analytics responses for API tests."""

    def get_overview(
        self,
        *,
        user_id: UUID,
        period: AnalyticsPeriod,
    ) -> AnalyticsOverviewResponse:
        assert user_id == USER_ID

        unavailable = AnalyticsMetric(
            availability=AnalyticsAvailability.UNAVAILABLE,
            value=None,
            sample_size=0,
            message="Canonical source not integrated.",
        )

        return AnalyticsOverviewResponse(
            period=period,
            data_state=AnalyticsDataState.PARTIAL,
            subject_count=AnalyticsCountMetric(
                availability=AnalyticsAvailability.AVAILABLE,
                value=3,
            ),
            study_material_count=AnalyticsCountMetric(
                availability=AnalyticsAvailability.AVAILABLE,
                value=8,
            ),
            ready_study_material_count=AnalyticsCountMetric(
                availability=AnalyticsAvailability.AVAILABLE,
                value=6,
            ),
            quiz_accuracy_percent=unavailable,
            flashcard_performance_percent=unavailable,
            study_minutes=unavailable,
            strong_topics=(),
            weak_topics=(),
        )


def _analytics_service() -> FakeAnalyticsService:
    """Return the deterministic API-test Analytics service."""

    return FakeAnalyticsService()

class FailingAnalyticsService:
    """Simulate unavailable canonical Analytics data."""

    def get_overview(
        self,
        *,
        user_id: UUID,
        period: AnalyticsPeriod,
    ) -> AnalyticsOverviewResponse:
        _ = (
            user_id,
            period,
        )

        raise AnalyticsRepositoryError(
            "Canonical Analytics data failed.",
        )

def _failing_analytics_service() -> FailingAnalyticsService:
    """Return a failing Analytics service for API tests."""

    return FailingAnalyticsService()

def test_analytics_overview_requires_authentication() -> None:
    """Analytics must reject requests without student authentication."""

    with TestClient(app) as client:
        response = client.get(
            "/api/analytics/overview",
        )

    assert response.status_code == 401


def test_authenticated_user_can_get_analytics_overview() -> None:
    """Authenticated users receive available and deferred metrics."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user
    app.dependency_overrides[
        get_analytics_service
    ] = _analytics_service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/analytics/overview",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    payload = response.json()

    assert payload["period"] == "all_time"
    assert payload["data_state"] == "partial"

    assert payload["subject_count"] == {
        "availability": "available",
        "value": 3,
        "scope": "current_inventory",
        "message": None,
    }

    assert payload["study_material_count"]["value"] == 8
    assert payload["ready_study_material_count"]["value"] == 6

    assert (
        payload["quiz_accuracy_percent"]["availability"]
        == "unavailable"
    )
    assert payload["quiz_accuracy_percent"]["value"] is None

    assert (
        payload["flashcard_performance_percent"]["availability"]
        == "unavailable"
    )

    assert payload["study_minutes"]["availability"] == "unavailable"
    assert payload["strong_topics"] == []
    assert payload["weak_topics"] == []


def test_analytics_overview_accepts_supported_period() -> None:
    """A supported period must be reflected in the response."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user
    app.dependency_overrides[
        get_analytics_service
    ] = _analytics_service

    try:
        with TestClient(app) as client:
            response = client.get(
                (
                    "/api/analytics/overview"
                    "?period=last_7_days"
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["period"] == "last_7_days"


def test_analytics_overview_rejects_unknown_period() -> None:
    """Unsupported reporting periods must fail validation."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user
    app.dependency_overrides[
        get_analytics_service
    ] = _analytics_service

    try:
        with TestClient(app) as client:
            response = client.get(
                (
                    "/api/analytics/overview"
                    "?period=last_365_days"
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

def test_analytics_overview_returns_503_for_data_source_error() -> None:
    """Controlled canonical-data failures must not leak as server errors."""

    app.dependency_overrides[
        require_authenticated_user
    ] = _authenticated_user
    app.dependency_overrides[
        get_analytics_service
    ] = _failing_analytics_service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/analytics/overview",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Analytics data is temporarily unavailable.",
    }