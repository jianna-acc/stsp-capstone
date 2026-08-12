# File: /backend/app/schemas/analytics.py
# Purpose: Defines stable API contracts for study analytics.

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AnalyticsPeriod(str, Enum):
    """Supported reporting periods for period-sensitive analytics."""

    ALL_TIME = "all_time"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"


class AnalyticsAvailability(str, Enum):
    """Indicates whether a metric currently has a canonical data source."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class AnalyticsDataState(str, Enum):
    """Describes the overall readiness of an analytics response."""

    PARTIAL = "partial"
    READY = "ready"


class AnalyticsCountScope(str, Enum):
    """Defines how a count metric should be interpreted."""

    CURRENT_INVENTORY = "current_inventory"


class AnalyticsMetric(BaseModel):
    """One percentage or duration metric and its evidence state."""

    availability: AnalyticsAvailability
    value: float | None = None
    sample_size: int = Field(
        default=0,
        ge=0,
    )
    message: str | None = None


class AnalyticsCountMetric(BaseModel):
    """One current-inventory count metric."""

    availability: AnalyticsAvailability
    value: int | None = Field(
        default=None,
        ge=0,
    )
    scope: AnalyticsCountScope = (
        AnalyticsCountScope.CURRENT_INVENTORY
    )
    message: str | None = None


class AnalyticsTopicPerformance(BaseModel):
    """Performance summary for one study topic."""

    topic: str
    score_percent: float = Field(
        ge=0.0,
        le=100.0,
    )
    sample_size: int = Field(
        ge=1,
    )


class AnalyticsApiErrorResponse(BaseModel):
    """Controlled Analytics API error response."""

    detail: str


class AnalyticsOverviewResponse(BaseModel):
    """Top-level analytics overview for the authenticated student."""

    period: AnalyticsPeriod
    data_state: AnalyticsDataState

    subject_count: AnalyticsCountMetric
    study_material_count: AnalyticsCountMetric
    ready_study_material_count: AnalyticsCountMetric

    quiz_accuracy_percent: AnalyticsMetric
    flashcard_performance_percent: AnalyticsMetric
    study_minutes: AnalyticsMetric

    strong_topics: tuple[
        AnalyticsTopicPerformance,
        ...,
    ] = ()
    weak_topics: tuple[
        AnalyticsTopicPerformance,
        ...,
    ] = ()