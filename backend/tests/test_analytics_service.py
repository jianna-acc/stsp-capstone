# File: /backend/tests/test_analytics_service.py
# Purpose: Verifies canonical and deferred Track E analytics behavior.

from uuid import UUID

from app.schemas.analytics import (
    AnalyticsAvailability,
    AnalyticsDataState,
    AnalyticsPeriod,
)
from app.services.analytics_service import AnalyticsService

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)


class FakeAnalyticsRepository:
    """Deterministic canonical analytics source for service tests."""

    def __init__(
        self,
        *,
        subject_count: int = 3,
        study_file_count: int = 8,
        ready_study_file_count: int = 6,
    ) -> None:
        self.subject_count = subject_count
        self.study_file_count = study_file_count
        self.ready_study_file_count = ready_study_file_count
        self.user_ids: list[UUID] = []

    def count_subjects(
        self,
        *,
        user_id: UUID,
    ) -> int:
        self.user_ids.append(
            user_id,
        )
        return self.subject_count

    def count_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int:
        self.user_ids.append(
            user_id,
        )
        return self.study_file_count

    def count_ready_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int:
        self.user_ids.append(
            user_id,
        )
        return self.ready_study_file_count


def test_overview_returns_canonical_counts_and_partial_state() -> None:
    """Canonical data is real while deferred performance stays unavailable."""

    repository = FakeAnalyticsRepository()
    service = AnalyticsService(
        repository=repository,
    )

    response = service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.ALL_TIME,
    )

    assert response.period is AnalyticsPeriod.ALL_TIME
    assert response.data_state is AnalyticsDataState.PARTIAL

    assert (
        response.subject_count.availability
        is AnalyticsAvailability.AVAILABLE
    )
    assert response.subject_count.value == 3

    assert (
        response.study_material_count.availability
        is AnalyticsAvailability.AVAILABLE
    )
    assert response.study_material_count.value == 8

    assert (
        response.ready_study_material_count.availability
        is AnalyticsAvailability.AVAILABLE
    )
    assert response.ready_study_material_count.value == 6

    assert (
        response.quiz_accuracy_percent.availability
        is AnalyticsAvailability.UNAVAILABLE
    )
    assert response.quiz_accuracy_percent.value is None

    assert (
        response.flashcard_performance_percent.availability
        is AnalyticsAvailability.UNAVAILABLE
    )
    assert response.flashcard_performance_percent.value is None

    assert (
        response.study_minutes.availability
        is AnalyticsAvailability.UNAVAILABLE
    )

    assert response.strong_topics == ()
    assert response.weak_topics == ()


def test_overview_scopes_all_queries_to_authenticated_user() -> None:
    """Every canonical query must use the authenticated user's UUID."""

    repository = FakeAnalyticsRepository()
    service = AnalyticsService(
        repository=repository,
    )

    service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.LAST_30_DAYS,
    )

    assert repository.user_ids == [
        USER_ID,
        USER_ID,
        USER_ID,
    ]


def test_overview_supports_zero_canonical_records() -> None:
    """A new student with no records should receive valid zero counts."""

    repository = FakeAnalyticsRepository(
        subject_count=0,
        study_file_count=0,
        ready_study_file_count=0,
    )
    service = AnalyticsService(
        repository=repository,
    )

    response = service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.LAST_7_DAYS,
    )

    assert response.subject_count.value == 0
    assert response.study_material_count.value == 0
    assert response.ready_study_material_count.value == 0

    assert response.subject_count.availability is (
        AnalyticsAvailability.AVAILABLE
    )