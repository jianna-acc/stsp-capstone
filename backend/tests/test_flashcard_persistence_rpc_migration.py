# File: /backend/tests/test_flashcard_persistence_rpc_migration.py
# Purpose: Verifies the atomic trusted database function used
# to save generated Flashcard decks and their ordered cards.

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260809145600_create_flashcard_persistence_rpc.sql"
)


def _migration_sql() -> str:
    """Return normalized Flashcard persistence RPC SQL."""

    assert MIGRATION_PATH.exists(), (
        "Flashcard persistence RPC migration does not exist."
    )

    return " ".join(
        MIGRATION_PATH.read_text(
            encoding="utf-8",
        )
        .lower()
        .split()
    )


def test_flashcard_persistence_rpc_migration_exists() -> None:
    """Atomic Flashcard persistence needs its own migration."""

    assert MIGRATION_PATH.exists()


def test_create_flashcard_deck_rpc_exists() -> None:
    """Migration must create the trusted persistence function."""

    sql = _migration_sql()

    assert (
        "create or replace function "
        "public.create_flashcard_deck_with_cards"
        in sql
    )

    assert "returns uuid" in sql
    assert "language plpgsql" in sql


def test_rpc_accepts_deck_and_card_data() -> None:
    """RPC must receive all generated persistence data."""

    sql = _migration_sql()

    required_arguments = (
        "p_user_id uuid",
        "p_subject_id uuid",
        "p_study_file_id uuid",
        "p_scope_type text",
        "p_title text",
        "p_requested_card_count integer",
        "p_sources jsonb",
        "p_generation_model text",
        "p_cards jsonb",
    )

    for argument in required_arguments:
        assert argument in sql


def test_rpc_validates_cards_as_array() -> None:
    """Generated card payload must be a JSON array."""

    sql = _migration_sql()

    assert "jsonb_typeof(p_cards)" in sql
    assert "'array'" in sql


def test_rpc_requires_requested_card_count() -> None:
    """Saved generated card count must match the request."""

    sql = _migration_sql()

    assert (
        "jsonb_array_length(p_cards) "
        "<> p_requested_card_count"
        in sql
    )


def test_rpc_inserts_flashcard_deck() -> None:
    """RPC must create the parent deck first."""

    sql = _migration_sql()

    assert "insert into public.flashcard_decks" in sql

    required_columns = (
        "user_id",
        "subject_id",
        "study_file_id",
        "scope_type",
        "title",
        "requested_card_count",
        "sources",
        "generation_model",
    )

    for column in required_columns:
        assert column in sql

    assert "returning id" in sql


def test_rpc_inserts_ordered_flashcards() -> None:
    """RPC must persist individual cards in generation order."""

    sql = _migration_sql()

    assert "insert into public.flashcards" in sql
    assert "deck_id" in sql
    assert "position" in sql
    assert "question" in sql
    assert "answer" in sql

    assert "jsonb_array_elements" in sql
    assert "with ordinality" in sql


def test_card_positions_start_at_zero() -> None:
    """Stored card positions must be zero-based."""

    sql = _migration_sql()

    assert "ordinality - 1" in sql


def test_rpc_returns_created_deck_id() -> None:
    """Backend needs the created deck ID for retrieval."""

    sql = _migration_sql()

    assert "return v_deck_id" in sql


def test_rpc_is_security_definer() -> None:
    """Generated persistence must execute as trusted backend work."""

    sql = _migration_sql()

    assert "security definer" in sql
    assert "set search_path = public, pg_temp" in sql


def test_rpc_is_not_executable_by_browser_roles() -> None:
    """Browser roles must not call generated persistence directly."""

    sql = _migration_sql()

    assert (
        "revoke execute on function "
        "public.create_flashcard_deck_with_cards"
        in sql
    )

    assert "from public" in sql
    assert "from anon" in sql
    assert "from authenticated" in sql


def test_service_role_can_execute_rpc() -> None:
    """Only trusted backend service role should receive execution."""

    sql = _migration_sql()

    assert (
        "grant execute on function "
        "public.create_flashcard_deck_with_cards"
        in sql
    )

    assert "to service_role" in sql