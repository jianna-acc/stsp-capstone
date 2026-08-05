# File: /backend/tests/test_query_embedding_integration.py
# Purpose: Tests query failure codes, package exports, provider
# cleanup, and FastAPI dependency construction without live APIs.

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

import pytest

import app.services as services_package
from app.ai.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
)
from app.ai.errors import AIProviderRequestError
from app.api import (
    query_embedding_dependency as dependency_module,
)
from app.core.config import Settings
from app.services.query_embedding import (
    QueryEmbeddingFailureCode,
    QueryEmbeddingProviderError,
    QueryEmbeddingService,
    QueryEmbeddingValidationError,
)

EMBEDDING_DIMENSIONS = 768
EMBEDDING_MODEL = "gemini-embedding-2"


def make_settings() -> Settings:
    """Create the settings needed by the query service."""

    return cast(
        Settings,
        SimpleNamespace(
            gemini_embedding_model=EMBEDDING_MODEL,
            gemini_embedding_dimensions=(
                EMBEDDING_DIMENSIONS
            ),
        ),
    )


def make_vector(
    value: float = 0.125,
) -> tuple[float, ...]:
    """Create one deterministic query vector."""

    return tuple(
        value
        for _ in range(
            EMBEDDING_DIMENSIONS,
        )
    )


class SuccessfulProvider:
    """Return one valid query embedding."""

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Return one valid provider-independent result."""

        return EmbeddingResult(
            vectors=(
                make_vector(),
            ),
            provider="gemini",
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        )


class FailingProvider:
    """Raise one controlled provider error."""

    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """Simulate a failed external provider request."""

        raise AIProviderRequestError(
            "External provider request failed.",
        )


class ClosableProvider(
    SuccessfulProvider,
):
    """Record asynchronous provider cleanup."""

    def __init__(
        self,
    ) -> None:
        self.closed = False

    async def aclose(
        self,
    ) -> None:
        """Record cleanup."""

        self.closed = True


def test_validation_error_uses_stable_failure_code() -> None:
    """Invalid questions should expose the validation code."""

    with pytest.raises(
        QueryEmbeddingValidationError,
    ) as error_info:
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=SuccessfulProvider(),
            ).embed_query(
                "   ",
            ),
        )

    assert error_info.value.error_code is (
        QueryEmbeddingFailureCode
        .QUERY_VALIDATION_FAILED
    )

    assert str(
        error_info.value.error_code,
    ) == "QUERY_VALIDATION_FAILED"


def test_provider_error_uses_stable_failure_code() -> None:
    """Provider failures should expose the embedding code."""

    with pytest.raises(
        QueryEmbeddingProviderError,
    ) as error_info:
        asyncio.run(
            QueryEmbeddingService(
                settings=make_settings(),
                provider=FailingProvider(),
            ).embed_query(
                "What is photosynthesis?",
            ),
        )

    assert error_info.value.error_code is (
        QueryEmbeddingFailureCode
        .QUERY_EMBEDDING_FAILED
    )

    assert str(
        error_info.value.error_code,
    ) == "QUERY_EMBEDDING_FAILED"


def test_service_closes_supported_provider() -> None:
    """Service cleanup should close provider-owned resources."""

    provider = ClosableProvider()

    service = QueryEmbeddingService(
        settings=make_settings(),
        provider=provider,
    )

    asyncio.run(
        service.aclose(),
    )

    assert provider.closed is True


def test_service_allows_provider_without_close() -> None:
    """Test providers without cleanup should remain supported."""

    service = QueryEmbeddingService(
        settings=make_settings(),
        provider=SuccessfulProvider(),
    )

    asyncio.run(
        service.aclose(),
    )


def test_services_package_exports_query_contract() -> None:
    """The services package should expose the public contract."""

    assert services_package.QueryEmbeddingService is (
        QueryEmbeddingService
    )

    assert (
        services_package.QueryEmbeddingFailureCode
        is QueryEmbeddingFailureCode
    )

    assert (
        "QueryEmbeddingService"
        in services_package.__all__
    )

    assert (
        "QueryEmbeddingFailureCode"
        in services_package.__all__
    )


def test_dependency_creates_and_closes_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI dependency should guarantee cleanup."""

    created_services: list[Any] = []

    class FakeQueryEmbeddingService:
        """Record construction and cleanup."""

        def __init__(
            self,
            settings: Settings,
        ) -> None:
            self.settings = settings
            self.closed = False

            created_services.append(
                self,
            )

        async def aclose(
            self,
        ) -> None:
            """Record dependency cleanup."""

            self.closed = True

    monkeypatch.setattr(
        dependency_module,
        "QueryEmbeddingService",
        FakeQueryEmbeddingService,
    )

    settings = make_settings()

    async def execute_dependency() -> Any:
        dependency = (
            dependency_module
            .get_query_embedding_service(
                settings=settings,
            )
        )

        service = await anext(
            dependency,
        )

        assert service.settings is settings
        assert service.closed is False

        await dependency.aclose()

        return service

    service = asyncio.run(
        execute_dependency(),
    )

    assert len(
        created_services,
    ) == 1

    assert service.closed is True