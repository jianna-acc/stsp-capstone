# File: /backend/tests/test_generated_study_plan_regeneration_service.py
# Purpose: Tests validation and delegation for generated
# study-plan replacement persistence.

from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import uuid4

import pytest

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.study_plan import (
    StudyPlanResponse,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)
from app.services.generated_study_plan_regeneration_service import (
    GeneratedStudyPlanRegenerationService,
)
from app.services.study_plan_errors import (
    StudyPlanValidationError,
)

_FIXED_TIME = datetime(
    2026,
    8,
    11,
    0,
    30,
    tzinfo=timezone.utc,
)


class _RepositoryStub:
    def __init__(
        self,
        result:
            GeneratedStudyPlanPersistenceResult,
    ) -> None:
        self.result = result
        self.request = None

    def replace_generated_schedule(
        self,
        **kwargs,
    ) -> GeneratedStudyPlanPersistenceResult:
        self.request = kwargs

        return self.result


def _result() -> GeneratedStudyPlanPersistenceResult:
    plan_id = uuid4()

    return (
        GeneratedStudyPlanPersistenceResult(
            plan=StudyPlanResponse(
                id=plan_id,
                title="Finals Plan",
                starts_on=date(
                    2026,
                    8,
                    11,
                ),
                ends_on=date(
                    2026,
                    8,
                    20,
                ),
                status="active",
                generation_mode="generated",
                generated_at=_FIXED_TIME,
                created_at=_FIXED_TIME,
                updated_at=_FIXED_TIME,
            ),
            sessions=(),
        )
    )


def _session() -> GeneratedStudySession:
    return GeneratedStudySession(
        task_id=uuid4(),
        subject_id=uuid4(),
        title="Review Biology",
        starts_at=datetime(
            2026,
            8,
            11,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        ends_at=datetime(
            2026,
            8,
            11,
            19,
            0,
            tzinfo=timezone.utc,
        ),
        duration_minutes=60,
    )


def test_service_builds_timestamped_replacement_request() -> None:
    repository = _RepositoryStub(
        _result(),
    )

    service = (
        GeneratedStudyPlanRegenerationService(
            repository,
            clock=lambda: _FIXED_TIME,
        )
    )

    user_id = uuid4()
    plan_id = uuid4()
    session = _session()

    service.replace_generated_schedule(
        user_id=user_id,
        study_plan_id=plan_id,
        sessions=(
            session,
        ),
    )

    assert (
        repository.request
        is not None
    )

    assert (
        repository.request[
            "user_id"
        ]
        == user_id
    )

    assert (
        repository.request[
            "study_plan_id"
        ]
        == plan_id
    )

    request = (
        repository.request[
            "request"
        ]
    )

    assert (
        request.generated_at
        == _FIXED_TIME
    )

    assert (
        request.sessions
        == (
            session,
        )
    )


def test_service_rejects_empty_replacement_schedule() -> None:
    service = (
        GeneratedStudyPlanRegenerationService(
            _RepositoryStub(
                _result(),
            ),
            clock=lambda: _FIXED_TIME,
        )
    )

    with pytest.raises(
        StudyPlanValidationError,
    ):
        service.replace_generated_schedule(
            user_id=uuid4(),
            study_plan_id=uuid4(),
            sessions=(),
        )