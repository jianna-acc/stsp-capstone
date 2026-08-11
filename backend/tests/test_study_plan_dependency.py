# File: /backend/tests/test_study_plan_dependency.py
# Purpose: Verifies the Track D FastAPI dependency builds the
# study-plan persistence service without shared-router registration.

from app.api.study_plan_dependency import (
    get_study_plan_service,
)
from app.services.study_plan_service import (
    StudyPlanService,
)


class FakeSupabaseClient:
    """Minimal stand-in for dependency construction."""


def test_dependency_builds_study_plan_service() -> None:
    """The dependency should construct the Track D service."""

    service = get_study_plan_service(
        FakeSupabaseClient(),
    )

    assert isinstance(
        service,
        StudyPlanService,
    )