# File: /backend/app/main.py
# Purpose: Creates the FastAPI application, configures shared
# middleware, and registers the main API router.

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.validation_error_handler import (
    handle_request_validation_error,
)
from app.core.config import get_settings
from app.workers.file_processing_worker import FileProcessingWorker

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop the file-processing worker with FastAPI."""

    if not settings.file_processing_worker_enabled:
        yield
        return

    stop_event = asyncio.Event()

    worker = FileProcessingWorker(
        settings=settings,
    )

    worker_task = asyncio.create_task(
        worker.run_forever(
            stop_event=stop_event,
        )
    )

    try:
        yield
    finally:
        stop_event.set()
        await worker_task

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for the STS Capstone Project's "
        "study-management and AI-learning features."
    ),
    lifespan=lifespan,
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
