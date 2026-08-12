# File: /backend/tests/test_reviewer_orchestration_dependency.py
# Purpose: Verifies reviewer dependency assembly uses the configured
# generation-provider factory without making external service calls.

import asyncio
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

from app.api import reviewer_orchestration_dependency as dependency_module


class FakeGenerationService:
    """Record provider wiring and close behavior."""

    instances: ClassVar[list["FakeGenerationService"]] = []

    def __init__(
        self,
        *,
        provider: Any,
    ) -> None:
        self.provider = provider
        self.closed = False
        self.__class__.instances.append(self)

    async def aclose(self) -> None:
        self.closed = True


class FakeAdminService:
    """Avoid creating a real Supabase administration client."""

    def __init__(
        self,
        *,
        settings: Any,
    ) -> None:
        self.settings = settings


class FakeSourceLoader:
    """Record source-loader construction."""

    def __init__(
        self,
        admin_service: Any,
    ) -> None:
        self.admin_service = admin_service


class FakeOrchestrationService:
    """Record orchestration dependencies."""

    def __init__(
        self,
        *,
        source_loader: Any,
        generation_service: Any,
        reviewer_service: Any,
    ) -> None:
        self.source_loader = source_loader
        self.generation_service = generation_service
        self.reviewer_service = reviewer_service


def test_dependency_uses_generation_provider_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeGenerationService.instances.clear()

    settings = SimpleNamespace(
        ai_provider="bedrock",
    )
    reviewer_service = object()
    provider = object()

    captured_settings: list[Any] = []

    def fake_create_generation_provider(
        *,
        settings: Any,
    ) -> Any:
        captured_settings.append(settings)
        return provider

    monkeypatch.setattr(
        dependency_module,
        "create_generation_provider",
        fake_create_generation_provider,
    )
    monkeypatch.setattr(
        dependency_module,
        "ReviewerGenerationService",
        FakeGenerationService,
    )
    monkeypatch.setattr(
        dependency_module,
        "SupabaseAdminService",
        FakeAdminService,
    )
    monkeypatch.setattr(
        dependency_module,
        "ReviewerSourceLoader",
        FakeSourceLoader,
    )
    monkeypatch.setattr(
        dependency_module,
        "ReviewerOrchestrationService",
        FakeOrchestrationService,
    )

    async def run_dependency() -> None:
        dependency = (
            dependency_module.get_reviewer_orchestration_service(
                settings=settings,
                reviewer_service=reviewer_service,
            )
        )

        service = await dependency.__anext__()

        assert captured_settings == [
            settings,
        ]

        assert len(
            FakeGenerationService.instances
        ) == 1

        generation_service = (
            FakeGenerationService.instances[0]
        )

        assert generation_service.provider is provider

        assert service.generation_service is generation_service
        assert service.reviewer_service is reviewer_service

        await dependency.aclose()

        assert generation_service.closed is True

    asyncio.run(
        run_dependency()
    )