# File: /backend/app/api/retrieval_orchestration_dependency.py
# Purpose: Constructs the retrieval-orchestration service for
# future protected FastAPI RAG routes.

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.ai.retrieval_persistence import (
    SupabaseRetrievalPersistence,
)
from app.api.query_embedding_dependency import (
    get_query_embedding_service,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.services.query_embedding import (
    QueryEmbeddingService,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationService,
)
from app.services.supabase_admin import (
    SupabaseAdminService,
)


def get_retrieval_orchestration_service(
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
    query_embedding_service: Annotated[
        QueryEmbeddingService,
        Depends(get_query_embedding_service),
    ],
) -> RetrievalOrchestrationService:
    """Construct retrieval orchestration for one API request."""

    admin_service = SupabaseAdminService(
        settings=settings,
    )

    retrieval_persistence = SupabaseRetrievalPersistence(
        client=admin_service,
    )

    return RetrievalOrchestrationService(
        query_embedding_service=query_embedding_service,
        retrieval_persistence=retrieval_persistence,
    )