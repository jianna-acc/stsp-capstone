# File: /backend/tests/test_reviewer_service.py
# Purpose: Verifies ownership-aware reviewer service
# persistence, listing, retrieval, and deletion behavior.

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerDefinition,
    ReviewerLength,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
    ReviewerTopic,
)
from app.services.reviewer_errors import (
    ReviewerNotFoundError,
)
from app.services.reviewer_service import (
    ReviewerService,
)


def _content() -> ReviewerContent:
    """Return valid generated reviewer content."""

    return ReviewerContent(
        overview="Material overview",
        topics=(
            ReviewerTopic(
                title="Topic One",
                summary="Topic summary",
                key_points=(
                    "Key point one",
                ),
                definitions=(
                    ReviewerDefinition(
                        term="Term",
                        definition="Definition",
                    ),
                ),
            ),
        ),
    )


def _source(
    study_file_id: UUID,
) -> ReviewerSource:
    """Return one valid reviewer source."""

    return ReviewerSource(
        study_file_id=study_file_id,
        source_name="Lecture.pdf",
        chunk_index=0,
        locator_type="page",
        locator_label="Page 1",
    )


def _reviewer(
    *,
    reviewer_id: UUID | None = None,
    subject_id: UUID | None = None,
    study_file_id: UUID | None = None,
) -> ReviewerResponse:
    """Return one valid saved reviewer."""

    resolved_file_id = (
        study_file_id
        if study_file_id is not None
        else uuid4()
    )

    now = datetime.now(
        UTC,
    )

    return ReviewerResponse(
        id=(
            reviewer_id
            if reviewer_id is not None
            else uuid4()
        ),
        subject_id=(
            subject_id
            if subject_id is not None
            else uuid4()
        ),
        study_file_id=resolved_file_id,
        scope_type=ReviewerScopeType.FILE,
        title="Generated Reviewer",
        reviewer_length=ReviewerLength.MEDIUM,
        content=_content(),
        sources=(
            _source(
                resolved_file_id,
            ),
        ),
        generation_model="gemini-3.6-flash",
        generation_count=1,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


class FakeReviewerRepository:
    """Minimal repository used by reviewer service tests."""

    def __init__(
        self,
    ) -> None:
        self.created: ReviewerResponse | None = None

        self.reviewers: list[
            ReviewerResponse
        ] = []

        self.reviewer_by_id: dict[
            UUID,
            ReviewerResponse
        ] = {}

        self.deleted_ids: set[
            UUID
        ] = set()

        self.create_arguments: dict[
            str,
            object,
        ] | None = None

        self.list_user_id: UUID | None = None
        self.list_limit: int | None = None

        self.get_user_id: UUID | None = None
        self.get_reviewer_id: UUID | None = None

        self.delete_user_id: UUID | None = None
        self.delete_reviewer_id: UUID | None = None

    def create_reviewer(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: ReviewerScopeType,
        title: str,
        reviewer_length: ReviewerLength,
        content: ReviewerContent,
        sources: Sequence[
            ReviewerSource,
        ],
        generation_model: str,
    ) -> ReviewerResponse:
        self.create_arguments = {
            "user_id": user_id,
            "subject_id": subject_id,
            "study_file_id": study_file_id,
            "scope_type": scope_type,
            "title": title,
            "reviewer_length": reviewer_length,
            "content": content,
            "sources": tuple(
                sources,
            ),
            "generation_model": generation_model,
        }

        reviewer = _reviewer(
            subject_id=subject_id,
            study_file_id=study_file_id,
        )

        self.created = reviewer

        return reviewer

    def list_reviewers(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> list[
        ReviewerResponse
    ]:
        self.list_user_id = user_id
        self.list_limit = limit

        return list(
            self.reviewers,
        )

    def get_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse | None:
        self.get_user_id = user_id
        self.get_reviewer_id = reviewer_id

        return self.reviewer_by_id.get(
            reviewer_id,
        )

    def delete_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> bool:
        self.delete_user_id = user_id
        self.delete_reviewer_id = reviewer_id

        if reviewer_id not in self.reviewer_by_id:
            return False

        self.deleted_ids.add(
            reviewer_id,
        )

        return True


def test_save_generated_reviewer_delegates_to_repository() -> None:
    """Generated content must be persisted through the repository."""

    repository = FakeReviewerRepository()
    service = ReviewerService(
        repository,
    )

    user_id = uuid4()
    subject_id = uuid4()
    study_file_id = uuid4()

    content = _content()

    sources = (
        _source(
            study_file_id,
        ),
    )

    result = service.save_generated_reviewer(
        user_id=user_id,
        subject_id=subject_id,
        study_file_id=study_file_id,
        scope_type=ReviewerScopeType.FILE,
        title="Generated Reviewer",
        reviewer_length=ReviewerLength.MEDIUM,
        content=content,
        sources=sources,
        generation_model="gemini-3.6-flash",
    )

    assert result.subject_id == subject_id
    assert result.study_file_id == study_file_id

    assert repository.create_arguments is not None

    assert (
        repository.create_arguments[
            "user_id"
        ]
        == user_id
    )

    assert (
        repository.create_arguments[
            "reviewer_length"
        ]
        == ReviewerLength.MEDIUM
    )


def test_list_reviewers_preserves_owner_and_limit() -> None:
    """Reviewer list requests must remain user scoped."""

    repository = FakeReviewerRepository()

    repository.reviewers = [
        _reviewer(),
        _reviewer(),
    ]

    service = ReviewerService(
        repository,
    )

    user_id = uuid4()

    result = service.list_reviewers(
        user_id=user_id,
        limit=20,
    )

    assert len(
        result.items,
    ) == 2

    assert repository.list_user_id == user_id
    assert repository.list_limit == 20


def test_get_reviewer_returns_owned_reviewer() -> None:
    """Existing reviewer must be returned."""

    repository = FakeReviewerRepository()
    service = ReviewerService(
        repository,
    )

    user_id = uuid4()
    reviewer_id = uuid4()

    saved = _reviewer(
        reviewer_id=reviewer_id,
    )

    repository.reviewer_by_id[
        reviewer_id
    ] = saved

    result = service.get_reviewer(
        user_id=user_id,
        reviewer_id=reviewer_id,
    )

    assert result.id == reviewer_id
    assert repository.get_user_id == user_id


def test_get_missing_reviewer_raises_not_found() -> None:
    """Missing reviewer must become a controlled error."""

    service = ReviewerService(
        FakeReviewerRepository(),
    )

    with pytest.raises(
        ReviewerNotFoundError,
    ):
        service.get_reviewer(
            user_id=uuid4(),
            reviewer_id=uuid4(),
        )


def test_delete_existing_reviewer_succeeds() -> None:
    """Existing owned reviewer must be deletable."""

    repository = FakeReviewerRepository()
    service = ReviewerService(
        repository,
    )

    user_id = uuid4()
    reviewer_id = uuid4()

    repository.reviewer_by_id[
        reviewer_id
    ] = _reviewer(
        reviewer_id=reviewer_id,
    )

    service.delete_reviewer(
        user_id=user_id,
        reviewer_id=reviewer_id,
    )

    assert reviewer_id in repository.deleted_ids
    assert repository.delete_user_id == user_id


def test_delete_missing_reviewer_raises_not_found() -> None:
    """Missing reviewer deletion must fail safely."""

    service = ReviewerService(
        FakeReviewerRepository(),
    )

    with pytest.raises(
        ReviewerNotFoundError,
    ):
        service.delete_reviewer(
            user_id=uuid4(),
            reviewer_id=uuid4(),
        )