# File: /backend/app/repositories/generated_study_plan_regeneration_repository.py
# Purpose: Atomically replaces generated sessions on an existing
# generated study plan through the trusted regeneration RPC.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from typing import (
    Protocol,
)
from uuid import UUID

from pydantic import ValidationError

from app.schemas.generated_study_plan import (
    GeneratedStudyPlanPersistenceResult,
)
from app.schemas.generated_study_plan_regeneration import (
    GeneratedStudyPlanRegenerationRequest,
)
from app.schemas.study_plan import (
    StudyPlanResponse,
    StudySessionResponse,
)
from app.services.study_plan_errors import (
    StudyPlanPersistenceError,
    StudyPlanResponseError,
)

_REGENERATION_RPC = (
    "replace_generated_study_plan_sessions"
)


class _SupabaseResponse(
    Protocol,
):
    data: object


class _SupabaseRpcQuery(
    Protocol,
):
    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseClient(
    Protocol,
):
    def rpc(
        self,
        function_name: str,
        params: Mapping[
            str,
            object,
        ],
    ) -> _SupabaseRpcQuery: ...


class GeneratedStudyPlanRegenerationRepository:
    """Replaces generated sessions transactionally."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def replace_generated_schedule(
        self,
        *,
        user_id: UUID,
        study_plan_id: UUID,
        request:
            GeneratedStudyPlanRegenerationRequest,
    ) -> GeneratedStudyPlanPersistenceResult:
        """Replace generated sessions while preserving manual ones."""

        sessions_payload = [
            {
                "subject_id": str(
                    session.subject_id,
                ),
                "title": (
                    session.title
                ),
                "starts_at": (
                    session
                    .starts_at
                    .isoformat()
                ),
                "ends_at": (
                    session
                    .ends_at
                    .isoformat()
                ),
            }
            for session in request.sessions
        ]

        try:
            response = (
                self._client
                .rpc(
                    _REGENERATION_RPC,
                    {
                        "p_user_id": str(
                            user_id,
                        ),
                        "p_study_plan_id": str(
                            study_plan_id,
                        ),
                        "p_generated_at": (
                            request
                            .generated_at
                            .isoformat()
                        ),
                        "p_sessions": (
                            sessions_payload
                        ),
                    },
                )
                .execute()
            )

        except Exception as exc:
            raise StudyPlanPersistenceError(
                "Unable to replace generated "
                "study-plan sessions.",
            ) from exc

        rows = self._extract_rows(
            response,
        )

        if len(
            rows,
        ) != 1:
            raise StudyPlanResponseError(
                "Study-plan regeneration returned "
                "an unexpected response.",
            )

        row = rows[0]

        plan_data = row.get(
            "plan",
        )

        sessions_data = row.get(
            "sessions",
        )

        if not isinstance(
            plan_data,
            Mapping,
        ):
            raise StudyPlanResponseError(
                "Regenerated study-plan data "
                "was invalid.",
            )

        if (
            isinstance(
                sessions_data,
                (str, bytes),
            )
            or not isinstance(
                sessions_data,
                Sequence,
            )
        ):
            raise StudyPlanResponseError(
                "Regenerated study-session data "
                "was invalid.",
            )

        try:
            plan = (
                StudyPlanResponse
                .model_validate(
                    plan_data,
                )
            )

            sessions = tuple(
                StudySessionResponse
                .model_validate(
                    session,
                )
                for session in sessions_data
            )

        except ValidationError as exc:
            raise StudyPlanResponseError(
                "Study-plan regeneration response "
                "was invalid.",
            ) from exc

        return (
            GeneratedStudyPlanPersistenceResult(
                plan=plan,
                sessions=sessions,
            )
        )

    @staticmethod
    def _extract_rows(
        response: _SupabaseResponse,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Validate the tabular RPC response."""

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            isinstance(
                data,
                (str, bytes),
            )
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise StudyPlanResponseError(
                "Supabase returned invalid "
                "study-plan regeneration data.",
            )

        rows: list[
            Mapping[
                str,
                object,
            ]
        ] = []

        for item in data:
            if not isinstance(
                item,
                Mapping,
            ):
                raise StudyPlanResponseError(
                    "Supabase returned an invalid "
                    "regeneration row.",
                )

            rows.append(
                item,
            )

        return rows