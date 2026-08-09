# File: /backend/app/services/study_plan_service.py
# Purpose: Coordinates ownership-aware study-plan and manual
# study-session operations for authenticated students.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanListResponse,
    StudyPlanResponse,
    StudySessionCreateRequest,
    StudySessionListResponse,
    StudySessionResponse,
)
from app.services.study_plan_errors import (
    StudyPlanNotFoundError,
    StudyPlanValidationError,
    StudySessionNotFoundError,
)


class _StudyPlanRepository(
    Protocol,
):
    def create_study_plan(
        self,
        *,
        user_id: UUID,
        request: StudyPlanCreateRequest,
    ) -> StudyPlanResponse: ...

    def list_study_plans(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> list[
        StudyPlanResponse
    ]: ...

    def get_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> StudyPlanResponse | None: ...

    def delete_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> bool: ...

    def create_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request: StudySessionCreateRequest,
    ) -> StudySessionResponse: ...

    def list_study_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        limit: int = 200,
    ) -> list[
        StudySessionResponse
    ]: ...

    def delete_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        study_session_id: UUID,
    ) -> bool: ...


class StudyPlanService:
    """Coordinates study-plan operations for one student."""

    def __init__(
        self,
        repository: _StudyPlanRepository,
    ) -> None:
        self._repository = repository

    def create_study_plan(
        self,
        *,
        user_id: UUID,
        request: StudyPlanCreateRequest,
    ) -> StudyPlanResponse:
        """Create one manual study plan."""

        return self._repository.create_study_plan(
            user_id=user_id,
            request=request,
        )

    def list_study_plans(
        self,
        *,
        user_id: UUID,
        limit: int = 50,
    ) -> StudyPlanListResponse:
        """Return study plans belonging to the student."""

        plans = (
            self._repository.list_study_plans(
                user_id=user_id,
                limit=limit,
            )
        )

        return StudyPlanListResponse(
            items=tuple(
                plans,
            ),
        )

    def get_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> StudyPlanResponse:
        """Return one owned study plan."""

        plan = (
            self._repository.get_study_plan(
                user_id=user_id,
                study_plan_id=study_plan_id,
            )
        )

        if plan is None:
            raise StudyPlanNotFoundError(
                "The requested study plan "
                "was not found.",
            )

        return plan

    def delete_study_plan(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
    ) -> None:
        """Delete one study plan owned by the student."""

        deleted = (
            self._repository.delete_study_plan(
                user_id=user_id,
                study_plan_id=study_plan_id,
            )
        )

        if not deleted:
            raise StudyPlanNotFoundError(
                "The requested study plan "
                "was not found.",
            )

    def create_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request: StudySessionCreateRequest,
    ) -> StudySessionResponse:
        """Add one manual session to an owned study plan."""

        plan = self.get_study_plan(
            user_id=user_id,
            study_plan_id=study_plan_id,
        )

        session_start_date = (
            request.starts_at.date()
        )

        session_end_date = (
            request.ends_at.date()
        )

        if (
            session_start_date
            < plan.starts_on
            or session_end_date
            > plan.ends_on
        ):
            raise StudyPlanValidationError(
                "Study sessions must fall within "
                "the study-plan date range.",
            )

        return (
            self._repository.create_study_session(
                user_id=user_id,
                study_plan_id=study_plan_id,
                request=request,
            )
        )

    def list_study_sessions(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        limit: int = 200,
    ) -> StudySessionListResponse:
        """Return sessions from one owned study plan."""

        self.get_study_plan(
            user_id=user_id,
            study_plan_id=study_plan_id,
        )

        sessions = (
            self._repository.list_study_sessions(
                user_id=user_id,
                study_plan_id=study_plan_id,
                limit=limit,
            )
        )

        return StudySessionListResponse(
            items=tuple(
                sessions,
            ),
        )

    def delete_study_session(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        study_session_id: UUID,
    ) -> None:
        """Delete one session from an owned study plan."""

        self.get_study_plan(
            user_id=user_id,
            study_plan_id=study_plan_id,
        )

        deleted = (
            self._repository.delete_study_session(
                user_id=user_id,
                study_plan_id=study_plan_id,
                study_session_id=study_session_id,
            )
        )

        if not deleted:
            raise StudySessionNotFoundError(
                "The requested study session "
                "was not found.",
            )