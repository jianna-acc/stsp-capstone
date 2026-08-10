# File: /backend/app/schemas/study_scheduler_context.py
# Purpose: Defines validated Track D scheduling context loaded
# from the student's existing onboarding preferences.

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.study_scheduler import (
    SchedulerAvailabilitySlot,
    SchedulerPreferences,
)


class StudySchedulerContext(BaseModel):
    """Existing student preferences required by the scheduler."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    preferences: SchedulerPreferences

    availability: tuple[
        SchedulerAvailabilitySlot,
        ...,
    ] = Field(
        min_length=1,
        max_length=30,
    )