# File: /backend/app/services/academic_task_priority_context.py
# Purpose: Resolves student output confidence and recurring study
# availability into inputs used by academic-task priority scoring.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from datetime import (
    UTC,
    datetime,
    time,
    timedelta,
)
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from app.schemas.academic_task import (
    AcademicTaskOutputType,
)

_CONFIDENCE_OUTPUT_TYPES = (
    AcademicTaskOutputType.WRITING,
    AcademicTaskOutputType.COMPUTATION,
    AcademicTaskOutputType.RESEARCH,
    AcademicTaskOutputType.PRESENTATION,
    AcademicTaskOutputType.CREATIVE,
    AcademicTaskOutputType.READING_ANALYSIS,
    AcademicTaskOutputType.MEMORIZATION,
)


@dataclass(
    frozen=True,
    slots=True,
)
class StudyAvailabilitySlot:
    """One recurring weekly student study period."""

    day_of_week: int
    start_time: time
    end_time: time


def _validate_aware_datetime(
    value: datetime,
    *,
    field_name: str,
) -> None:
    """Require a timezone-aware datetime."""

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"{field_name} must include a timezone."
        )


def _validate_confidence_level(
    value: int,
) -> None:
    """Validate one persisted output-confidence rating."""

    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
        or not 1 <= value <= 5
    ):
        raise ValueError(
            "Output confidence levels must be between 1 and 5."
        )


def resolve_output_confidence(
    *,
    output_type: AcademicTaskOutputType,
    confidence_levels: Mapping[
        str,
        int,
    ],
) -> float | None:
    """Resolve confidence appropriate to one task output type."""

    if (
        output_type
        is AcademicTaskOutputType.OTHER
    ):
        return None

    if (
        output_type
        is AcademicTaskOutputType.MIXED
    ):
        mixed_levels: list[
            int
        ] = []

        for supported_type in (
            _CONFIDENCE_OUTPUT_TYPES
        ):
            level = (
                confidence_levels.get(
                    supported_type.value,
                )
            )

            if level is None:
                return None

            _validate_confidence_level(
                level,
            )

            mixed_levels.append(
                level,
            )

        return (
            sum(
                mixed_levels,
            )
            / len(
                mixed_levels,
            )
        )

    confidence_level = (
        confidence_levels.get(
            output_type.value,
        )
    )

    if confidence_level is None:
        return None

    _validate_confidence_level(
        confidence_level,
    )

    return float(
        confidence_level,
    )


def _validate_availability_slots(
    slots: Sequence[
        StudyAvailabilitySlot
    ],
) -> None:
    """Validate recurring availability before calculation."""

    ordered_slots = sorted(
        slots,
        key=lambda slot: (
            slot.day_of_week,
            slot.start_time,
            slot.end_time,
        ),
    )

    previous_slot: StudyAvailabilitySlot | None = None

    for slot in ordered_slots:
        if not 1 <= slot.day_of_week <= 7:
            raise ValueError(
                "day_of_week must be between 1 and 7."
            )

        if (
            slot.start_time.tzinfo
            is not None
            or slot.end_time.tzinfo
            is not None
        ):
            raise ValueError(
                "Study availability times must not "
                "contain timezone information."
            )

        if (
            slot.start_time
            >= slot.end_time
        ):
            raise ValueError(
                "Study availability start_time "
                "must be earlier than end_time."
            )

        if (
            previous_slot is not None
            and previous_slot.day_of_week
            == slot.day_of_week
            and slot.start_time
            < previous_slot.end_time
        ):
            raise ValueError(
                "Study availability periods "
                "must not overlap."
            )

        previous_slot = slot


def _load_timezone(
    timezone_name: str,
) -> ZoneInfo:
    """Load a student's validated IANA timezone."""

    normalized_name = (
        timezone_name.strip()
    )

    if not normalized_name:
        raise ValueError(
            "timezone_name must not be empty."
        )

    try:
        return ZoneInfo(
            normalized_name,
        )

    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            "timezone_name must be a valid IANA timezone."
        ) from exc


def calculate_available_study_minutes(
    *,
    slots: Sequence[
        StudyAvailabilitySlot
    ],
    now: datetime,
    deadline: datetime,
    timezone_name: str,
) -> int:
    """Count recurring available study minutes until deadline."""

    _validate_aware_datetime(
        now,
        field_name="now",
    )

    _validate_aware_datetime(
        deadline,
        field_name="deadline",
    )

    _validate_availability_slots(
        slots,
    )

    if deadline <= now:
        return 0

    timezone = _load_timezone(
        timezone_name,
    )

    local_now = now.astimezone(
        timezone,
    )

    local_deadline = (
        deadline.astimezone(
            timezone,
        )
    )

    current_date = (
        local_now.date()
    )

    final_date = (
        local_deadline.date()
    )

    available_seconds = 0.0

    while (
        current_date
        <= final_date
    ):
        weekday = (
            current_date.isoweekday()
        )

        for slot in slots:
            if (
                slot.day_of_week
                != weekday
            ):
                continue

            slot_start = (
                datetime.combine(
                    current_date,
                    slot.start_time,
                    tzinfo=timezone,
                )
            )

            slot_end = (
                datetime.combine(
                    current_date,
                    slot.end_time,
                    tzinfo=timezone,
                )
            )

            overlap_start = max(
                slot_start,
                local_now,
            )

            overlap_end = min(
                slot_end,
                local_deadline,
            )

            if (
                overlap_end
                <= overlap_start
            ):
                continue

            available_seconds += (
                overlap_end.astimezone(
                    UTC,
                )
                - overlap_start.astimezone(
                    UTC,
                )
            ).total_seconds()

        current_date += timedelta(
            days=1,
        )

    return int(
        available_seconds
        // 60
    )