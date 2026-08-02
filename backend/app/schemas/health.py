# File: /backend/app/schemas/health.py
# Purpose: Defines the structured response returned by the health endpoint.

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned when the backend is operating normally."""

    status: Literal["healthy"]
    service: str
    version: str
    environment: str
