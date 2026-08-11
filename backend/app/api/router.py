# File: /backend/app/api/router.py
# Purpose: Combines all backend API route modules.

from fastapi import APIRouter

from app.api.health import (
    router as health_router,
)
from app.api.routes import (
    quiz_attempts,
    quizzes,
    rag,
    reviewers,
    study_conversations,
)
from app.api.routes.academic_tasks import (
    router as academic_tasks_router,
)
from app.api.routes.file_processing import (
    router as file_processing_router,
)
from app.api.routes.flashcards import (
    router as flashcard_router,
)

api_router = APIRouter()

api_router.include_router(
    health_router,
)

api_router.include_router(
    file_processing_router,
)

api_router.include_router(
    rag.router,
)

api_router.include_router(
    study_conversations.router,
)

api_router.include_router(
    reviewers.router,
)

api_router.include_router(
    flashcard_router,
)

api_router.include_router(
    quizzes.router,
)

api_router.include_router(
    quiz_attempts.router,
)

api_router.include_router(
    academic_tasks_router,
)