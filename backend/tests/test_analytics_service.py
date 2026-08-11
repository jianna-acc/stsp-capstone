# File: /backend/tests/test_analytics_service.py
# Purpose: Verifies canonical Track E Analytics aggregation behavior.

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.repositories.analytics_repository import (
    QuizAnswerAnalyticsRecord,
    QuizAttemptAnalyticsRecord,
)
from app.schemas.analytics import (
    AnalyticsAvailability,
    AnalyticsDataState,
    AnalyticsPeriod,
)
from app.services.analytics_service import AnalyticsService

USER_ID = UUID(
    "11111111-1111-4111-8111-111111111111",
)

ATTEMPT_ONE_ID = UUID(
    "22222222-2222-4222-8222-222222222222",
)

ATTEMPT_TWO_ID = UUID(
    "33333333-3333-4333-8333-333333333333",
)

NOW = datetime(
    2026,
    8,
    11,
    6,
    0,
    tzinfo=timezone.utc,
)


class FakeAnalyticsRepository:
    """Deterministic canonical Analytics source for service tests."""

    def __init__(self) -> None:
        self.user_ids: list[
            UUID
        ] = []

        self.attempts = (
            QuizAttemptAnalyticsRecord(
                id=ATTEMPT_ONE_ID,
                correct_count=8,
                question_count=10,
                completed_at=NOW
                - timedelta(
                    days=2,
                ),
            ),
            QuizAttemptAnalyticsRecord(
                id=ATTEMPT_TWO_ID,
                correct_count=3,
                question_count=5,
                completed_at=NOW
                - timedelta(
                    days=20,
                ),
            ),
        )

        self.answers = {
            ATTEMPT_ONE_ID: (
                QuizAnswerAnalyticsRecord(
                    topic="Algebra",
                    is_correct=True,
                ),
                QuizAnswerAnalyticsRecord(
                    topic="Algebra",
                    is_correct=True,
                ),
                QuizAnswerAnalyticsRecord(
                    topic="Algebra",
                    is_correct=True,
                ),
                QuizAnswerAnalyticsRecord(
                    topic="Algebra",
                    is_correct=False,
                ),
                QuizAnswerAnalyticsRecord(
                    topic="Biology",
                    is_correct=True,
                ),
                QuizAnswerAnalyticsRecord(
                    topic="Biology",
                    is_correct=False,
                ),
            ),
            ATTEMPT_TWO_ID: (
                QuizAnswerAnalyticsRecord(
                    topic="Biology",
                    is_correct=False,
                ),
                QuizAnswerAnalyticsRecord(
                    topic="Biology",
                    is_correct=True,
                ),
            ),
        }

    def count_subjects(
        self,
        *,
        user_id: UUID,
    ) -> int:
        self.user_ids.append(
            user_id,
        )
        return 3

    def count_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int:
        self.user_ids.append(
            user_id,
        )
        return 8

    def count_ready_study_files(
        self,
        *,
        user_id: UUID,
    ) -> int:
        self.user_ids.append(
            user_id,
        )
        return 6

    def list_completed_quiz_attempts(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        QuizAttemptAnalyticsRecord,
        ...,
    ]:
        self.user_ids.append(
            user_id,
        )
        return self.attempts

    def list_quiz_attempt_answers(
        self,
        *,
        attempt_id: UUID,
    ) -> tuple[
        QuizAnswerAnalyticsRecord,
        ...,
    ]:
        return self.answers.get(
            attempt_id,
            (),
        )


def _service(
    repository: FakeAnalyticsRepository,
) -> AnalyticsService:
    """Create an Analytics service with a deterministic clock."""

    return AnalyticsService(
        repository=repository,
        clock=lambda: NOW,
    )


def test_all_time_overview_uses_real_quiz_evidence() -> None:
    """All-time Analytics aggregates completed canonical Quiz attempts."""

    repository = FakeAnalyticsRepository()
    service = _service(
        repository,
    )

    response = service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.ALL_TIME,
    )

    assert response.data_state is AnalyticsDataState.PARTIAL

    assert response.subject_count.value == 3
    assert response.study_material_count.value == 8
    assert response.ready_study_material_count.value == 6

    assert response.quiz_accuracy_percent.availability is (
        AnalyticsAvailability.AVAILABLE
    )
    assert response.quiz_accuracy_percent.value == 73.33
    assert response.quiz_accuracy_percent.sample_size == 15

    assert [
        (
            item.topic,
            item.score_percent,
            item.sample_size,
        )
        for item in response.strong_topics
    ] == [
        (
            "Algebra",
            75.0,
            4,
        ),
    ]

    assert [
        (
            item.topic,
            item.score_percent,
            item.sample_size,
        )
        for item in response.weak_topics
    ] == [
        (
            "Biology",
            50.0,
            4,
        ),
    ]

    assert response.flashcard_performance_percent.availability is (
        AnalyticsAvailability.UNAVAILABLE
    )


def test_last_7_days_excludes_old_quiz_attempts() -> None:
    """Period-sensitive Quiz Analytics excludes older attempts."""

    repository = FakeAnalyticsRepository()
    service = _service(
        repository,
    )

    response = service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.LAST_7_DAYS,
    )

    assert response.quiz_accuracy_percent.value == 80.0
    assert response.quiz_accuracy_percent.sample_size == 10

    assert len(
        response.strong_topics,
    ) == 1

    assert len(
        response.weak_topics,
    ) == 1


def test_last_30_days_includes_both_quiz_attempts() -> None:
    """Thirty-day Analytics includes both deterministic attempts."""

    repository = FakeAnalyticsRepository()
    service = _service(
        repository,
    )

    response = service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.LAST_30_DAYS,
    )

    assert response.quiz_accuracy_percent.value == 73.33
    assert response.quiz_accuracy_percent.sample_size == 15


def test_no_completed_quizzes_returns_available_empty_metric() -> None:
    """No evidence is different from an unavailable Quiz data source."""

    repository = FakeAnalyticsRepository()
    repository.attempts = ()

    service = _service(
        repository,
    )

    response = service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.ALL_TIME,
    )

    assert response.quiz_accuracy_percent.availability is (
        AnalyticsAvailability.AVAILABLE
    )
    assert response.quiz_accuracy_percent.value is None
    assert response.quiz_accuracy_percent.sample_size == 0
    assert response.quiz_accuracy_percent.message is not None

    assert response.strong_topics == ()
    assert response.weak_topics == ()


def test_overview_scopes_canonical_queries_to_authenticated_user() -> None:
    """Owner-scoped Analytics reads must receive the authenticated UUID."""

    repository = FakeAnalyticsRepository()
    service = _service(
        repository,
    )

    service.get_overview(
        user_id=USER_ID,
        period=AnalyticsPeriod.ALL_TIME,
    )

    assert repository.user_ids == [
        USER_ID,
        USER_ID,
        USER_ID,
        USER_ID,
    ]