# File: /backend/tests/test_flashcard_review_migration.py
# Purpose: Protects the Flashcard review-event database foundation.

from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260811162000_create_flashcard_review_events.sql"
)


def test_flashcard_review_migration_has_secure_foundation() -> None:
    """Review events must enforce ownership, outcomes, and RLS."""

    sql = MIGRATION.read_text(
        encoding="utf-8",
    ).lower()

    assert (
        "create table public.flashcard_review_events"
        in sql
    )

    assert "user_id uuid not null" in sql
    assert "deck_id uuid not null" in sql
    assert "card_position integer not null" in sql

    assert "'known'" in sql
    assert "'review_again'" in sql

    assert (
        "validate_flashcard_review_event_scope"
        in sql
    )

    assert (
        "enable row level security"
        in sql
    )

    assert (
        'create policy "flashcard_review_events_select_own"'
        in sql
    )

    assert (
        "auth.uid() = user_id"
        in sql
    )

    assert (
        "grant all"
        in sql
    )

    assert (
        "to service_role"
        in sql
    )