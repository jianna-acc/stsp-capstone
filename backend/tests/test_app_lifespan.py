# File: /backend/tests/test_app_lifespan.py
# Purpose: Verifies that FastAPI automatically starts and stops
# the file-processing worker when background processing is enabled.

import asyncio

import app.main as main_module


class FakeFileProcessingWorker:
    """In-memory worker used to verify lifespan behavior."""

    created_count = 0
    started_count = 0
    stopped_count = 0

    def __init__(
        self,
        settings: object,
    ) -> None:
        self.settings = settings

        type(self).created_count += 1

    async def run_forever(
        self,
        stop_event: asyncio.Event,
    ) -> None:
        """Wait until the application requests worker shutdown."""

        type(self).started_count += 1

        await stop_event.wait()

        type(self).stopped_count += 1


def reset_fake_worker_counts() -> None:
    """Reset shared fake-worker counters between tests."""

    FakeFileProcessingWorker.created_count = 0
    FakeFileProcessingWorker.started_count = 0
    FakeFileProcessingWorker.stopped_count = 0


def test_lifespan_starts_and_stops_file_processing_worker(
    monkeypatch,
) -> None:
    """Enabled processing should follow the FastAPI lifecycle."""

    reset_fake_worker_counts()

    monkeypatch.setattr(
        main_module.settings,
        "file_processing_worker_enabled",
        True,
    )

    monkeypatch.setattr(
        main_module,
        "FileProcessingWorker",
        FakeFileProcessingWorker,
    )

    async def run_test() -> None:
        async with main_module.lifespan(
            main_module.app,
        ):
            await asyncio.sleep(0)

            assert FakeFileProcessingWorker.created_count == 1
            assert FakeFileProcessingWorker.started_count == 1
            assert FakeFileProcessingWorker.stopped_count == 0

        assert FakeFileProcessingWorker.stopped_count == 1

    asyncio.run(
        run_test(),
    )


def test_lifespan_skips_worker_when_processing_is_disabled(
    monkeypatch,
) -> None:
    """Disabled processing should not create a background worker."""

    reset_fake_worker_counts()

    monkeypatch.setattr(
        main_module.settings,
        "file_processing_worker_enabled",
        False,
    )

    monkeypatch.setattr(
        main_module,
        "FileProcessingWorker",
        FakeFileProcessingWorker,
    )

    async def run_test() -> None:
        async with main_module.lifespan(
            main_module.app,
        ):
            await asyncio.sleep(0)

        assert FakeFileProcessingWorker.created_count == 0
        assert FakeFileProcessingWorker.started_count == 0
        assert FakeFileProcessingWorker.stopped_count == 0

    asyncio.run(
        run_test(),
    )