# File: /backend/app/repositories/academic_task_priority_context_repository.py
# Purpose: Loads authenticated student timezone, output-confidence,
# and recurring availability data used by academic-task priority scoring.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import time
from typing import Protocol, Self
from uuid import UUID

from app.schemas.academic_task import (
    AcademicTaskOutputType,
)
from app.services.academic_task_errors import (
    AcademicTaskPersistenceError,
    AcademicTaskResponseError,
)
from app.services.academic_task_priority_context import (
    StudyAvailabilitySlot,
)

_CONFIDENCE_OUTPUT_TYPES = {
    AcademicTaskOutputType.WRITING.value,
    AcademicTaskOutputType.COMPUTATION.value,
    AcademicTaskOutputType.RESEARCH.value,
    AcademicTaskOutputType.PRESENTATION.value,
    AcademicTaskOutputType.CREATIVE.value,
    AcademicTaskOutputType.READING_ANALYSIS.value,
    AcademicTaskOutputType.MEMORIZATION.value,
}


@dataclass(
    frozen=True,
    slots=True,
)
class AcademicTaskPriorityContextData:
    """Student context required for academic-task prioritization."""

    timezone_name: str
    confidence_levels: dict[str, int]
    availability_slots: tuple[
        StudyAvailabilitySlot,
        ...,
    ]


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


class AcademicTaskPriorityContextRepository:
    """Loads student-owned data used by the priority engine."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def load_priority_context(
        self,
        *,
        user_id: UUID,
    ) -> AcademicTaskPriorityContextData:
        """Load all available student priority context."""

        timezone_name = self._load_timezone(
            user_id=user_id,
        )

        confidence_levels = (
            self._load_output_confidences(
                user_id=user_id,
            )
        )

        availability_slots = (
            self._load_study_availability(
                user_id=user_id,
            )
        )

        return AcademicTaskPriorityContextData(
            timezone_name=timezone_name,
            confidence_levels=confidence_levels,
            availability_slots=tuple(
                availability_slots,
            ),
        )

    def _load_timezone(
        self,
        *,
        user_id: UUID,
    ) -> str:
        """Load the student's saved IANA timezone."""

        response = self._execute(
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
            operation="load the student timezone",
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise AcademicTaskResponseError(
                "The student timezone response was invalid.",
            )

        timezone_value = rows[
            0
        ].get(
            "timezone",
        )

        if not isinstance(
            timezone_value,
            str,
        ):
            raise AcademicTaskResponseError(
                "The stored student timezone was invalid.",
            )

        timezone_name = (
            timezone_value.strip()
        )

        if not timezone_name:
            raise AcademicTaskResponseError(
                "The stored student timezone was empty.",
            )

        return timezone_name

    def _load_output_confidences(
        self,
        *,
        user_id: UUID,
    ) -> dict[str, int]:
        """Load saved output-confidence ratings."""

        response = self._execute(
            self._client
            .table(
                "learning_output_confidences",
            )
            .select(
                "output_type,confidence_level",
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "output_type",
                desc=False,
            ),
            operation="load output-confidence ratings",
        )

        rows = self._extract_rows(
            response,
        )

        confidence_levels: dict[
            str,
            int,
        ] = {}

        for row in rows:
            output_type = row.get(
                "output_type",
            )

            confidence_level = row.get(
                "confidence_level",
            )

            if (
                not isinstance(
                    output_type,
                    str,
                )
                or output_type
                not in _CONFIDENCE_OUTPUT_TYPES
            ):
                raise AcademicTaskResponseError(
                    "A stored output-confidence type was invalid.",
                )

            if (
                isinstance(
                    confidence_level,
                    bool,
                )
                or not isinstance(
                    confidence_level,
                    int,
                )
                or not 1
                <= confidence_level
                <= 5
            ):
                raise AcademicTaskResponseError(
                    "A stored output-confidence level was invalid.",
                )

            if (
                output_type
                in confidence_levels
            ):
                raise AcademicTaskResponseError(
                    "Duplicate output-confidence data was returned.",
                )

            confidence_levels[
                output_type
            ] = confidence_level

        return confidence_levels

    def _load_study_availability(
        self,
        *,
        user_id: UUID,
    ) -> list[
        StudyAvailabilitySlot
    ]:
        """Load recurring weekly study-availability periods."""

        response = self._execute(
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
                desc=False,
            )
            .order(
                "start_time",
                desc=False,
            ),
            operation="load study availability",
        )

        rows = self._extract_rows(
            response,
        )

        slots: list[
            StudyAvailabilitySlot
        ] = []

        for row in rows:
            day_of_week = row.get(
                "day_of_week",
            )

            if (
                isinstance(
                    day_of_week,
                    bool,
                )
                or not isinstance(
                    day_of_week,
                    int,
                )
                or not 1
                <= day_of_week
                <= 7
            ):
                raise AcademicTaskResponseError(
                    "A stored study-availability weekday was invalid.",
                )

            start_time = self._parse_time(
                row.get(
                    "start_time",
                ),
                field_name="start_time",
            )

            end_time = self._parse_time(
                row.get(
                    "end_time",
                ),
                field_name="end_time",
            )

            if (
                start_time
                >= end_time
            ):
                raise AcademicTaskResponseError(
                    "A stored study-availability period was invalid.",
                )

            slots.append(
                StudyAvailabilitySlot(
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

        return slots

    def _parse_time(
        self,
        value: object,
        *,
        field_name: str,
    ) -> time:
        """Parse one Postgres time value safely."""

        if not isinstance(
            value,
            str,
        ):
            raise AcademicTaskResponseError(
                f"Stored {field_name} was invalid.",
            )

        try:
            parsed = time.fromisoformat(
                value,
            )

        except ValueError as exc:
            raise AcademicTaskResponseError(
                f"Stored {field_name} was invalid.",
            ) from exc

        if (
            parsed.tzinfo
            is not None
        ):
            raise AcademicTaskResponseError(
                f"Stored {field_name} must not contain a timezone.",
            )

        return parsed

    def _execute(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one context query safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise AcademicTaskPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _extract_rows(
        self,
        response: _SupabaseResponse,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Validate Supabase list responses."""

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
            raise AcademicTaskResponseError(
                "Supabase returned invalid priority-context data.",
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
                raise AcademicTaskResponseError(
                    "Supabase returned an invalid priority-context row.",
                )

            rows.append(
                item,
            )

        return rows