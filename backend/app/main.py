# File: /backend/app/main.py
# Purpose: Creates the FastAPI application, configures shared
# middleware, and registers the main API router.

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.validation_error_handler import (
    handle_request_validation_error,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for the STS Capstone Project's "
        "study-management and AI-learning features."
    ),
)

app.add_exception_handler(
    RequestValidationError,
    handle_request_validation_error,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.api_prefix,
)
