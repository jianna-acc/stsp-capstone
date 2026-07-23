# File: /backend/app/api/router.py
# Purpose: Combines all feature routers into one main API router.

from fastapi import APIRouter

from app.api.health import router as health_router


api_router = APIRouter()

api_router.include_router(health_router)