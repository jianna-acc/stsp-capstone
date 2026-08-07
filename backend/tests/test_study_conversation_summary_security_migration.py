# File: /backend/tests/test_study_conversation_summary_security_migration.py
# Purpose: Ensures authenticated clients cannot directly alter
# backend-managed conversation-summary state.

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = (
    Path(
        __file__,
    ).resolve().parents[2]
    / "supabase"
    / "migrations"
    / (
        "20260806234000_"
        "restrict_study_conversation_summary_updates.sql"
    )
)


def migration_text() -> str:
    """Return normalized migration SQL."""

    raw_sql = MIGRATION_PATH.read_text(
        encoding="utf-8-sig",
    ).lower()

    return " ".join(
        raw_sql.split(),
    )


def authenticated_update_columns(
    sql: str,
) -> str:
    """Extract the authenticated column-level update grant."""

    grant_start = sql.index(
        "grant update (",
    )

    grant_end = sql.index(
        ") on table public.study_conversations "
        "to authenticated;",
        grant_start,
    )

    return sql[
        grant_start:
        grant_end
    ]


def test_authenticated_table_update_is_revoked() -> None:
    sql = migration_text()

    assert (
        "revoke update on table "
        "public.study_conversations "
        "from authenticated;"
    ) in sql


def test_authenticated_update_is_limited_to_metadata() -> None:
    sql = migration_text()

    allowed_grant = authenticated_update_columns(
        sql,
    )

    for allowed_column in (
        "title",
        "subject_id",
        "study_file_id",
    ):
        assert allowed_column in allowed_grant

    for internal_column in (
        "summary_text",
        "summarized_message_count",
        "summary_updated_at",
        "summary_version",
        "user_id",
        "last_message_at",
    ):
        assert internal_column not in allowed_grant


def test_service_role_preserves_backend_update_access() -> None:
    sql = migration_text()

    assert (
        "grant update on table "
        "public.study_conversations "
        "to service_role;"
    ) in sql


def test_migration_documents_backend_managed_state() -> None:
    sql = migration_text()

    assert "backend-managed" in sql
