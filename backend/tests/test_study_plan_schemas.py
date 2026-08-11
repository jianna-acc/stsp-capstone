# File: /backend/tests/test_study_plan_schemas.py
# Purpose: Verifies validation and normalization for Track D
# study-plan and study-session schemas.

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudySessionCreateRequest,
)


def test_study_plan_create_normalizes_title() -> None:
    """Manual study-plan titles should be trimmed."""

    request = StudyPlanCreateRequest(
        title="  Finals Review  ",
        starts_on=date(
            2026,
            8,
            10,
        ),
        ends_on=date(
            2026,
            8,
            17,
        ),
    )

    assert request.title == "Finals Review"


def test_study_plan_rejects_reversed_dates() -> None:
    """A plan cannot end before it begins."""

    with pytest.raises(
        ValidationError,
    ):
        StudyPlanCreateRequest(
            title="Finals Review",
            starts_on=date(
                2026,
                8,
                20,
            ),
            ends_on=date(
                2026,
                8,
                10,
            ),
        )


def test_study_plan_rejects_excessive_range() -> None:
    """A plan cannot span more than 366 days."""

    with pytest.raises(
        ValidationError,
    ):
        StudyPlanCreateRequest(
            title="Long Plan",
            starts_on=date(
                2026,
                1,
                1,
            ),
            ends_on=date(
                2027,
                1,
                3,
            ),
        )


def test_study_session_normalizes_text() -> None:
    """Session text should be normalized before persistence."""

    starts_at = datetime(
        2026,
        8,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    request = StudySessionCreateRequest(
        subject_id=uuid4(),
        title="  Read Chapter 4  ",
        starts_at=starts_at,
        ends_at=(
            starts_at
            + timedelta(
                minutes=60,
            )
        ),
        notes="  Focus on definitions.  ",
    )

    assert request.title == "Read Chapter 4"
    assert request.notes == "Focus on definitions."


def test_study_session_converts_blank_notes_to_none() -> None:
    """Blank optional notes should not be persisted."""

    starts_at = datetime(
        2026,
        8,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    request = StudySessionCreateRequest(
        subject_id=uuid4(),
        title="Read Chapter 4",
        starts_at=starts_at,
        ends_at=(
            starts_at
            + timedelta(
                minutes=60,
            )
        ),
        notes="   ",
    )

    assert request.notes is None


def test_study_session_requires_timezone() -> None:
    """Scheduling timestamps must be timezone-aware."""

    aware_starts_at = datetime(
        2026,
        8,
        10,
        18,
        0,
        tzinfo=timezone.utc,
    )

    starts_at = aware_starts_at.replace(
        tzinfo=None,
    )

    with pytest.raises(
        ValidationError,
    ):
        StudySessionCreateRequest(
            subject_id=uuid4(),
            title="Practice Problems",
            starts_at=starts_at,
            ends_at=(
                starts_at
                + timedelta(
                    minutes=60,
                )
            ),
        )

def test_study_session_rejects_reversed_times() -> None:
    """A session cannot finish before it starts."""

    starts_at = datetime(
        2026,
        8,
        10,
        18,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValidationError,
    ):
        StudySessionCreateRequest(
            subject_id=uuid4(),
            title="Practice Problems",
            starts_at=starts_at,
            ends_at=(
                starts_at
                - timedelta(
                    minutes=30,
                )
            ),
        )


def test_study_session_rejects_more_than_eight_hours() -> None:
    """One study session has a defensive eight-hour maximum."""

    starts_at = datetime(
        2026,
        8,
        10,
        8,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValidationError,
    ):
        StudySessionCreateRequest(
            subject_id=uuid4(),
            title="Marathon Session",
            starts_at=starts_at,
            ends_at=(
                starts_at
                + timedelta(
                    hours=9,
                )
            ),
        )