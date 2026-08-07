# File: /backend/tests/test_study_conversation_summary_migration.py
# Purpose: Prevents regression in the bounded internal
# conversation-summary database state.

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = (
    Path(
        __file__,
    ).resolve().parents[2]
    / "supabase"
    / "migrations"
    / (
        "20260806223000_"
        "add_study_conversation_summary_state.sql"
    )
)


def migration_text() -> str:
    """Load the summary-state migration."""

    return MIGRATION_PATH.read_text(
        encoding="utf-8-sig",
    ).lower()


def test_summary_migration_adds_required_columns() -> None:
    sql = migration_text()

    for column_name in (
        "summary_text",
        "summarized_message_count",
        "summary_updated_at",
        "summary_version",
    ):
        assert column_name in sql


def test_summary_migration_enforces_bounded_state() -> None:
    sql = migration_text()

    assert "between 1 and 4000" in sql
    assert "summarized_message_count >= 0" in sql
    assert "summary_version between 1 and 100" in sql
    assert "study_conversations_summary_state_check" in sql


def test_summary_migration_documents_non_evidence_use() -> None:
    sql = migration_text()

    assert "not factual study evidence" in sql