# File: /backend/app/services/analytics_service.py
# Purpose: Builds authenticated study analytics from canonical feature data.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.analytics import (
    AnalyticsAvailability,
    AnalyticsCountMetric,
    AnalyticsDataState,
    AnalyticsMetric,
    AnalyticsOverviewResponse,
    AnalyticsPeriod,
)


class AnalyticsDataSource(
    Protocol,
):
    """Canonical record counts required by the Analytics service."""

    def count_subjects(
        self,
        *,
        user_id: UUID,
    ) -> int: ...

    def count_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int: ...

    def count_ready_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int: ...


class AnalyticsService:
    """Build study analytics without fabricating unavailable data."""

    def __init__(
        self,
        repository: AnalyticsDataSource,
    ) -> None:
        self._repository = repository

    def get_overview(
        self,
        *,
        user_id: UUID,
        period: AnalyticsPeriod,
    ) -> AnalyticsOverviewResponse:
        """Return currently supported analytics for one student."""

        subject_count = self._repository.count_subjects(
            user_id=user_id,
        )
        study_material_count = self._repository.count_study_files(
            user_id=user_id,
        )
        ready_study_material_count = (
            self._repository.count_ready_study_files(
                user_id=user_id,
            )
        )

        return AnalyticsOverviewResponse(
            period=period,
            data_state=AnalyticsDataState.PARTIAL,
            subject_count=self._available_count(
                subject_count,
            ),
            study_material_count=self._available_count(
                study_material_count,
            ),
            ready_study_material_count=self._available_count(
                ready_study_material_count,
            ),
            quiz_accuracy_percent=self._unavailable_metric(
                (
                    "Quiz analytics will be available after the canonical "
                    "Track B quiz data source is integrated."
                ),
            ),
            flashcard_performance_percent=self._unavailable_metric(
                (
                    "Flashcard analytics will be available after the "
                    "canonical Track A flashcard data source is integrated."
                ),
            ),
            study_minutes=self._unavailable_metric(
                (
                    "No canonical general study-activity duration source "
                    "is available yet."
                ),
            ),
            strong_topics=(),
            weak_topics=(),
        )

    @staticmethod
    def _available_count(
        value: int,
    ) -> AnalyticsCountMetric:
        """Create an available canonical count metric."""

        return AnalyticsCountMetric(
            availability=AnalyticsAvailability.AVAILABLE,
            value=value,
        )

    @staticmethod
    def _unavailable_metric(
        message: str,
    ) -> AnalyticsMetric:
        """Create a metric that has no canonical source yet."""

        return AnalyticsMetric(
            availability=AnalyticsAvailability.UNAVAILABLE,
            value=None,
            sample_size=0,
            message=message,
        )