# File: /backend/app/api/health.py
# Purpose: Provides a public endpoint that reports whether the
# FastAPI backend is operating normally.

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check backend health",
    description=(
        "Returns basic service information when the FastAPI "
        "application is running correctly."
    ),
)
def get_health() -> HealthResponse:
    """Return the current backend health status."""

    settings = get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
