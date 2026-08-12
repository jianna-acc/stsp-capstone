# File: /backend/app/repositories/flashcard_review_repository.py
# Purpose: Persists authenticated Flashcard self-assessment review events.

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Protocol,
    Self,
)
from uuid import UUID

from postgrest.exceptions import (
    APIError,
)

from app.schemas.flashcard_review import (
    FlashcardReviewOutcome,
    FlashcardReviewResponse,
)
from app.services.flashcard_review_errors import (
    FlashcardReviewNotFoundError,
    FlashcardReviewPersistenceError,
    FlashcardReviewResponseError,
)


class _SupabaseResponse(
    Protocol,
):
    data: object


class _SupabaseQuery(
    Protocol,
):
    def select(
        self,
        columns: str,
    ) -> Self: ...

    def insert(
        self,
        payload: Mapping[
            str,
            object,
        ],
    ) -> Self: ...

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseClient(
    Protocol,
):
    def table(
        self,
        table_name: str,
    ) -> _SupabaseQuery: ...


class FlashcardReviewRepository:
    """Reads and persists Flashcard review events for one student."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def create_review(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        card_position: int,
        outcome: FlashcardReviewOutcome,
    ) -> FlashcardReviewResponse:
        """Persist one owned Flashcard self-assessment event."""

        self._require_owned_card(
            user_id=user_id,
            deck_id=deck_id,
            card_position=card_position,
        )

        payload: dict[
            str,
            object,
        ] = {
            "user_id": str(
                user_id,
            ),
            "deck_id": str(
                deck_id,
            ),
            "card_position": card_position,
            "outcome": outcome.value,
        }

        query = (
            self._client.table(
                "flashcard_review_events",
            )
            .insert(
                payload,
            )
        )

        rows = self._execute_rows(
            query,
            resource="Flashcard review",
        )

        if len(
            rows,
        ) != 1:
            raise FlashcardReviewResponseError(
                "Flashcard review storage returned an invalid response.",
            )

        return self._parse_review(
            rows[0],
        )

    def _require_owned_card(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        card_position: int,
    ) -> None:
        """Require that the review target belongs to the student."""

        deck_query = (
            self._client.table(
                "flashcard_decks",
            )
            .select(
                "id",
            )
            .eq(
                "id",
                str(
                    deck_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
        )

        deck_rows = self._execute_rows(
            deck_query,
            resource="Flashcard deck",
        )

        if not deck_rows:
            raise FlashcardReviewNotFoundError(
                "The Flashcard deck was not found.",
            )

        card_query = (
            self._client.table(
                "flashcards",
            )
            .select(
                "id",
            )
            .eq(
                "deck_id",
                str(
                    deck_id,
                ),
            )
            .eq(
                "position",
                card_position,
            )
        )

        card_rows = self._execute_rows(
            card_query,
            resource="Flashcard card",
        )

        if not card_rows:
            raise FlashcardReviewNotFoundError(
                "The Flashcard card was not found.",
            )

    def _execute_rows(
        self,
        query: _SupabaseQuery,
        *,
        resource: str,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Execute and validate one Flashcard review query."""

        try:
            response = query.execute()
        except APIError as exc:
            raise FlashcardReviewPersistenceError(
                f"Unable to access {resource}.",
            ) from exc

        data = response.data

        if not isinstance(
            data,
            Sequence,
        ) or isinstance(
            data,
            str | bytes,
        ):
            raise FlashcardReviewResponseError(
                "Flashcard review storage returned an invalid response.",
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
                raise FlashcardReviewResponseError(
                    "Flashcard review storage returned an invalid row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_review(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> FlashcardReviewResponse:
        """Parse one stored Flashcard review event."""

        review_id = self._parse_uuid(
            row.get(
                "id",
            ),
        )

        deck_id = self._parse_uuid(
            row.get(
                "deck_id",
            ),
        )

        card_position = row.get(
            "card_position",
        )

        if (
            isinstance(
                card_position,
                bool,
            )
            or not isinstance(
                card_position,
                int,
            )
            or card_position < 0
        ):
            raise FlashcardReviewResponseError(
                "Stored Flashcard review position is invalid.",
            )

        try:
            outcome = FlashcardReviewOutcome(
                row.get(
                    "outcome",
                ),
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise FlashcardReviewResponseError(
                "Stored Flashcard review outcome is invalid.",
            ) from exc

        reviewed_at = self._parse_datetime(
            row.get(
                "reviewed_at",
            ),
        )

        return FlashcardReviewResponse(
            id=review_id,
            deck_id=deck_id,
            card_position=card_position,
            outcome=outcome,
            reviewed_at=reviewed_at,
        )

    @staticmethod
    def _parse_uuid(
        value: object,
    ) -> UUID:
        """Parse one persisted UUID safely."""

        try:
            return UUID(
                str(
                    value,
                ),
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise FlashcardReviewResponseError(
                "Stored Flashcard review UUID is invalid.",
            ) from exc

    @staticmethod
    def _parse_datetime(
        value: object,
    ) -> datetime:
        """Parse one timezone-aware review timestamp."""

        if isinstance(
            value,
            datetime,
        ):
            parsed = value
        elif isinstance(
            value,
            str,
        ):
            try:
                parsed = datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    ),
                )
            except ValueError as exc:
                raise FlashcardReviewResponseError(
                    "Stored Flashcard review timestamp is invalid.",
                ) from exc
        else:
            raise FlashcardReviewResponseError(
                "Stored Flashcard review timestamp is invalid.",
            )

        if parsed.tzinfo is None:
            raise FlashcardReviewResponseError(
                "Stored Flashcard review timestamp must include a timezone.",
            )

        return parsed.astimezone(
            timezone.utc,
        )