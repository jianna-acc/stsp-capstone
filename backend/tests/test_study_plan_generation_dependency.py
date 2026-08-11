# File: /backend/tests/test_study_plan_generation_dependency.py
# Purpose: Verifies Track D generate-and-save orchestration can
# be constructed without modifying the shared API router.

from app.api.study_plan_generation_dependency import (
    get_study_plan_generation_orchestrator,
)
from app.services.study_plan_generation_orchestrator import (
    StudyPlanGenerationOrchestrator,
)


class FakeSupabaseClient:
    """Minimal stand-in for dependency construction."""


def test_dependency_builds_generation_orchestrator() -> None:
    """The dependency should build Track D orchestration."""

    orchestrator = (
        get_study_plan_generation_orchestrator(
            FakeSupabaseClient(),
        )
    )

    assert isinstance(
        orchestrator,
        StudyPlanGenerationOrchestrator,
    )