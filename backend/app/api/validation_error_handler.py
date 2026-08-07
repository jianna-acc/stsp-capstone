# File: /backend/app/api/validation_error_handler.py

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def handle_request_validation_error(
    _request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Return validation errors without echoing request values."""

    safe_details: list[
        dict[str, object]
    ] = []

    for validation_error in error.errors():
        safe_details.append(
            {
                "type": validation_error.get(
                    "type",
                    "value_error",
                ),
                "loc": list(
                    validation_error.get(
                        "loc",
                        (),
                    )
                ),
                "msg": validation_error.get(
                    "msg",
                    "The request is invalid.",
                ),
            }
        )

    return JSONResponse(
        status_code=(
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ),
        content={
            "detail": safe_details,
        },
    )