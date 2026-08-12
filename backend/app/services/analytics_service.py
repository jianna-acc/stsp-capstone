# File: /backend/app/services/analytics_service.py
# Purpose: Builds authenticated study analytics from canonical feature data.

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from app.repositories.analytics_repository import (
    FlashcardReviewAnalyticsRecord,
    QuizAnswerAnalyticsRecord,
    QuizAttemptAnalyticsRecord,
    StudyActivityAnalyticsRecord,
)
from app.schemas.analytics import (
    AnalyticsAvailability,
    AnalyticsCountMetric,
    AnalyticsDataState,
    AnalyticsMetric,
    AnalyticsOverviewResponse,
    AnalyticsPeriod,
    AnalyticsStudyWeek,
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

    def list_completed_study_activities(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        StudyActivityAnalyticsRecord,
        ...,
    ]: ...


class AnalyticsService:
    """Build study analytics from canonical persisted evidence."""

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

        subject_count = (
            self._repository.count_subjects(
                user_id=user_id,
            )
        )

        study_material_count = (
            self._repository.count_study_files(
                user_id=user_id,
            )
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

        period_attempts = (
            self._filter_quiz_attempts(
                completed_attempts,
                period=period,
            )
        )

        quiz_accuracy = (
            self._build_quiz_accuracy(
                period_attempts,
            )
        )

        topic_performance = (
            self._build_topic_performance(
                period_attempts,
            )
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

        completed_study_activities = (
            self._repository.list_completed_study_activities(
                user_id=user_id,
            )
        )

        period_study_activities = (
            self._filter_study_activities(
                completed_study_activities,
                period=period,
            )
        )

        study_minutes = (
            self._build_study_minutes(
                period_study_activities,
            )
        )

        study_time_by_week = (
            self._build_study_time_by_week(
                period_study_activities,
            )
        )

        return AnalyticsOverviewResponse(
            period=period,
            data_state=AnalyticsDataState.READY,
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
            study_minutes=study_minutes,
            study_time_by_week=study_time_by_week,
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

        cutoff = self._period_cutoff(
            period,
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

        cutoff = self._period_cutoff(
            period,
        )

        return tuple(
            review
            for review in reviews
            if review.reviewed_at >= cutoff
        )

    def _filter_study_activities(
        self,
        activities: tuple[
            StudyActivityAnalyticsRecord,
            ...,
        ],
        *,
        period: AnalyticsPeriod,
    ) -> tuple[
        StudyActivityAnalyticsRecord,
        ...,
    ]:
        """Apply the reporting period to completed actual-study evidence."""

        if period is AnalyticsPeriod.ALL_TIME:
            return activities

        cutoff = self._period_cutoff(
            period,
        )

        return tuple(
            activity
            for activity in activities
            if activity.ended_at >= cutoff
        )

    def _period_cutoff(
        self,
        period: AnalyticsPeriod,
    ) -> datetime:
        """Return the UTC cutoff for one period-sensitive metric."""

        now = self._clock()

        if now.tzinfo is None:
            raise ValueError(
                "Analytics clock must return a timezone-aware datetime.",
            )

        now = now.astimezone(
            timezone.utc,
        )

        if period is AnalyticsPeriod.LAST_7_DAYS:
            return now - timedelta(
                days=7,
            )

        if period is AnalyticsPeriod.LAST_30_DAYS:
            return now - timedelta(
                days=30,
            )

        raise ValueError(
            "A cutoff is not required for all-time Analytics.",
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
            review.outcome
            is FlashcardReviewOutcome.KNOWN
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

    def _build_study_minutes(
        self,
        activities: tuple[
            StudyActivityAnalyticsRecord,
            ...,
        ],
    ) -> AnalyticsMetric:
        """Calculate actual focus minutes from completed timer sessions."""

        if not activities:
            return AnalyticsMetric(
                availability=AnalyticsAvailability.AVAILABLE,
                value=None,
                sample_size=0,
                message=(
                    "No completed study sessions are available for "
                    "the selected period."
                ),
            )

        focus_seconds = sum(
            activity.focus_seconds
            for activity in activities
        )

        study_minutes = round(
            focus_seconds / 60,
            2,
        )

        return AnalyticsMetric(
            availability=AnalyticsAvailability.AVAILABLE,
            value=study_minutes,
            sample_size=len(
                activities,
            ),
        )

    @staticmethod
    def _build_study_time_by_week(
        activities: tuple[
            StudyActivityAnalyticsRecord,
            ...,
        ],
    ) -> tuple[
        AnalyticsStudyWeek,
        ...,
    ]:
        """Group actual completed focus time into UTC Monday-Sunday weeks."""

        focus_seconds_by_week: dict[
            date,
            int,
        ] = {}

        session_count_by_week: dict[
            date,
            int,
        ] = {}

        for activity in activities:
            ended_date = (
                activity.ended_at
                .astimezone(
                    timezone.utc,
                )
                .date()
            )

            week_start = (
                ended_date
                - timedelta(
                    days=ended_date.weekday(),
                )
            )

            focus_seconds_by_week[
                week_start
            ] = (
                focus_seconds_by_week.get(
                    week_start,
                    0,
                )
                + activity.focus_seconds
            )

            session_count_by_week[
                week_start
            ] = (
                session_count_by_week.get(
                    week_start,
                    0,
                )
                + 1
            )

        return tuple(
            AnalyticsStudyWeek(
                week_start=week_start,
                week_end=(
                    week_start
                    + timedelta(
                        days=6,
                    )
                ),
                study_minutes=round(
                    focus_seconds_by_week[
                        week_start
                    ]
                    / 60,
                    2,
                ),
                session_count=(
                    session_count_by_week[
                        week_start
                    ]
                ),
            )
            for week_start in sorted(
                focus_seconds_by_week,
            )
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
            answers = (
                self._repository.list_quiz_attempt_answers(
                    attempt_id=attempt.id,
                )
            )

            for answer in answers:
                key = (
                    answer.topic
                    .strip()
                    .casefold()
                )

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
            sample_size = (
                question_counts[
                    key
                ]
            )

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