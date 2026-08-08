# File: /backend/tests/test_reviewer_schemas.py
# Purpose: Verifies reviewer request, content, source,
# and response validation contracts.

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerDefinition,
    ReviewerGenerateRequest,
    ReviewerLength,
    ReviewerLocatorType,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
    ReviewerTopic,
)


def _content() -> ReviewerContent:
    """Return valid structured reviewer content."""

    return ReviewerContent(
        overview="A concise overview of the material.",
        topics=(
            ReviewerTopic(
                title="Core Topic",
                summary="This topic explains the main concept.",
                key_points=(
                    "Important point one.",
                    "Important point two.",
                ),
                definitions=(
                    ReviewerDefinition(
                        term="Important term",
                        definition=(
                            "The meaning of the important term."
                        ),
                    ),
                ),
            ),
        ),
    )


def _source() -> ReviewerSource:
    """Return one valid reviewer source."""

    return ReviewerSource(
        study_file_id=uuid4(),
        source_name="Lecture 1.pdf",
        chunk_index=0,
        locator_type=ReviewerLocatorType.PAGE,
        locator_label="Page 1",
    )


def test_subject_reviewer_request_is_valid() -> None:
    """Subject generation must not require a file."""

    request = ReviewerGenerateRequest(
        scope_type=ReviewerScopeType.SUBJECT,
        subject_id=uuid4(),
        reviewer_length=ReviewerLength.SHORT,
    )

    assert request.study_file_id is None
    assert request.reviewer_length == ReviewerLength.SHORT


def test_file_reviewer_request_requires_file() -> None:
    """File generation must include study_file_id."""

    with pytest.raises(
        ValidationError,
    ):
        ReviewerGenerateRequest(
            scope_type=ReviewerScopeType.FILE,
            subject_id=uuid4(),
            reviewer_length=ReviewerLength.MEDIUM,
        )


def test_subject_reviewer_rejects_file_id() -> None:
    """Subject scope must not silently become file scope."""

    with pytest.raises(
        ValidationError,
    ):
        ReviewerGenerateRequest(
            scope_type=ReviewerScopeType.SUBJECT,
            subject_id=uuid4(),
            study_file_id=uuid4(),
        )


def test_reviewer_content_supports_required_features() -> None:
    """Content must contain topics, key points, and definitions."""

    content = _content()

    assert content.overview
    assert len(content.topics) == 1

    topic = content.topics[0]

    assert topic.title == "Core Topic"
    assert len(topic.key_points) == 2
    assert len(topic.definitions) == 1


def test_empty_key_point_is_rejected() -> None:
    """Generated key points must contain useful text."""

    with pytest.raises(
        ValidationError,
    ):
        ReviewerTopic(
            title="Topic",
            summary="Summary",
            key_points=(
                "Valid point",
                "   ",
            ),
        )


def test_source_supports_location_metadata() -> None:
    """Sources must preserve safe material-location details."""

    source = _source()

    assert source.source_name == "Lecture 1.pdf"
    assert source.chunk_index == 0
    assert source.locator_type == ReviewerLocatorType.PAGE
    assert source.locator_label == "Page 1"


def test_response_supports_saved_regenerated_reviewer() -> None:
    """Saved response must expose generation state and sources."""

    subject_id = uuid4()
    study_file_id = uuid4()
    now = datetime.now(
        UTC,
    )

    response = ReviewerResponse(
        id=uuid4(),
        subject_id=subject_id,
        study_file_id=study_file_id,
        scope_type=ReviewerScopeType.FILE,
        title="Financial Management Reviewer",
        reviewer_length=ReviewerLength.LONG,
        content=_content(),
        sources=(
            _source(),
        ),
        generation_model="gemini-3.6-flash",
        generation_count=2,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )

    assert response.scope_type == ReviewerScopeType.FILE
    assert response.generation_count == 2
    assert len(response.sources) == 1


def test_saved_subject_reviewer_rejects_file() -> None:
    """Saved subject reviewer must remain subject scoped."""

    now = datetime.now(
        UTC,
    )

    with pytest.raises(
        ValidationError,
    ):
        ReviewerResponse(
            id=uuid4(),
            subject_id=uuid4(),
            study_file_id=uuid4(),
            scope_type=ReviewerScopeType.SUBJECT,
            title="Subject Reviewer",
            reviewer_length=ReviewerLength.MEDIUM,
            content=_content(),
            sources=(),
            generation_model="gemini-3.6-flash",
            generation_count=1,
            generated_at=now,
            created_at=now,
            updated_at=now,
        )