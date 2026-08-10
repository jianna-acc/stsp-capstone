# File: /backend/app/schemas/academic_task_priority.py
# Purpose: Defines public API response contracts for explainable
# academic-task priority scores and prioritized task lists.

from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.academic_task import (
    AcademicTaskResponse,
)


class AcademicTaskPriorityBreakdownResponse(
    BaseModel,
):
    """Explainable deterministic priority score."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    total_score: float = Field(
        ge=0,
        le=100,
    )

    deadline_score: float = Field(
        ge=0,
        le=100,
    )

    difficulty_score: float = Field(
        ge=0,
        le=100,
    )

    estimated_time_score: float = Field(
        ge=0,
        le=100,
    )

    output_confidence_score: float = Field(
        ge=0,
        le=100,
    )

    previous_performance_score: float = Field(
        ge=0,
        le=100,
    )

    available_study_time_score: float = Field(
        ge=0,
        le=100,
    )

    status_score: float = Field(
        ge=0,
        le=100,
    )


class AcademicTaskPriorityResponse(
    BaseModel,
):
    """One academic task with its priority calculation."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    task: AcademicTaskResponse

    priority: AcademicTaskPriorityBreakdownResponse


class AcademicTaskPriorityListResponse(
    BaseModel,
):
    """Prioritized academic-task collection."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    items: tuple[
        AcademicTaskPriorityResponse,
        ...,
    ]