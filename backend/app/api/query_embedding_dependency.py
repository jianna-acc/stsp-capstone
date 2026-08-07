# File: /backend/app/api/query_embedding_dependency.py
# Purpose: Constructs and safely closes the query-embedding
# service for future authenticated RAG API routes.

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.core.config import (
    Settings,
    get_settings,
)
from app.services.query_embedding import (
    QueryEmbeddingService,
)


async def get_query_embedding_service(
    settings: Annotated[
        Settings,
        Depends(
            get_settings,
        ),
    ],
) -> AsyncIterator[QueryEmbeddingService]:
    """Provide one query-embedding service per API request."""

    service = QueryEmbeddingService(
        settings=settings,
    )

    try:
        yield service
    finally:
        await service.aclose()