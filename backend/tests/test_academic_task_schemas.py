# File: /backend/tests/test_academic_task_schemas.py
# Purpose: Verifies academic-task request and response validation.

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.academic_task import (
    AcademicTaskApiErrorResponse,
    AcademicTaskCreateRequest,
    AcademicTaskDifficulty,
    AcademicTaskListResponse,
    AcademicTaskOutputType,
    AcademicTaskResponse,
    AcademicTaskStatus,
    AcademicTaskStatusUpdateRequest,
    AcademicTaskType,
    AcademicTaskUpdateRequest,
)

TASK_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)

SUBJECT_ID = UUID(
    "22222222-2222-4222-8222-222222222222"
)

DEADLINE = datetime(
    2026,
    8,
    20,
    12,
    0,
    tzinfo=UTC,
)

CREATED_AT = datetime(
    2026,
    8,
    9,
    12,
    0,
    tzinfo=UTC,
)

UPDATED_AT = datetime(
    2026,
    8,
    9,
    13,
    0,
    tzinfo=UTC,
)


def create_request_payload() -> dict[str, object]:
    """Return one valid academic-task creation payload."""

    return {
        "subject_id": SUBJECT_ID,
        "title": "Research assignment",
        "description": "Complete the first draft.",
        "deadline": DEADLINE,
        "estimated_minutes": 120,
        "difficulty": "medium",
        "task_type": "assignment",
        "output_type": "writing",
    }


def response_payload() -> dict[str, object]:
    """Return one valid persisted academic-task payload."""

    return {
        "id": TASK_ID,
        "subject_id": SUBJECT_ID,
        "title": "Research assignment",
        "description": "Complete the first draft.",
        "deadline": DEADLINE,
        "estimated_minutes": 120,
        "difficulty": "medium",
        "task_type": "assignment",
        "output_type": "writing",
        "status": "pending",
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }


def test_academic_task_enum_values_match_database() -> None:
    """Backend enums must match the database constraints."""

    assert {
        item.value
        for item in AcademicTaskDifficulty
    } == {
        "easy",
        "medium",
        "hard",
    }

    assert {
        item.value
        for item in AcademicTaskType
    } == {
        "assignment",
        "project",
        "exam",
        "quiz",
        "reading",
        "presentation",
        "research",
        "other",
    }

    assert {
        item.value
        for item in AcademicTaskOutputType
    } == {
        "writing",
        "computation",
        "research",
        "presentation",
        "creative",
        "reading_analysis",
        "memorization",
        "mixed",
        "other",
    }

    assert {
        item.value
        for item in AcademicTaskStatus
    } == {
        "pending",
        "in_progress",
        "completed",
        "cancelled",
    }


def test_create_request_normalizes_text_and_defaults_status() -> None:
    """Creation should normalize text and default to pending."""

    payload = create_request_payload()

    payload["title"] = "  Research assignment  "
    payload["description"] = "  Complete the first draft.  "

    request = AcademicTaskCreateRequest(
        **payload,
    )

    assert request.title == "Research assignment"
    assert request.description == "Complete the first draft."
    assert request.status is AcademicTaskStatus.PENDING
    assert (
        request.output_type
        is AcademicTaskOutputType.WRITING
    )


def test_create_request_converts_blank_description_to_none() -> None:
    """Whitespace-only descriptions should behave as absent."""

    payload = create_request_payload()
    payload["description"] = "   "

    request = AcademicTaskCreateRequest(
        **payload,
    )

    assert request.description is None


def test_create_request_rejects_blank_title() -> None:
    """A task title cannot contain only whitespace."""

    payload = create_request_payload()
    payload["title"] = "   "

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskCreateRequest(
            **payload,
        )


def test_create_request_requires_output_type() -> None:
    """Creation must identify the academic output required."""

    payload = create_request_payload()
    payload.pop("output_type")

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskCreateRequest(
            **payload,
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        (
            "difficulty",
            "extreme",
        ),
        (
            "task_type",
            "homework123",
        ),
        (
            "output_type",
            "coding",
        ),
        (
            "status",
            "finished-ish",
        ),
    ],
)
def test_create_request_rejects_invalid_enum_values(
    field_name: str,
    invalid_value: str,
) -> None:
    """Unsupported enum values must be rejected."""

    payload = create_request_payload()
    payload[field_name] = invalid_value

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskCreateRequest(
            **payload,
        )


@pytest.mark.parametrize(
    "estimated_minutes",
    [
        0,
        10_081,
    ],
)
def test_create_request_rejects_invalid_duration(
    estimated_minutes: int,
) -> None:
    """Estimated workload must match database limits."""

    payload = create_request_payload()
    payload["estimated_minutes"] = estimated_minutes

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskCreateRequest(
            **payload,
        )


def test_create_request_rejects_naive_deadline() -> None:
    """Deadlines must include an explicit timezone."""

    payload = create_request_payload()

    payload["deadline"] = datetime(  # noqa: DTZ001
        2026,
        8,
        20,
        12,
        0,
    )

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskCreateRequest(
            **payload,
        )


def test_create_request_forbids_client_user_id() -> None:
    """Clients must not submit trusted task ownership."""

    payload = create_request_payload()

    payload["user_id"] = (
        "33333333-3333-4333-8333-333333333333"
    )

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskCreateRequest(
            **payload,
        )


def test_update_request_requires_at_least_one_field() -> None:
    """Empty PATCH-style requests must be rejected."""

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskUpdateRequest()


def test_update_request_normalizes_provided_fields() -> None:
    """Partial updates should normalize supplied text."""

    request = AcademicTaskUpdateRequest(
        title="  Revised title  ",
        description="  Revised details  ",
        status="in_progress",
    )

    assert request.title == "Revised title"
    assert request.description == "Revised details"
    assert (
        request.status
        is AcademicTaskStatus.IN_PROGRESS
    )


def test_update_request_accepts_output_type() -> None:
    """Partial updates should allow changing output type."""

    request = AcademicTaskUpdateRequest(
        output_type="research",
    )

    assert (
        request.output_type
        is AcademicTaskOutputType.RESEARCH
    )


def test_update_request_rejects_invalid_output_type() -> None:
    """Updates must reject unsupported output categories."""

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskUpdateRequest(
            output_type="coding",
        )


def test_update_request_can_clear_description() -> None:
    """Explicit blank description should clear the description."""

    request = AcademicTaskUpdateRequest(
        description="   ",
    )

    assert request.description is None
    assert "description" in request.model_fields_set


@pytest.mark.parametrize(
    "field_name",
    [
        "subject_id",
        "title",
        "deadline",
        "estimated_minutes",
        "difficulty",
        "task_type",
        "output_type",
        "status",
    ],
)
def test_update_request_rejects_explicit_null_for_required_fields(
    field_name: str,
) -> None:
    """Required persisted fields cannot be changed to null."""

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskUpdateRequest(
            **{
                field_name: None,
            },
        )


def test_response_validates_persisted_task() -> None:
    """A valid persisted database row should form a response."""

    response = AcademicTaskResponse(
        **response_payload(),
    )

    assert response.id == TASK_ID
    assert response.subject_id == SUBJECT_ID

    assert (
        response.status
        is AcademicTaskStatus.PENDING
    )

    assert (
        response.difficulty
        is AcademicTaskDifficulty.MEDIUM
    )

    assert (
        response.task_type
        is AcademicTaskType.ASSIGNMENT
    )

    assert (
        response.output_type
        is AcademicTaskOutputType.WRITING
    )


def test_response_requires_output_type() -> None:
    """Persisted task responses must contain an output type."""

    payload = response_payload()
    payload.pop("output_type")

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskResponse(
            **payload,
        )


def test_response_forbids_user_id() -> None:
    """The public task response should not expose ownership ID."""

    payload = response_payload()

    payload["user_id"] = (
        "33333333-3333-4333-8333-333333333333"
    )

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskResponse(
            **payload,
        )


def test_list_response_contains_validated_tasks() -> None:
    """Task-list responses should contain validated task objects."""

    task = AcademicTaskResponse(
        **response_payload(),
    )

    response = AcademicTaskListResponse(
        items=(
            task,
        ),
    )

    assert response.items == (
        task,
    )


def test_api_error_response_normalizes_text() -> None:
    """Controlled API errors should expose normalized safe text."""

    response = AcademicTaskApiErrorResponse(
        error_code="  ACADEMIC_TASK_NOT_FOUND  ",
        message="  The requested task was not found.  ",
    )

    assert (
        response.error_code
        == "ACADEMIC_TASK_NOT_FOUND"
    )

    assert (
        response.message
        == "The requested task was not found."
    )


def test_status_update_request_accepts_valid_status() -> None:
    """Dedicated status requests should accept task statuses."""

    request = AcademicTaskStatusUpdateRequest(
        status="completed",
    )

    assert (
        request.status
        is AcademicTaskStatus.COMPLETED
    )


def test_status_update_request_rejects_unknown_fields() -> None:
    """Status requests must not accept trusted ownership."""

    with pytest.raises(
        ValidationError,
    ):
        AcademicTaskStatusUpdateRequest(
            status="completed",
            user_id=(
                "33333333-3333-4333-8333-333333333333"
            ),
        )