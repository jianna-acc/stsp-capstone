# File: /backend/tests/test_study_schedule_generation_dependency.py
# Purpose: Verifies the independent Track D generation dependency
# can be constructed without shared-router registration.

from app.api.study_schedule_generation_dependency import (
    get_study_schedule_generation_service,
)
from app.services.study_schedule_generation_service import (
    StudyScheduleGenerationService,
)


class FakeSupabaseClient:
    """Minimal stand-in for dependency construction."""


def test_dependency_builds_generation_service() -> None:
    """The dependency should construct Track D orchestration."""

    service = (
        get_study_schedule_generation_service(
            FakeSupabaseClient(),
        )
    )

    assert isinstance(
        service,
        StudyScheduleGenerationService,
    )