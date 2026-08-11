# File: /backend/app/services/analytics_service.py
# Purpose: Builds authenticated study analytics from canonical feature data.

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from app.repositories.analytics_repository import (
    FlashcardReviewAnalyticsRecord,
    QuizAnswerAnalyticsRecord,
    QuizAttemptAnalyticsRecord,
)
from app.schemas.analytics import (
    AnalyticsAvailability,
    AnalyticsCountMetric,
    AnalyticsDataState,
    AnalyticsMetric,
    AnalyticsOverviewResponse,
    AnalyticsPeriod,
    AnalyticsTopicPerformance,
)
from app.schemas.flashcard_review import (
    FlashcardReviewOutcome,
)
from app.services.quiz_attempt_service import (
    STRONG_TOPIC_THRESHOLD_PERCENTAGE,
)


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc,
    )


class AnalyticsDataSource(
    Protocol,
):
    """Canonical records required by the Analytics service."""

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

    def list_completed_quiz_attempts(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        QuizAttemptAnalyticsRecord,
        ...,
    ]: ...

    def list_quiz_attempt_answers(
        self,
        *,
        attempt_id: UUID,
    ) -> tuple[
        QuizAnswerAnalyticsRecord,
        ...,
    ]: ...

    def list_flashcard_review_events(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        FlashcardReviewAnalyticsRecord,
        ...,
    ]: ...


class AnalyticsService:
    """Build study analytics without fabricating unavailable data."""

    def __init__(
        self,
        repository: AnalyticsDataSource,
        *,
        clock: Callable[
            [],
            datetime,
        ]
        | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or _utc_now

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

        completed_attempts = (
            self._repository.list_completed_quiz_attempts(
                user_id=user_id,
            )
        )

        period_attempts = self._filter_quiz_attempts(
            completed_attempts,
            period=period,
        )

        quiz_accuracy = self._build_quiz_accuracy(
            period_attempts,
        )

        topic_performance = self._build_topic_performance(
            period_attempts,
        )

        strong_topics = tuple(
            result
            for result in topic_performance
            if (
                result.score_percent
                >= STRONG_TOPIC_THRESHOLD_PERCENTAGE
            )
        )

        weak_topics = tuple(
            result
            for result in topic_performance
            if (
                result.score_percent
                < STRONG_TOPIC_THRESHOLD_PERCENTAGE
            )
        )

        flashcard_reviews = (
            self._repository.list_flashcard_review_events(
                user_id=user_id,
            )
        )

        period_flashcard_reviews = (
            self._filter_flashcard_reviews(
                flashcard_reviews,
                period=period,
            )
        )

        flashcard_performance = (
            self._build_flashcard_performance(
                period_flashcard_reviews,
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
            quiz_accuracy_percent=quiz_accuracy,
            flashcard_performance_percent=flashcard_performance,
            study_minutes=self._unavailable_metric(
                (
                    "No canonical general study-activity duration source "
                    "is available yet."
                ),
            ),
            strong_topics=strong_topics,
            weak_topics=weak_topics,
        )

    def _filter_quiz_attempts(
        self,
        attempts: tuple[
            QuizAttemptAnalyticsRecord,
            ...,
        ],
        *,
        period: AnalyticsPeriod,
    ) -> tuple[
        QuizAttemptAnalyticsRecord,
        ...,
    ]:
        """Apply the selected reporting period to completed Quiz attempts."""

        if period is AnalyticsPeriod.ALL_TIME:
            return attempts

        now = self._clock()

        if now.tzinfo is None:
            raise ValueError(
                "Analytics clock must return a timezone-aware datetime.",
            )

        if period is AnalyticsPeriod.LAST_7_DAYS:
            cutoff = now - timedelta(
                days=7,
            )
        else:
            cutoff = now - timedelta(
                days=30,
            )

        return tuple(
            attempt
            for attempt in attempts
            if attempt.completed_at >= cutoff
        )

    def _filter_flashcard_reviews(
        self,
        reviews: tuple[
            FlashcardReviewAnalyticsRecord,
            ...,
        ],
        *,
        period: AnalyticsPeriod,
    ) -> tuple[
        FlashcardReviewAnalyticsRecord,
        ...,
    ]:
        """Apply the reporting period to Flashcard review evidence."""

        if period is AnalyticsPeriod.ALL_TIME:
            return reviews

        now = self._clock()

        if now.tzinfo is None:
            raise ValueError(
                "Analytics clock must return a timezone-aware datetime.",
            )

        if period is AnalyticsPeriod.LAST_7_DAYS:
            cutoff = now - timedelta(
                days=7,
            )
        else:
            cutoff = now - timedelta(
                days=30,
            )

        return tuple(
            review
            for review in reviews
            if review.reviewed_at >= cutoff
        )

    def _build_quiz_accuracy(
        self,
        attempts: tuple[
            QuizAttemptAnalyticsRecord,
            ...,
        ],
    ) -> AnalyticsMetric:
        """Calculate weighted accuracy across completed Quiz questions."""

        if not attempts:
            return AnalyticsMetric(
                availability=AnalyticsAvailability.AVAILABLE,
                value=None,
                sample_size=0,
                message=(
                    "No completed Quiz attempts are available for "
                    "the selected period."
                ),
            )

        correct_count = sum(
            attempt.correct_count
            for attempt in attempts
        )

        question_count = sum(
            attempt.question_count
            for attempt in attempts
        )

        accuracy = round(
            (
                correct_count
                / question_count
            )
            * 100,
            2,
        )

        return AnalyticsMetric(
            availability=AnalyticsAvailability.AVAILABLE,
            value=accuracy,
            sample_size=question_count,
        )

    def _build_flashcard_performance(
        self,
        reviews: tuple[
            FlashcardReviewAnalyticsRecord,
            ...,
        ],
    ) -> AnalyticsMetric:
        """Calculate self-assessed Flashcard knowledge percentage."""

        if not reviews:
            return AnalyticsMetric(
                availability=AnalyticsAvailability.AVAILABLE,
                value=None,
                sample_size=0,
                message=(
                    "No Flashcard review events are available for "
                    "the selected period."
                ),
            )

        known_count = sum(
            review.outcome is FlashcardReviewOutcome.KNOWN
            for review in reviews
        )

        performance = round(
            (
                known_count
                / len(
                    reviews,
                )
            )
            * 100,
            2,
        )

        return AnalyticsMetric(
            availability=AnalyticsAvailability.AVAILABLE,
            value=performance,
            sample_size=len(
                reviews,
            ),
        )

    def _build_topic_performance(
        self,
        attempts: tuple[
            QuizAttemptAnalyticsRecord,
            ...,
        ],
    ) -> tuple[
        AnalyticsTopicPerformance,
        ...,
    ]:
        """Aggregate Quiz correctness by normalized topic."""

        correct_counts: dict[
            str,
            int,
        ] = {}

        question_counts: dict[
            str,
            int,
        ] = {}

        display_names: dict[
            str,
            str,
        ] = {}

        for attempt in attempts:
            answers = self._repository.list_quiz_attempt_answers(
                attempt_id=attempt.id,
            )

            for answer in answers:
                key = answer.topic.strip().casefold()

                if key not in display_names:
                    display_names[
                        key
                    ] = answer.topic.strip()

                    correct_counts[
                        key
                    ] = 0

                    question_counts[
                        key
                    ] = 0

                question_counts[
                    key
                ] += 1

                if answer.is_correct:
                    correct_counts[
                        key
                    ] += 1

        results: list[
            AnalyticsTopicPerformance
        ] = []

        for key in sorted(
            display_names,
        ):
            sample_size = question_counts[
                key
            ]

            score = round(
                (
                    correct_counts[
                        key
                    ]
                    / sample_size
                )
                * 100,
                2,
            )

            results.append(
                AnalyticsTopicPerformance(
                    topic=display_names[
                        key
                    ],
                    score_percent=score,
                    sample_size=sample_size,
                ),
            )

        return tuple(
            results,
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