# File: /backend/app/api/routes/file_processing.py
# Purpose: Exposes protected internal endpoints for validating
# and processing student learning-material files.

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.core.config import (
    Settings,
    get_settings,
)
from app.core.security import (
    require_processor_key,
)
from app.schemas.file_processing import (
    FileProcessingResponse,
    FileSourceValidationResponse,
)
from app.services.file_processor import (
    FileProcessorConflictError,
    FileProcessorError,
    FileProcessorExtractionError,
    FileProcessorNotFoundError,
    FileProcessorService,
    FileProcessorTooLargeError,
    FileProcessorUpstreamError,
)

router = APIRouter(
    prefix="/internal/file-processing",
    tags=[
        "File Processing",
    ],
    dependencies=[
        Depends(require_processor_key),
    ],
)


def raise_processor_http_error(
    error: FileProcessorError,
) -> NoReturn:
    """Convert a service-layer error into an HTTP response."""

    if isinstance(
        error,
        FileProcessorNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        FileProcessorConflictError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        FileProcessorTooLargeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        FileProcessorExtractionError,
    ):
        raise HTTPException(
            status_code=(status.HTTP_422_UNPROCESSABLE_CONTENT),
            detail=str(error),
        ) from error

    if isinstance(
        error,
        FileProcessorUpstreamError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="The file-processing request failed.",
    ) from error


@router.post(
    "/{file_id}/validate-source",
    response_model=FileSourceValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_file_source(
    file_id: UUID,
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> FileSourceValidationResponse:
    """Validate that a queued private file is available."""

    processor = FileProcessorService(
        settings=settings,
    )

    try:
        result = await processor.validate_source(
            file_id=file_id,
        )
    except FileProcessorError as error:
        raise_processor_http_error(
            error,
        )

    return FileSourceValidationResponse(
        study_file_id=result.study_file_id,
        processing_job_id=(result.processing_job_id),
        filename=result.filename,
        mime_type=result.mime_type,
        expected_size_bytes=(result.expected_size_bytes),
        downloaded_size_bytes=(result.downloaded_size_bytes),
        processing_status=(result.processing_status),
        job_status=result.job_status,
        source_available=True,
    )


@router.post(
    "/{file_id}/process",
    response_model=FileProcessingResponse,
    status_code=status.HTTP_200_OK,
)
async def process_file(
    file_id: UUID,
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> FileProcessingResponse:
    """Process one queued or already claimed study file."""

    processor = FileProcessorService(
        settings=settings,
    )

    try:
        result = await processor.process_file(
            file_id=file_id,
        )
    except FileProcessorError as error:
        raise_processor_http_error(
            error,
        )

    return FileProcessingResponse(
        study_file_id=result.study_file_id,
        processing_job_id=(result.processing_job_id),
        filename=result.filename,
        mime_type=result.mime_type,
        character_count=result.character_count,
        chunk_count=result.chunk_count,
        page_count=result.page_count,
        slide_count=result.slide_count,
        sheet_count=result.sheet_count,
        processing_status=(result.processing_status),
        job_status=result.job_status,
    )
