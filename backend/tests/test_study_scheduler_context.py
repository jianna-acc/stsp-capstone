# File: /backend/tests/test_study_scheduler_context.py
# Purpose: Verifies Track D loading of existing onboarding
# scheduling preferences without depending on other tracks.

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.repositories.study_scheduler_context_repository import (
    StudySchedulerContextRepository,
)
from app.schemas.study_scheduler import (
    SchedulerAvailabilitySlot,
    SchedulerPreferences,
)
from app.schemas.study_scheduler_context import (
    StudySchedulerContext,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
    StudyPlanResponseError,
    StudyPlanValidationError,
)
from app.services.study_scheduler_context_service import (
    StudySchedulerContextService,
)

USER_ID = uuid4()


class FakeQuery:
    def __init__(
        self,
        data: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.data = data
        self.error = error

        self.calls: list[
            tuple[
                str,
                object,
            ]
        ] = []

    def select(
        self,
        columns: str,
    ) -> FakeQuery:
        self.calls.append(
            (
                "select",
                columns,
            )
        )

        return self

    def eq(
        self,
        column: str,
        value: object,
    ) -> FakeQuery:
        self.calls.append(
            (
                "eq",
                (
                    column,
                    value,
                ),
            )
        )

        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> FakeQuery:
        self.calls.append(
            (
                "order",
                (
                    column,
                    desc,
                ),
            )
        )

        return self

    def limit(
        self,
        count: int,
    ) -> FakeQuery:
        self.calls.append(
            (
                "limit",
                count,
            )
        )

        return self

    def execute(
        self,
    ) -> SimpleNamespace:
        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            data=self.data,
        )


class FakeClient:
    def __init__(
        self,
        *,
        profiles: FakeQuery,
        learning_profiles: FakeQuery,
        study_availability: FakeQuery,
    ) -> None:
        self.queries = {
            "profiles": profiles,
            "learning_profiles": (
                learning_profiles
            ),
            "study_availability": (
                study_availability
            ),
        }

    def table(
        self,
        table_name: str,
    ) -> FakeQuery:
        return self.queries[
            table_name
        ]


def _repository(
    *,
    timezone_value: object = "Asia/Manila",
    preferred_minutes: object = 60,
    availability: object | None = None,
) -> StudySchedulerContextRepository:
    if availability is None:
        availability = [
            {
                "day_of_week": 1,
                "start_time": "18:00:00",
                "end_time": "20:00:00",
            },
        ]

    return StudySchedulerContextRepository(
        FakeClient(
            profiles=FakeQuery(
                [
                    {
                        "timezone": (
                            timezone_value
                        ),
                    },
                ]
            ),
            learning_profiles=FakeQuery(
                [
                    {
                        "preferred_study_duration_minutes": (
                            preferred_minutes
                        ),
                    },
                ]
            ),
            study_availability=FakeQuery(
                availability,
            ),
        )
    )


def test_repository_loads_existing_context() -> None:
    """Existing onboarding values should feed Track D."""

    context = (
        _repository()
        .get_scheduler_context(
            user_id=USER_ID,
        )
    )

    assert context is not None

    assert (
        context.preferences.timezone
        == "Asia/Manila"
    )

    assert (
        context.preferences
        .preferred_session_minutes
        == 60
    )

    assert len(
        context.availability,
    ) == 1

    assert (
        context.availability[0]
        .day_of_week
        == 1
    )


def test_short_preference_uses_safe_minimum() -> None:
    """A ten-minute preference should remain valid."""

    context = (
        _repository(
            preferred_minutes=10,
        )
        .get_scheduler_context(
            user_id=USER_ID,
        )
    )

    assert context is not None

    assert (
        context.preferences
        .preferred_session_minutes
        == 10
    )

    assert (
        context.preferences
        .minimum_session_minutes
        == 10
    )


def test_repository_returns_none_without_availability() -> None:
    """Incomplete onboarding context should not schedule."""

    context = (
        _repository(
            availability=[],
        )
        .get_scheduler_context(
            user_id=USER_ID,
        )
    )

    assert context is None


def test_repository_rejects_invalid_preferences() -> None:
    """Malformed stored preference values should fail safely."""

    with pytest.raises(
        StudyPlanResponseError,
    ):
        (
            _repository(
                preferred_minutes="sixty",
            )
            .get_scheduler_context(
                user_id=USER_ID,
            )
        )


def test_repository_wraps_storage_error() -> None:
    """Supabase failures should become controlled errors."""

    repository = StudySchedulerContextRepository(
        FakeClient(
            profiles=FakeQuery(
                [],
                error=RuntimeError(
                    "storage unavailable",
                ),
            ),
            learning_profiles=FakeQuery(
                [],
            ),
            study_availability=FakeQuery(
                [],
            ),
        )
    )

    with pytest.raises(
        StudyPlanPersistenceError,
    ):
        repository.get_scheduler_context(
            user_id=USER_ID,
        )


class FakeContextRepository:
    def __init__(
        self,
        context: (
            StudySchedulerContext
            | None
        ),
    ) -> None:
        self.context = context

    def get_scheduler_context(
        self,
        *,
        user_id,
    ):
        del user_id

        return self.context


def _context() -> StudySchedulerContext:
    return StudySchedulerContext(
        preferences=SchedulerPreferences(
            timezone="Asia/Manila",
            preferred_session_minutes=60,
            minimum_session_minutes=15,
        ),
        availability=(
            SchedulerAvailabilitySlot(
                day_of_week=1,
                start_time="18:00:00",
                end_time="20:00:00",
            ),
        ),
    )


def test_context_service_returns_complete_context() -> None:
    """Complete onboarding context should be returned."""

    service = StudySchedulerContextService(
        FakeContextRepository(
            _context(),
        )
    )

    result = service.get_scheduler_context(
        user_id=USER_ID,
    )

    assert (
        result.preferences.timezone
        == "Asia/Manila"
    )


def test_context_service_rejects_missing_context() -> None:
    """Missing preferences should produce a controlled failure."""

    service = StudySchedulerContextService(
        FakeContextRepository(
            None,
        )
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        service.get_scheduler_context(
            user_id=USER_ID,
        )