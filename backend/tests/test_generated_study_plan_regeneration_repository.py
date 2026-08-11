# File: /backend/tests/test_generated_study_plan_regeneration_repository.py
# Purpose: Tests the generated study-plan regeneration RPC adapter.

from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from app.repositories.generated_study_plan_regeneration_repository import (
    GeneratedStudyPlanRegenerationRepository,
)
from app.schemas.generated_study_plan_regeneration import (
    GeneratedStudyPlanRegenerationRequest,
)
from app.schemas.study_scheduler import (
    GeneratedStudySession,
)

_NOW = datetime(
    2026,
    8,
    11,
    0,
    30,
    tzinfo=timezone.utc,
)


class _Response:
    def __init__(
        self,
        data,
    ) -> None:
        self.data = data


class _RpcQuery:
    def __init__(
        self,
        response,
    ) -> None:
        self.response = response

    def execute(
        self,
    ):
        return self.response


class _Client:
    def __init__(
        self,
        response,
    ) -> None:
        self.response = response
        self.function_name = None
        self.params = None

    def rpc(
        self,
        function_name,
        params,
    ):
        self.function_name = (
            function_name
        )

        self.params = params

        return _RpcQuery(
            self.response,
        )


def test_repository_calls_regeneration_rpc_and_parses_result() -> None:
    user_id = uuid4()
    plan_id = uuid4()
    subject_id = uuid4()
    session_id = uuid4()

    client = _Client(
        _Response(
            [
                {
                    "plan": {
                        "id": str(
                            plan_id,
                        ),
                        "title":
                            "Finals Plan",
                        "starts_on":
                            "2026-08-11",
                        "ends_on":
                            "2026-08-20",
                        "status":
                            "active",
                        "generation_mode":
                            "generated",
                        "generated_at":
                            _NOW.isoformat(),
                        "created_at":
                            _NOW.isoformat(),
                        "updated_at":
                            _NOW.isoformat(),
                    },
                    "sessions": [
                        {
                            "id": str(
                                session_id,
                            ),
                            "study_plan_id": str(
                                plan_id,
                            ),
                            "subject_id": str(
                                subject_id,
                            ),
                            "title":
                                "Review Biology",
                            "starts_at":
                                "2026-08-11T18:00:00+00:00",
                            "ends_at":
                                "2026-08-11T19:00:00+00:00",
                            "status":
                                "planned",
                            "origin":
                                "generated",
                            "notes":
                                None,
                            "created_at":
                                _NOW.isoformat(),
                            "updated_at":
                                _NOW.isoformat(),
                        },
                    ],
                },
            ],
        )
    )

    repository = (
        GeneratedStudyPlanRegenerationRepository(
            client,
        )
    )

    request = (
        GeneratedStudyPlanRegenerationRequest(
            generated_at=_NOW,
            sessions=(
                GeneratedStudySession(
                    task_id=uuid4(),
                    subject_id=subject_id,
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
                ),
            ),
        )
    )

    result = (
        repository
        .replace_generated_schedule(
            user_id=user_id,
            study_plan_id=plan_id,
            request=request,
        )
    )

    assert (
        client.function_name
        ==
        "replace_generated_study_plan_sessions"
    )

    assert (
        client.params[
            "p_user_id"
        ]
        == str(
            user_id,
        )
    )

    assert (
        client.params[
            "p_study_plan_id"
        ]
        == str(
            plan_id,
        )
    )

    assert (
        result.plan.id
        == plan_id
    )

    assert len(
        result.sessions,
    ) == 1

    assert (
        result.sessions[0]
        .origin
        == "generated"
    )