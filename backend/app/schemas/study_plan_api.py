# File: /backend/app/schemas/study_plan_api.py
# Purpose: Defines safe public API error responses for Track D
# study-plan and scheduling endpoints.

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class StudyPlanApiErrorResponse(BaseModel):
    """Safe public error returned by study-plan endpoints."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    error_code: str = Field(
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        min_length=1,
        max_length=300,
    )