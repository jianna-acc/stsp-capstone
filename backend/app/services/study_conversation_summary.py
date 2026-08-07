# File: /backend/app/services/study_conversation_summary.py
# Purpose: Builds a deterministic bounded summary from older
# Study Assistant conversation messages without an AI provider.

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final

from app.schemas.study_conversation import (
    MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS,
    StudyConversationSummaryState,
    StudyConversationSummaryUpdate,
    StudyMessageResponse,
)
from app.services.study_conversation_errors import (
    StudyConversationValidationError,
)

CONVERSATION_SUMMARY_VERSION: Final = 1

MAX_SUMMARY_ENTRY_CHARACTERS: Final = 600

SUMMARY_HEADER: Final = (
    "Earlier conversation summary "
    "(not factual study evidence):"
)

SUMMARY_TRUNCATION_MARKER: Final = (
    "[Earlier summary content was truncated "
    "to fit the summary limit.]"
)

MESSAGE_TRUNCATION_MARKER: Final = (
    " [Message shortened.]"
)

_SOURCE_MARKER_PATTERN: Final = re.compile(
    r"\[Source\s+\d+\]",
    flags=re.IGNORECASE,
)


def build_conversation_summary_update(
    *,
    state: StudyConversationSummaryState,
    messages: Sequence[
        StudyMessageResponse
    ],
) -> StudyConversationSummaryUpdate | None:
    """Build the next summary update from older messages."""

    if not isinstance(
        state,
        StudyConversationSummaryState,
    ):
        raise StudyConversationValidationError(
            "Conversation summary state is invalid.",
        )

    if (
        isinstance(
            messages,
            (
                str,
                bytes,
            ),
        )
        or not isinstance(
            messages,
            Sequence,
        )
    ):
        raise StudyConversationValidationError(
            "Summary messages must be a sequence.",
        )

    normalized_messages = tuple(
        messages,
    )

    if not all(
        isinstance(
            message,
            StudyMessageResponse,
        )
        for message in normalized_messages
    ):
        raise StudyConversationValidationError(
            "Every summary item must be a "
            "StudyMessageResponse.",
        )

    if not normalized_messages:
        return None

    if (
        state.summary_version
        != CONVERSATION_SUMMARY_VERSION
    ):
        raise StudyConversationValidationError(
            "The stored conversation summary version "
            "is not supported.",
        )

    mismatched_message = next(
        (
            message
            for message in normalized_messages
            if (
                message.conversation_id
                != state.conversation_id
            )
        ),
        None,
    )

    if mismatched_message is not None:
        raise StudyConversationValidationError(
            "A summary message does not belong to "
            "the resolved conversation.",
        )

    new_rows = tuple(
        _build_summary_row(
            message,
        )
        for message in normalized_messages
    )

    existing_body = _extract_existing_body(
        state.summary_text,
    )

    body_parts = [
        part
        for part in (
            existing_body,
            "\n".join(
                new_rows,
            ),
        )
        if part
    ]

    combined_body = "\n".join(
        body_parts,
    )

    bounded_summary = _bound_summary_text(
        combined_body,
    )

    return StudyConversationSummaryUpdate(
        summary_text=bounded_summary,
        summarized_message_count=(
            state.summarized_message_count
            + len(
                normalized_messages,
            )
        ),
        summary_version=CONVERSATION_SUMMARY_VERSION,
    )


def _build_summary_row(
    message: StudyMessageResponse,
) -> str:
    role_label = (
        "User"
        if message.role == "user"
        else "Assistant"
    )

    content = _normalize_summary_content(
        message.content,
    )

    if not content:
        content = "Content omitted."

    if (
        len(
            content,
        )
        > MAX_SUMMARY_ENTRY_CHARACTERS
    ):
        available_characters = (
            MAX_SUMMARY_ENTRY_CHARACTERS
            - len(
                MESSAGE_TRUNCATION_MARKER,
            )
        )

        content = (
            content[
                :available_characters
            ].rstrip()
            + MESSAGE_TRUNCATION_MARKER
        )

    return f"{role_label}: {content}"


def _normalize_summary_content(
    value: str,
) -> str:
    without_source_markers = (
        _SOURCE_MARKER_PATTERN.sub(
            "",
            value,
        )
    )

    normalized_newlines = (
        without_source_markers
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
    )

    return " ".join(
        normalized_newlines.split(),
    )


def _extract_existing_body(
    summary_text: str | None,
) -> str:
    if summary_text is None:
        return ""

    normalized_summary = summary_text.strip()

    if normalized_summary.startswith(
        SUMMARY_HEADER,
    ):
        return normalized_summary[
            len(
                SUMMARY_HEADER,
            ):
        ].lstrip()

    return normalized_summary


def _bound_summary_text(
    body: str,
) -> str:
    full_summary = (
        f"{SUMMARY_HEADER}\n"
        f"{body}"
    ).strip()

    if (
        len(
            full_summary,
        )
        <= MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
    ):
        return full_summary

    available_body_characters = (
        MAX_STUDY_CONVERSATION_SUMMARY_CHARACTERS
        - len(
            SUMMARY_HEADER,
        )
        - len(
            SUMMARY_TRUNCATION_MARKER,
        )
        - 2
    )

    selected_newest_lines: list[
        str
    ] = []

    selected_character_count = 0

    for line in reversed(
        body.splitlines(),
    ):
        normalized_line = line.strip()

        if not normalized_line:
            continue

        separator_characters = (
            1
            if selected_newest_lines
            else 0
        )

        required_characters = (
            len(
                normalized_line,
            )
            + separator_characters
        )

        if (
            selected_character_count
            + required_characters
            > available_body_characters
        ):
            break

        selected_newest_lines.append(
            normalized_line,
        )

        selected_character_count += (
            required_characters
        )

    selected_newest_lines.reverse()

    retained_body = "\n".join(
        selected_newest_lines,
    )

    bounded_summary = (
        f"{SUMMARY_HEADER}\n"
        f"{SUMMARY_TRUNCATION_MARKER}"
    )

    if retained_body:
        bounded_summary = (
            f"{bounded_summary}\n"
            f"{retained_body}"
        )

    return bounded_summary