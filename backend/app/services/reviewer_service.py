# File: /backend/app/services/reviewer_service.py
# Purpose: Coordinates ownership-aware reviewer persistence,
# listing, retrieval, and deletion operations.

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.schemas.reviewer import (
    ReviewerContent,
    ReviewerLength,
    ReviewerListResponse,
    ReviewerResponse,
    ReviewerScopeType,
    ReviewerSource,
)
from app.services.reviewer_errors import (
    ReviewerNotFoundError,
)


class _ReviewerRepository(
    Protocol,
):
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
    ) -> ReviewerResponse: ...

    def list_reviewers(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> list[
        ReviewerResponse
    ]: ...

    def get_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse | None: ...

    def delete_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> bool: ...


class ReviewerService:
    """Coordinates reviewer operations for one student."""

    def __init__(
        self,
        repository: _ReviewerRepository,
    ) -> None:
        self._repository = repository

    def save_generated_reviewer(
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
        """Persist one successfully generated reviewer."""

        return self._repository.create_reviewer(
            user_id=user_id,
            subject_id=subject_id,
            study_file_id=study_file_id,
            scope_type=scope_type,
            title=title,
            reviewer_length=reviewer_length,
            content=content,
            sources=sources,
            generation_model=generation_model,
        )

    def list_reviewers(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> ReviewerListResponse:
        """Return recent reviewers belonging to the student."""

        reviewers = (
            self._repository.list_reviewers(
                user_id=user_id,
                limit=limit,
            )
        )

        return ReviewerListResponse(
            items=tuple(
                reviewers,
            ),
        )

    def get_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> ReviewerResponse:
        """Return one reviewer owned by the student."""

        reviewer = (
            self._repository.get_reviewer(
                user_id=user_id,
                reviewer_id=reviewer_id,
            )
        )

        if reviewer is None:
            raise ReviewerNotFoundError(
                "The requested reviewer was not found.",
            )

        return reviewer

    def delete_reviewer(
        self,
        *,
        user_id: UUID,
        reviewer_id: UUID,
    ) -> None:
        """Delete one reviewer owned by the student."""

        deleted = (
            self._repository.delete_reviewer(
                user_id=user_id,
                reviewer_id=reviewer_id,
            )
        )

        if not deleted:
            raise ReviewerNotFoundError(
                "The requested reviewer was not found.",
            )