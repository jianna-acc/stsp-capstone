# File: /backend/app/repositories/study_conversation_repository.py
# Purpose: Persists and reads authenticated Study Assistant
# conversations and messages through Supabase.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Protocol, Self
from uuid import UUID

from pydantic import ValidationError

from app.schemas.study_conversation import (
    StudyConversationResponse,
    StudyConversationSummaryState,
    StudyConversationSummaryUpdate,
    StudyMessageOutcome,
    StudyMessageResponse,
    StudyMessageRole,
    StudyMessageSourceResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationPersistenceError,
    StudyConversationResponseError,
    StudyConversationValidationError,
)

_CONVERSATION_COLUMNS = (
    "id,title,subject_id,study_file_id,"
    "created_at,updated_at,last_message_at"
)

_SUMMARY_COLUMNS = (
    "id,summary_text,summarized_message_count,"
    "summary_updated_at,summary_version"
)

_MESSAGE_COLUMNS = (
    "id,conversation_id,role,content,"
    "outcome,sources,created_at"
)

_CONVERSATION_FIELDS = (
    "id",
    "title",
    "subject_id",
    "study_file_id",
    "created_at",
    "updated_at",
    "last_message_at",
)

_SUMMARY_FIELDS = (
    "summary_text",
    "summarized_message_count",
    "summary_updated_at",
    "summary_version",
)

_MESSAGE_FIELDS = (
    "id",
    "conversation_id",
    "role",
    "content",
    "outcome",
    "sources",
    "created_at",
)

_MAX_RECENT_MESSAGE_LIMIT = 10
_MAX_MESSAGE_WINDOW_LIMIT = 501


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

    def update(
        self,
        payload: Mapping[
            str,
            object,
        ],
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

    def limit(
        self,
        count: int,
    ) -> Self: ...

    def range(
        self,
        start: int,
        end: int,
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


class StudyConversationRepository:
    """Reads and persists owned Study Assistant conversations."""

    def __init__(
        self,
        client: _SupabaseClient,
    ) -> None:
        self._client = client

    def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str,
        subject_id: UUID | None,
        study_file_id: UUID | None,
    ) -> StudyConversationResponse:
        """Create and return one conversation."""

        payload: dict[
            str,
            object,
        ] = {
            "user_id": str(
                user_id,
            ),
            "title": title,
        }

        if subject_id is not None:
            payload[
                "subject_id"
            ] = str(
                subject_id,
            )

        if study_file_id is not None:
            payload[
                "study_file_id"
            ] = str(
                study_file_id,
            )

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .insert(
                payload,
            ),
            operation=(
                "create the conversation"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise StudyConversationResponseError(
                "The created conversation response "
                "was invalid.",
            )

        return self._parse_conversation(
            rows[0],
        )

    def list_conversations(
        self,
        *,
        user_id: UUID,
        limit: int,
    ) -> list[
        StudyConversationResponse
    ]:
        """List recent conversations belonging to one user."""

        if not 1 <= limit <= 50:
            raise StudyConversationValidationError(
                "Conversation list limit must be "
                "between 1 and 50.",
            )

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .select(
                _CONVERSATION_COLUMNS,
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .order(
                "last_message_at",
                desc=True,
            )
            .limit(
                limit,
            ),
            operation=(
                "list conversations"
            ),
        )

        return [
            self._parse_conversation(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]

    def get_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationResponse | None:
        """Return one owned conversation when it exists."""

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .select(
                _CONVERSATION_COLUMNS,
            )
            .eq(
                "id",
                str(
                    conversation_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .limit(
                1,
            ),
            operation=(
                "load the conversation"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise StudyConversationResponseError(
                "The conversation lookup response "
                "was invalid.",
            )

        return self._parse_conversation(
            rows[0],
        )

    def get_summary_state(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> StudyConversationSummaryState | None:
        """Load internal summary state for one owned conversation."""

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .select(
                _SUMMARY_COLUMNS,
            )
            .eq(
                "id",
                str(
                    conversation_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            )
            .limit(
                1,
            ),
            operation=(
                "load the conversation summary"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise StudyConversationResponseError(
                "The conversation summary response "
                "was invalid.",
            )

        return self._parse_summary_state(
            rows[0],
        )

    def save_summary_state(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        update: StudyConversationSummaryUpdate,
    ) -> StudyConversationSummaryState | None:
        """Persist validated summary state for an owned conversation."""

        if not isinstance(
            update,
            StudyConversationSummaryUpdate,
        ):
            raise StudyConversationValidationError(
                "The conversation summary update is invalid.",
            )

        summary_updated_at = datetime.now(
            UTC,
        )

        payload: dict[
            str,
            object,
        ] = {
            "summary_text": update.summary_text,
            "summarized_message_count": (
                update.summarized_message_count
            ),
            "summary_updated_at": (
                summary_updated_at.isoformat()
            ),
            "summary_version": update.summary_version,
        }

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .update(
                payload,
            )
            .eq(
                "id",
                str(
                    conversation_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            ),
            operation=(
                "save the conversation summary"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise StudyConversationResponseError(
                "The saved conversation summary response "
                "was invalid.",
            )

        return self._parse_summary_state(
            rows[0],
        )

    def list_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = 200,
    ) -> list[
        StudyMessageResponse
    ]:
        """Load saved messages in chronological order."""

        if not 1 <= limit <= 500:
            raise StudyConversationValidationError(
                "Message list limit must be between "
                "1 and 500.",
            )

        response = self._execute(
            self._client
            .table(
                "study_messages",
            )
            .select(
                _MESSAGE_COLUMNS,
            )
            .eq(
                "conversation_id",
                str(
                    conversation_id,
                ),
            )
            .order(
                "created_at",
            )
            .order(
                "id",
            )
            .limit(
                limit,
            ),
            operation=(
                "load conversation messages"
            ),
        )

        return [
            self._parse_message(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]

    def list_messages_from_offset(
        self,
        *,
        conversation_id: UUID,
        offset: int,
        limit: int = _MAX_MESSAGE_WINDOW_LIMIT,
    ) -> list[
        StudyMessageResponse
    ]:
        """Load a chronological message window from one offset."""

        if (
            isinstance(
                offset,
                bool,
            )
            or not isinstance(
                offset,
                int,
            )
            or offset < 0
        ):
            raise StudyConversationValidationError(
                "Message offset must be a non-negative integer.",
            )

        if not 1 <= limit <= _MAX_MESSAGE_WINDOW_LIMIT:
            raise StudyConversationValidationError(
                "Message window limit must be between "
                f"1 and {_MAX_MESSAGE_WINDOW_LIMIT}.",
            )

        response = self._execute(
            self._client
            .table(
                "study_messages",
            )
            .select(
                _MESSAGE_COLUMNS,
            )
            .eq(
                "conversation_id",
                str(
                    conversation_id,
                ),
            )
            .order(
                "created_at",
            )
            .order(
                "id",
            )
            .range(
                offset,
                offset + limit - 1,
            ),
            operation=(
                "load a conversation message window"
            ),
        )

        return [
            self._parse_message(
                row,
            )
            for row in self._extract_rows(
                response,
            )
        ]

    def list_recent_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = _MAX_RECENT_MESSAGE_LIMIT,
    ) -> list[
        StudyMessageResponse
    ]:
        """Load the newest messages in chronological order.

        The caller must verify conversation ownership before using
        this method because the trusted backend client can bypass RLS.
        """

        if not 1 <= limit <= _MAX_RECENT_MESSAGE_LIMIT:
            raise StudyConversationValidationError(
                "Recent message limit must be between "
                f"1 and {_MAX_RECENT_MESSAGE_LIMIT}.",
            )

        response = self._execute(
            self._client
            .table(
                "study_messages",
            )
            .select(
                _MESSAGE_COLUMNS,
            )
            .eq(
                "conversation_id",
                str(
                    conversation_id,
                ),
            )
            .order(
                "created_at",
                desc=True,
            )
            .order(
                "id",
                desc=True,
            )
            .limit(
                limit,
            ),
            operation=(
                "load recent conversation messages"
            ),
        )

        newest_first_rows = self._extract_rows(
            response,
        )

        chronological_rows = reversed(
            newest_first_rows,
        )

        return [
            self._parse_message(
                row,
            )
            for row in chronological_rows
        ]

    def save_user_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
    ) -> StudyMessageResponse:
        """Save and return one user message."""

        return self._insert_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            outcome=None,
            sources=(),
        )

    def save_assistant_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
        outcome: StudyMessageOutcome,
        sources: Sequence[
            StudyMessageSourceResponse
        ],
    ) -> StudyMessageResponse:
        """Save and return one assistant message."""

        if outcome not in (
            "answered",
            "no_context",
        ):
            raise StudyConversationValidationError(
                "Assistant message outcome is invalid.",
            )

        if (
            outcome == "answered"
            and not sources
        ):
            raise StudyConversationValidationError(
                "An answered assistant message "
                "requires sources.",
            )

        if (
            outcome == "no_context"
            and sources
        ):
            raise StudyConversationValidationError(
                "A no-context assistant message "
                "must not include sources.",
            )

        return self._insert_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            outcome=outcome,
            sources=sources,
        )

    def update_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        updates: Mapping[
            str,
            object,
        ],
    ) -> StudyConversationResponse | None:
        """Update one owned conversation."""

        allowed_fields = {
            "title",
            "subject_id",
            "study_file_id",
        }

        unexpected_fields = (
            set(
                updates,
            )
            - allowed_fields
        )

        if unexpected_fields:
            raise StudyConversationValidationError(
                "Conversation update contains "
                "unsupported fields.",
            )

        if not updates:
            raise StudyConversationValidationError(
                "Conversation update must contain "
                "at least one field.",
            )

        payload = {
            key: self._to_json_value(
                value,
            )
            for key, value in updates.items()
        }

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .update(
                payload,
            )
            .eq(
                "id",
                str(
                    conversation_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            ),
            operation=(
                "update the conversation"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        if not rows:
            return None

        if len(rows) != 1:
            raise StudyConversationResponseError(
                "The updated conversation response "
                "was invalid.",
            )

        return self._parse_conversation(
            rows[0],
        )

    def delete_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        """Delete one owned conversation."""

        response = self._execute(
            self._client
            .table(
                "study_conversations",
            )
            .delete()
            .eq(
                "id",
                str(
                    conversation_id,
                ),
            )
            .eq(
                "user_id",
                str(
                    user_id,
                ),
            ),
            operation=(
                "delete the conversation"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        return bool(
            rows,
        )

    def _insert_message(
        self,
        *,
        conversation_id: UUID,
        role: StudyMessageRole,
        content: str,
        outcome: StudyMessageOutcome | None,
        sources: Sequence[
            StudyMessageSourceResponse
        ],
    ) -> StudyMessageResponse:
        """Insert and validate one persisted message."""

        normalized_content = content.strip()

        if not normalized_content:
            raise StudyConversationValidationError(
                "Message content must not be blank.",
            )

        if len(normalized_content) > 50000:
            raise StudyConversationValidationError(
                "Message content must not exceed "
                "50000 characters.",
            )

        source_payloads = [
            source.model_dump(
                mode="json",
            )
            for source in sources
        ]

        payload: dict[
            str,
            object,
        ] = {
            "conversation_id": str(
                conversation_id,
            ),
            "role": role,
            "content": normalized_content,
            "outcome": outcome,
            "sources": source_payloads,
        }

        response = self._execute(
            self._client
            .table(
                "study_messages",
            )
            .insert(
                payload,
            ),
            operation=(
                "save the message"
            ),
        )

        rows = self._extract_rows(
            response,
        )

        if len(rows) != 1:
            raise StudyConversationResponseError(
                "The saved message response "
                "was invalid.",
            )

        return self._parse_message(
            rows[0],
        )

    @staticmethod
    def _execute(
        query: _SupabaseQuery,
        *,
        operation: str,
    ) -> _SupabaseResponse:
        try:
            return query.execute()
        except Exception as exc:
            raise StudyConversationPersistenceError(
                "The database could not "
                f"{operation}.",
            ) from exc

    @staticmethod
    def _extract_rows(
        response: _SupabaseResponse,
    ) -> list[
        Mapping[
            str,
            object,
        ]
    ]:
        response_data = getattr(
            response,
            "data",
            None,
        )

        if response_data is None:
            return []

        if not isinstance(
            response_data,
            list,
        ):
            raise StudyConversationResponseError(
                "The database returned an invalid "
                "conversation response.",
            )

        rows: list[
            Mapping[
                str,
                object,
            ]
        ] = []

        for row in response_data:
            if not isinstance(
                row,
                Mapping,
            ):
                raise StudyConversationResponseError(
                    "The database returned an invalid "
                    "conversation row.",
                )

            rows.append(
                row,
            )

        return rows

    @staticmethod
    def _parse_conversation(
        row: Mapping[
            str,
            object,
        ],
    ) -> StudyConversationResponse:
        safe_row = {
            field_name: row.get(
                field_name,
            )
            for field_name in _CONVERSATION_FIELDS
        }

        try:
            return (
                StudyConversationResponse
                .model_validate(
                    safe_row,
                )
            )
        except (
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            raise StudyConversationResponseError(
                "The database returned malformed "
                "conversation data.",
            ) from exc

    @staticmethod
    def _parse_summary_state(
        row: Mapping[
            str,
            object,
        ],
    ) -> StudyConversationSummaryState:
        safe_row: dict[
            str,
            object,
        ] = {
            "conversation_id": row.get(
                "id",
            ),
        }

        safe_row.update(
            {
                field_name: row.get(
                    field_name,
                )
                for field_name in _SUMMARY_FIELDS
            }
        )

        try:
            return (
                StudyConversationSummaryState
                .model_validate(
                    safe_row,
                )
            )
        except (
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            raise StudyConversationResponseError(
                "The database returned malformed "
                "conversation-summary data.",
            ) from exc

    @staticmethod
    def _parse_message(
        row: Mapping[
            str,
            object,
        ],
    ) -> StudyMessageResponse:
        safe_row = {
            field_name: row.get(
                field_name,
            )
            for field_name in _MESSAGE_FIELDS
        }

        try:
            return (
                StudyMessageResponse
                .model_validate(
                    safe_row,
                )
            )
        except (
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            raise StudyConversationResponseError(
                "The database returned malformed "
                "message data.",
            ) from exc

    @staticmethod
    def _to_json_value(
        value: object,
    ) -> object:
        if isinstance(
            value,
            UUID,
        ):
            return str(
                value,
            )

        return value