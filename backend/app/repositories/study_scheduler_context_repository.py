# File: /backend/app/repositories/study_scheduler_context_repository.py
# Purpose: Loads existing learning-profile scheduling preferences
# and recurring availability for Track D through Supabase.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from typing import (
    Protocol,
    Self,
)
from uuid import UUID

from pydantic import ValidationError

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
)


class _SupabaseResponse(
    Protocol,
):
    data: object


class _SupabaseQuery(
    Protocol,
):
    def select(
        self,
        columns: str,
    ) -> Self: ...

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> Self: ...

    def limit(
        self,
        count: int,
    ) -> Self: ...

    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseClient(
    Protocol,
):
    def table(
        self,
        table_name: str,
    ) -> _SupabaseQuery: ...


class StudySchedulerContextRepository:
    """Loads one student's existing scheduling preferences."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def get_scheduler_context(
        self,
        *,
        user_id: UUID,
    ) -> StudySchedulerContext | None:
        """Load availability and study preferences for one student."""

        profile_rows = self._query_rows(
            self._client
            .table(
                "profiles",
            )
            .select(
                "timezone",
            )
            .eq(
                "id",
                str(
                    user_id,
                ),
            )
            .limit(
                1,
            ),
            operation=(
                "load the student scheduling profile"
            ),
        )

        if not profile_rows:
            return None

        learning_profile_rows = self._query_rows(
            self._client
            .table(
                "learning_profiles",
            )
            .select(
                "preferred_study_duration_minutes",
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .limit(
                1,
            ),
            operation=(
                "load the student learning preferences"
            ),
        )

        if not learning_profile_rows:
            return None

        availability_rows = self._query_rows(
            self._client
            .table(
                "study_availability",
            )
            .select(
                "day_of_week,start_time,end_time",
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "day_of_week",
            )
            .order(
                "start_time",
            ),
            operation=(
                "load the student study availability"
            ),
        )

        if not availability_rows:
            return None

        profile = profile_rows[0]
        learning_profile = (
            learning_profile_rows[0]
        )

        timezone_value = profile.get(
            "timezone",
        )

        preferred_minutes = (
            learning_profile.get(
                "preferred_study_duration_minutes",
            )
        )

        if (
            not isinstance(
                timezone_value,
                str,
            )
            or isinstance(
                preferred_minutes,
                bool,
            )
            or not isinstance(
                preferred_minutes,
                int,
            )
        ):
            raise StudyPlanResponseError(
                "Stored scheduling preferences "
                "were invalid.",
            )

        minimum_minutes = min(
            15,
            preferred_minutes,
        )

        try:
            preferences = SchedulerPreferences(
                timezone=timezone_value,
                preferred_session_minutes=(
                    preferred_minutes
                ),
                minimum_session_minutes=(
                    minimum_minutes
                ),
            )

            availability = tuple(
                SchedulerAvailabilitySlot.model_validate(
                    row,
                )
                for row in availability_rows
            )

            return StudySchedulerContext(
                preferences=preferences,
                availability=availability,
            )

        except ValidationError as exc:
            raise StudyPlanResponseError(
                "Stored scheduling preferences "
                "were invalid.",
            ) from exc

    def _query_rows(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Execute one context query and validate its rows."""

        try:
            response = query.execute()

        except Exception as exc:
            raise StudyPlanPersistenceError(
                f"Unable to {operation}.",
            ) from exc

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            isinstance(
                data,
                (str, bytes),
            )
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise StudyPlanResponseError(
                "Supabase returned invalid "
                "scheduler-context data.",
            )

        rows: list[
            Mapping[
                str,
                object,
            ]
        ] = []

        for item in data:
            if not isinstance(
                item,
                Mapping,
            ):
                raise StudyPlanResponseError(
                    "Supabase returned an invalid "
                    "scheduler-context row.",
                )

            rows.append(
                item,
            )

        return rows