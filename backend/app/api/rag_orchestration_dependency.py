# File: /backend/app/api/rag_orchestration_dependency.py

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.grounded_answer_generation_dependency import (
    get_grounded_answer_generation_service,
)
from app.api.retrieval_orchestration_dependency import (
    get_retrieval_orchestration_service,
)
from app.services.grounded_answer_generation import (
    GroundedAnswerGenerationService,
)
from app.services.rag_orchestration import (
    RagOrchestrationService,
)
from app.services.retrieval_orchestration import (
    RetrievalOrchestrationService,
)


def get_rag_orchestration_service(
    retrieval_service: Annotated[
        RetrievalOrchestrationService,
        Depends(
            get_retrieval_orchestration_service,
        ),
    ],
    grounded_answer_service: Annotated[
        GroundedAnswerGenerationService,
        Depends(
            get_grounded_answer_generation_service,
        ),
    ],
) -> RagOrchestrationService:
    """Assemble retrieval and generation into one RAG service."""

    return RagOrchestrationService(
        retrieval_service=retrieval_service,
        grounded_answer_service=grounded_answer_service,
    )
