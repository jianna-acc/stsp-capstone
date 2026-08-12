# File: /backend/app/services/study_activity_service.py
# Purpose: Coordinates authenticated actual study-activity timer
# lifecycle operations.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.repositories.study_activity_repository import (
    StudyActivityStudySessionTarget,
)
from app.schemas.study_activity import (
    StudyActivityBreakStartRequest,
    StudyActivityResponse,
    StudyActivityStartRequest,
    StudyActivityTransitionAction,
)
from app.services.study_activity_errors import (
    StudyActivityConflictError,
    StudyActivityNotFoundError,
    StudyActivityValidationError,
)


class _StudyActivityRepository(
    Protocol,
):
    def get_active_activity(
        self,
        *,
        user_id: UUID,
    ) -> StudyActivityResponse | None: ...

    def subject_exists(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
    ) -> bool: ...

    def study_plan_exists(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> bool: ...

    def get_study_session_target(
        self,
        *,
        user_id: UUID,
        study_session_id: UUID,
    ) -> StudyActivityStudySessionTarget | None: ...

    def start_activity(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        title: str,
        study_plan_id: UUID | None,
        study_session_id: UUID | None,
    ) -> StudyActivityResponse: ...

    def start_break(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        duration_minutes: int,
    ) -> StudyActivityResponse: ...

    def transition_activity(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        action: StudyActivityTransitionAction,
    ) -> StudyActivityResponse: ...


class StudyActivityService:
    """Coordinates one student's actual study timer."""

    def __init__(
        self,
        repository: _StudyActivityRepository,
    ) -> None:
        self._repository = repository

    def get_active_activity(
        self,
        *,
        user_id: UUID,
    ) -> StudyActivityResponse | None:
        """Return the student's currently unfinished timer."""

        return self._repository.get_active_activity(
            user_id=user_id,
        )

    def start_activity(
        self,
        *,
        user_id: UUID,
        request: StudyActivityStartRequest,
    ) -> StudyActivityResponse:
        """Start a free-study timer or a scheduled-session timer."""

        current = (
            self._repository.get_active_activity(
                user_id=user_id,
            )
        )

        if current is not None:
            raise StudyActivityConflictError(
                "A study timer is already active.",
            )

        if request.study_session_id is not None:
            return self._start_from_study_session(
                user_id=user_id,
                request=request,
            )

        if request.subject_id is None:
            raise StudyActivityValidationError(
                "Free study activity requires a subject.",
            )

        if request.title is None:
            raise StudyActivityValidationError(
                "Free study activity requires a title.",
            )

        if not self._repository.subject_exists(
            user_id=user_id,
            subject_id=request.subject_id,
        ):
            raise StudyActivityNotFoundError(
                "The selected subject was not found.",
            )

        if (
            request.study_plan_id is not None
            and not self._repository.study_plan_exists(
                user_id=user_id,
                study_plan_id=request.study_plan_id,
            )
        ):
            raise StudyActivityNotFoundError(
                "The selected study plan was not found.",
            )

        return self._repository.start_activity(
            user_id=user_id,
            subject_id=request.subject_id,
            title=request.title,
            study_plan_id=request.study_plan_id,
            study_session_id=None,
        )

    def start_break(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        request: StudyActivityBreakStartRequest,
    ) -> StudyActivityResponse:
        """Start one persisted timed break."""

        return self._repository.start_break(
            user_id=user_id,
            activity_id=activity_id,
            duration_minutes=request.duration_minutes,
        )

    def transition_activity(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        action: StudyActivityTransitionAction,
    ) -> StudyActivityResponse:
        """Apply one atomic timer transition."""

        return self._repository.transition_activity(
            user_id=user_id,
            activity_id=activity_id,
            action=action,
        )

    def _start_from_study_session(
        self,
        *,
        user_id: UUID,
        request: StudyActivityStartRequest,
    ) -> StudyActivityResponse:
        """Resolve trusted timer metadata from one scheduled session."""

        study_session_id = request.study_session_id

        if study_session_id is None:
            raise StudyActivityValidationError(
                "Scheduled study activity requires a study session.",
            )

        target = (
            self._repository.get_study_session_target(
                user_id=user_id,
                study_session_id=study_session_id,
            )
        )

        if target is None:
            raise StudyActivityNotFoundError(
                "The selected study session was not found.",
            )

        if (
            request.subject_id is not None
            and request.subject_id
            != target.subject_id
        ):
            raise StudyActivityValidationError(
                "The selected subject does not match the study session.",
            )

        if (
            request.study_plan_id is not None
            and request.study_plan_id
            != target.study_plan_id
        ):
            raise StudyActivityValidationError(
                "The selected plan does not match the study session.",
            )

        if (
            request.title is not None
            and request.title
            != target.title
        ):
            raise StudyActivityValidationError(
                "The timer title does not match the study session.",
            )

        return self._repository.start_activity(
            user_id=user_id,
            subject_id=target.subject_id,
            title=target.title,
            study_plan_id=target.study_plan_id,
            study_session_id=target.id,
        )