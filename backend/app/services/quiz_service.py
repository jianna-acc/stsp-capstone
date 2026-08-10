# File: /backend/app/services/quiz_service.py
# Purpose: Coordinates ownership-aware Quiz persistence,
# retrieval, listing, and deletion operations.

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.schemas.quiz import (
    QuizDifficulty,
    QuizGeneratedContent,
    QuizListResponse,
    QuizResponse,
    QuizScopeType,
    QuizSummaryResponse,
    QuizType,
)
from app.services.quiz_errors import (
    QuizNotFoundError,
)


class _QuizRepository(
    Protocol,
):
    """Persistence operations required by QuizService."""

    def create_quiz(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: QuizScopeType,
        quiz_type: QuizType,
        difficulty: QuizDifficulty,
        question_count: int,
        content: QuizGeneratedContent,
        generation_model: str,
    ) -> QuizResponse: ...

    def list_quizzes(
        self,
        *,
        user_id: UUID,
    ) -> tuple[
        QuizSummaryResponse,
        ...,
    ]: ...

    def get_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizResponse | None: ...

    def delete_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> bool: ...


class QuizService:
    """Coordinates saved Quiz operations for one student."""

    def __init__(
        self,
        repository: _QuizRepository,
    ) -> None:
        self._repository = repository

    def save_generated_quiz(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: QuizScopeType,
        quiz_type: QuizType,
        difficulty: QuizDifficulty,
        question_count: int,
        content: QuizGeneratedContent,
        generation_model: str,
    ) -> QuizResponse:
        """Persist one successfully generated Quiz."""

        return self._repository.create_quiz(
            user_id=user_id,
            subject_id=subject_id,
            study_file_id=study_file_id,
            scope_type=scope_type,
            quiz_type=quiz_type,
            difficulty=difficulty,
            question_count=question_count,
            content=content,
            generation_model=generation_model,
        )

    def list_quizzes(
        self,
        *,
        user_id: UUID,
    ) -> QuizListResponse:
        """Return saved Quizzes owned by the student."""

        return QuizListResponse(
            items=self._repository.list_quizzes(
                user_id=user_id,
            ),
        )

    def get_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> QuizResponse:
        """Return one Quiz owned by the student."""

        quiz = self._repository.get_quiz(
            user_id=user_id,
            quiz_id=quiz_id,
        )

        if quiz is None:
            raise QuizNotFoundError(
                "The requested Quiz was not found.",
            )

        return quiz

    def delete_quiz(
        self,
        *,
        user_id: UUID,
        quiz_id: UUID,
    ) -> None:
        """Delete one Quiz owned by the student."""

        deleted = self._repository.delete_quiz(
            user_id=user_id,
            quiz_id=quiz_id,
        )

        if not deleted:
            raise QuizNotFoundError(
                "The requested Quiz was not found.",
            )