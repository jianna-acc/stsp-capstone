# File: /backend/app/repositories/flashcard_repository.py
# Purpose: Persists and reads authenticated students'
# generated Flashcard decks and cards through Supabase.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, Self
from uuid import UUID

from pydantic import ValidationError

from app.schemas.flashcard import (
    MAX_FLASHCARD_MODEL_CHARACTERS,
    MAX_FLASHCARD_TITLE_CHARACTERS,
    MAX_FLASHCARDS_PER_DECK,
    MIN_FLASHCARDS_PER_DECK,
    FlashcardDeckResponse,
    FlashcardItem,
    FlashcardScopeType,
    FlashcardSource,
)
from app.schemas.flashcard_summary import (
    FlashcardDeckSummary,
)
from app.services.flashcard_errors import (
    FlashcardPersistenceError,
    FlashcardResponseError,
    FlashcardValidationError,
)

_FLASHCARD_DECK_COLUMNS = (
    "id,"
    "subject_id,"
    "study_file_id,"
    "scope_type,"
    "title,"
    "requested_card_count,"
    "sources,"
    "generation_model,"
    "generation_count,"
    "generated_at,"
    "created_at,"
    "updated_at"
)

_FLASHCARD_COLUMNS = (
    "id,"
    "deck_id,"
    "position,"
    "question,"
    "answer,"
    "created_at"
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

    def delete(
        self,
    ) -> Self: ...

    def eq(
        self,
        column: str,
        value: object,
    ) -> Self: ...

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> Self: ...

    def execute(
        self,
    ) -> _SupabaseResponse: ...


class _SupabaseRpcQuery(
    Protocol,
):
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

    def rpc(
        self,
        function_name: str,
        params: Mapping[
            str,
            object,
        ],
    ) -> _SupabaseRpcQuery: ...


class FlashcardRepository:
    """Reads and persists Flashcard decks owned by students."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def create_deck(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        study_file_id: UUID | None,
        scope_type: FlashcardScopeType,
        title: str,
        requested_card_count: int,
        cards: Sequence[
            FlashcardItem,
        ],
        sources: Sequence[
            FlashcardSource,
        ],
        generation_model: str,
    ) -> FlashcardDeckResponse:
        """Atomically save and return one generated deck."""

        normalized_title = title.strip()
        normalized_model = generation_model.strip()

        if not normalized_title:
            raise FlashcardValidationError(
                "Flashcard deck title must not be empty.",
            )

        if (
            len(
                normalized_title,
            )
            > MAX_FLASHCARD_TITLE_CHARACTERS
        ):
            raise FlashcardValidationError(
                "Flashcard deck title is too long.",
            )

        if not normalized_model:
            raise FlashcardValidationError(
                "Flashcard generation model must not be empty.",
            )

        if (
            len(
                normalized_model,
            )
            > MAX_FLASHCARD_MODEL_CHARACTERS
        ):
            raise FlashcardValidationError(
                "Flashcard generation model is too long.",
            )

        if (
            isinstance(
                requested_card_count,
                bool,
            )
            or not isinstance(
                requested_card_count,
                int,
            )
            or not (
                MIN_FLASHCARDS_PER_DECK
                <= requested_card_count
                <= MAX_FLASHCARDS_PER_DECK
            )
        ):
            raise FlashcardValidationError(
                "Flashcard count must be between "
                f"{MIN_FLASHCARDS_PER_DECK} and "
                f"{MAX_FLASHCARDS_PER_DECK}.",
            )

        if (
            len(
                cards,
            )
            != requested_card_count
        ):
            raise FlashcardValidationError(
                "Generated Flashcard count does not "
                "match the requested count.",
            )

        if (
            scope_type
            is FlashcardScopeType.FILE
            and study_file_id is None
        ):
            raise FlashcardValidationError(
                "File-scope Flashcard decks require "
                "a study file.",
            )

        if (
            scope_type
            is FlashcardScopeType.SUBJECT
            and study_file_id is not None
        ):
            raise FlashcardValidationError(
                "Subject-scope Flashcard decks cannot "
                "store a study file.",
            )

        params: dict[
            str,
            object,
        ] = {
            "p_user_id": str(
                user_id,
            ),
            "p_subject_id": str(
                subject_id,
            ),
            "p_study_file_id": (
                str(
                    study_file_id,
                )
                if study_file_id is not None
                else None
            ),
            "p_scope_type": scope_type.value,
            "p_title": normalized_title,
            "p_requested_card_count": (
                requested_card_count
            ),
            "p_sources": [
                source.model_dump(
                    mode="json",
                )
                for source in sources
            ],
            "p_generation_model": normalized_model,
            "p_cards": [
                card.model_dump(
                    mode="json",
                )
                for card in cards
            ],
        }

        try:
            rpc_query = self._client.rpc(
                "create_flashcard_deck_with_cards",
                params,
            )

        except Exception as exc:
            raise FlashcardPersistenceError(
                "Unable to prepare Flashcard persistence.",
            ) from exc

        response = self._execute_rpc(
            rpc_query,
            operation="create the Flashcard deck",
        )

        deck_id = self._extract_created_deck_id(
            response,
        )

        deck = self.get_deck(
            user_id=user_id,
            deck_id=deck_id,
        )

        if deck is None:
            raise FlashcardResponseError(
                "The created Flashcard deck could not "
                "be loaded.",
            )

        return deck

    def list_decks(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
    ) -> tuple[
        FlashcardDeckSummary,
        ...,
    ]:
        """Return the student's saved decks newest first."""

        query = (
            self._client
            .table(
                "flashcard_decks",
            )
            .select(
                _FLASHCARD_DECK_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
        )

        if subject_id is not None:
            query = query.eq(
                "subject_id",
                str(
                    subject_id,
                ),
            )

        response = self._execute(
            query.order(
                "created_at",
                desc=True,
            ),
            operation="list the Flashcard decks",
        )

        rows = self._extract_rows(
            response,
            resource="Flashcard deck",
        )

        summaries: list[
            FlashcardDeckSummary
        ] = []

        for row in rows:
            summaries.append(
                self._parse_deck_summary(
                    row,
                )
            )

        return tuple(
            summaries,
        )

    def get_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> FlashcardDeckResponse | None:
        """Return one owned Flashcard deck and its cards."""

        deck_response = self._execute(
            self._client
            .table(
                "flashcard_decks",
            )
            .select(
                _FLASHCARD_DECK_COLUMNS,
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
            ),
            operation="load the Flashcard deck",
        )

        deck_rows = self._extract_rows(
            deck_response,
            resource="Flashcard deck",
        )

        if not deck_rows:
            return None

        if len(
            deck_rows,
        ) != 1:
            raise FlashcardResponseError(
                "The Flashcard deck lookup response "
                "was invalid.",
            )

        card_response = self._execute(
            self._client
            .table(
                "flashcards",
            )
            .select(
                _FLASHCARD_COLUMNS,
            )
            .eq(
                "deck_id",
                str(
                    deck_id,
                ),
            )
            .order(
                "position",
                desc=False,
            ),
            operation="load the Flashcards",
        )

        card_rows = self._extract_rows(
            card_response,
            resource="Flashcard",
        )

        cards = self._parse_cards(
            card_rows,
        )

        return self._parse_deck(
            deck_rows[0],
            cards=cards,
        )

    def delete_deck(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> bool:
        """Delete one Flashcard deck belonging to the student."""

        response = self._execute(
            self._client
            .table(
                "flashcard_decks",
            )
            .delete()
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
            ),
            operation="delete the Flashcard deck",
        )

        rows = self._extract_rows(
            response,
            resource="Flashcard deck",
        )

        return bool(
            rows,
        )

    def _execute(
        self,
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one Supabase table query safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise FlashcardPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _execute_rpc(
        self,
        query: _SupabaseRpcQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        """Execute one trusted Supabase RPC safely."""

        try:
            return query.execute()

        except Exception as exc:
            raise FlashcardPersistenceError(
                f"Unable to {operation}.",
            ) from exc

    def _extract_created_deck_id(
        self,
        response: _SupabaseResponse,
    ) -> UUID:
        """Extract the UUID returned by the persistence RPC."""

        data = getattr(
            response,
            "data",
            None,
        )

        if isinstance(
            data,
            UUID,
        ):
            return data

        if not isinstance(
            data,
            str,
        ):
            raise FlashcardResponseError(
                "Flashcard persistence returned "
                "an invalid deck ID.",
            )

        try:
            return UUID(
                data,
            )

        except ValueError as exc:
            raise FlashcardResponseError(
                "Flashcard persistence returned "
                "an invalid deck ID.",
            ) from exc

    def _extract_rows(
        self,
        response: _SupabaseResponse,
        *,
        resource: str,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        """Validate and normalize Supabase row data."""

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            isinstance(
                data,
                (
                    str,
                    bytes,
                ),
            )
            or not isinstance(
                data,
                Sequence,
            )
        ):
            raise FlashcardResponseError(
                f"Supabase returned invalid {resource} data.",
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
                raise FlashcardResponseError(
                    f"Supabase returned an invalid "
                    f"{resource} row.",
                )

            rows.append(
                item,
            )

        return rows

    def _parse_cards(
        self,
        rows: Sequence[
            Mapping[
                str,
                object,
            ]
        ],
    ) -> tuple[
        FlashcardItem,
        ...,
    ]:
        """Parse ordered database card rows safely."""

        cards: list[
            FlashcardItem
        ] = []

        for expected_position, row in enumerate(
            rows,
        ):
            position = row.get(
                "position",
            )

            if (
                isinstance(
                    position,
                    bool,
                )
                or not isinstance(
                    position,
                    int,
                )
                or position
                != expected_position
            ):
                raise FlashcardResponseError(
                    "Stored Flashcard positions were invalid.",
                )

            try:
                card = FlashcardItem.model_validate(
                    {
                        "question": row.get(
                            "question",
                        ),
                        "answer": row.get(
                            "answer",
                        ),
                    }
                )

            except ValidationError as exc:
                raise FlashcardResponseError(
                    "Stored Flashcard data was invalid.",
                ) from exc

            cards.append(
                card,
            )

        return tuple(
            cards,
        )

    def _parse_deck(
        self,
        row: Mapping[
            str,
            object,
        ],
        *,
        cards: Sequence[
            FlashcardItem,
        ],
    ) -> FlashcardDeckResponse:
        """Parse one database deck row into a safe response."""

        requested_card_count = row.get(
            "requested_card_count",
        )

        if (
            isinstance(
                requested_card_count,
                bool,
            )
            or not isinstance(
                requested_card_count,
                int,
            )
            or requested_card_count
            != len(
                cards,
            )
        ):
            raise FlashcardResponseError(
                "Stored Flashcard count was invalid.",
            )

        payload = dict(
            row,
        )

        payload[
            "cards"
        ] = [
            card.model_dump(
                mode="json",
            )
            for card in cards
        ]

        try:
            return FlashcardDeckResponse.model_validate(
                payload,
            )

        except ValidationError as exc:
            raise FlashcardResponseError(
                "The stored Flashcard deck data was invalid.",
            ) from exc

    def _parse_deck_summary(
        self,
        row: Mapping[
            str,
            object,
        ],
    ) -> FlashcardDeckSummary:
        """Parse one saved deck summary safely."""

        try:
            return FlashcardDeckSummary.model_validate(
                row,
            )

        except ValidationError as exc:
            raise FlashcardResponseError(
                "The stored Flashcard deck summary "
                "was invalid.",
            ) from exc