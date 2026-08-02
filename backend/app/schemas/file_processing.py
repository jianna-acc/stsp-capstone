# File: /backend/app/schemas/file_processing.py
# Purpose: Defines safe API responses for backend file processing.

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileSourceValidationResponse(BaseModel):
    """Result of validating a queued private file."""

    model_config = ConfigDict(
        extra="forbid",
    )

    study_file_id: UUID
    processing_job_id: UUID

    filename: str
    mime_type: str

    expected_size_bytes: int = Field(
        ge=0,
    )

    downloaded_size_bytes: int = Field(
        ge=0,
    )

    processing_status: str
    job_status: str

    source_available: bool = True


class FileProcessingResponse(BaseModel):
    """Result of extracting and storing a study file."""

    model_config = ConfigDict(
        extra="forbid",
    )

    study_file_id: UUID
    processing_job_id: UUID

    filename: str
    mime_type: str

    character_count: int = Field(
        ge=1,
    )

    chunk_count: int = Field(
        ge=1,
    )

    page_count: int | None = Field(
        default=None,
        ge=0,
    )

    slide_count: int | None = Field(
        default=None,
        ge=0,
    )

    sheet_count: int | None = Field(
        default=None,
        ge=0,
    )

    processing_status: str = "ready"
    job_status: str = "completed"
