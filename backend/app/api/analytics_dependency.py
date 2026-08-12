# File: /backend/app/api/analytics_dependency.py
# Purpose: Provides the AnalyticsService to authenticated API routes.

from app.database.supabase_client import get_supabase_client
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService


def get_analytics_service() -> AnalyticsService:
    """Return the Analytics service backed by canonical Supabase data."""

    client = get_supabase_client()

    return AnalyticsService(
        repository=AnalyticsRepository(
            client,
        ),
    )