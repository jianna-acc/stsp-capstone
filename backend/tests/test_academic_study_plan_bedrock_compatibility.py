# File: /backend/tests/test_academic_study_plan_bedrock_compatibility.py
#
# Purpose: Verifies that Academic Tasks and Study Plan scheduling
# remain provider-independent when Amazon Bedrock is configured.

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path
from typing import Any

import pytest

from app.core.config import Settings
from app.schemas.academic_task import (
    AcademicTaskDifficulty,
    AcademicTaskStatus,
)
from app.services.academic_task_priority import (
    AcademicTaskPriorityInput,
    calculate_academic_task_priority,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]

PROVIDER_INDEPENDENT_FILES = (
    "app/api/academic_task_priority_dependency.py",
    "app/api/study_plan_generation_dependency.py",
    "app/services/academic_task_priority.py",
    "app/services/academic_task_priority_service.py",
    "app/services/study_schedule_generation_service.py",
    "app/services/study_scheduler.py",
    "app/services/study_plan_generation_orchestrator.py",
    "app/services/study_plan_regeneration_orchestrator.py",
)


def build_settings(
    **overrides: Any,
) -> Settings:
    """Create isolated settings without loading the private .env."""

    values: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_secret_key": "sb_secret_test_value",
        "processor_internal_key": "x" * 32,
        "_env_file": None,
    }

    values.update(overrides)

    return Settings(
        **values,
    )


def test_academic_task_priority_works_with_bedrock_configured() -> None:
    """Task priority must remain deterministic under Bedrock config."""

    settings = build_settings(
        ai_provider="bedrock",
    )

    now = datetime(
        2026,
        8,
        12,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = calculate_academic_task_priority(
        AcademicTaskPriorityInput(
            deadline=(
                now
                + timedelta(
                    days=3,
                )
            ),
            estimated_minutes=120,
            difficulty=AcademicTaskDifficulty.MEDIUM,
            status=AcademicTaskStatus.PENDING,
        ),
        now=now,
    )

    assert settings.ai_provider == "bedrock"
    assert result.total_score > 0


@pytest.mark.parametrize(
    "relative_path",
    PROVIDER_INDEPENDENT_FILES,
)
def test_academic_task_and_study_plan_paths_do_not_depend_on_ai_provider(
    relative_path: str,
) -> None:
    """Deterministic Academic Task/Study Plan code must not import AI."""

    source = (
        BACKEND_ROOT
        / relative_path
    ).read_text(
        encoding="utf-8",
    )

    forbidden_dependencies = (
        "app.ai",
        "GeminiProvider",
        "BedrockGenerationProvider",
        "create_generation_provider",
    )

    for dependency in forbidden_dependencies:
        assert dependency not in source