# File: /backend/tests/test_flashcard_migration.py
# Purpose: Verifies the Flashcard persistence migration,
# ownership validation, constraints, privileges, and RLS.

from __future__ import annotations

from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260809142000_create_flashcard_foundation.sql"
)


def _migration_sql() -> str:
    """Return normalized Flashcard migration SQL."""

    assert MIGRATION_PATH.exists(), (
        "Flashcard foundation migration does not exist."
    )

    return " ".join(
        MIGRATION_PATH.read_text(
            encoding="utf-8",
        )
        .lower()
        .split()
    )


def test_flashcard_foundation_migration_exists() -> None:
    """Flashcard persistence must have its own migration."""

    assert MIGRATION_PATH.exists()


def test_migration_creates_deck_and_card_tables() -> None:
    """Flashcards use one deck table and one child-card table."""

    sql = _migration_sql()

    assert "create table public.flashcard_decks" in sql
    assert "create table public.flashcards" in sql


def test_deck_references_owner_subject_and_file() -> None:
    """Deck scope must remain tied to owned study material."""

    sql = _migration_sql()

    assert "references auth.users(id)" in sql
    assert "references public.subjects(id)" in sql
    assert "references public.study_files(id)" in sql

    assert "on delete cascade" in sql


def test_deck_scope_constraints_exist() -> None:
    """Subject/file scope must be database-enforced."""

    sql = _migration_sql()

    assert "flashcard_decks_scope_type_check" in sql
    assert "scope_type in ( 'subject', 'file' )" in sql

    assert "flashcard_decks_scope_file_check" in sql

    assert (
        "scope_type = 'file' and study_file_id is not null"
        in sql
    )

    assert (
        "scope_type = 'subject' and study_file_id is null"
        in sql
    )


def test_requested_card_count_is_bounded() -> None:
    """Deck requests must stay within the public schema limits."""

    sql = _migration_sql()

    assert "requested_card_count integer not null" in sql
    assert "flashcard_decks_requested_card_count_check" in sql

    assert (
        "requested_card_count between 5 and 50"
        in sql
    )


def test_deck_generation_metadata_is_validated() -> None:
    """Generated decks must keep safe generation metadata."""

    sql = _migration_sql()

    assert "sources jsonb not null" in sql
    assert "jsonb_typeof(sources) = 'array'" in sql

    assert "generation_model text not null" in sql
    assert "generation_count integer not null" in sql

    assert "generation_count >= 1" in sql
    assert "generated_at timestamptz not null" in sql


def test_flashcards_belong_to_deck_with_stable_position() -> None:
    """Each generated card must belong to one ordered deck."""

    sql = _migration_sql()

    assert "deck_id uuid not null" in sql

    assert (
        "references public.flashcard_decks(id)"
        in sql
    )

    assert "position integer not null" in sql
    assert "position >= 0" in sql

    assert "question text not null" in sql
    assert "answer text not null" in sql

    assert (
        "unique ( deck_id, position )"
        in sql
    )


def test_flashcard_text_constraints_exist() -> None:
    """Empty or excessively large card text must be rejected."""

    sql = _migration_sql()

    assert "flashcards_question_check" in sql
    assert "flashcards_answer_check" in sql

    assert "between 1 and 2000" in sql
    assert "between 1 and 4000" in sql


def test_flashcard_indexes_exist() -> None:
    """Common deck and ordered-card queries need indexes."""

    sql = _migration_sql()

    assert "flashcard_decks_user_created_at_idx" in sql
    assert "flashcard_decks_user_subject_idx" in sql
    assert "flashcard_decks_user_study_file_idx" in sql

    assert "flashcards_deck_position_idx" in sql


def test_deck_ownership_validation_trigger_exists() -> None:
    """Database must verify selected subject/file ownership."""

    sql = _migration_sql()

    assert (
        "validate_flashcard_deck_ownership_scope"
        in sql
    )

    assert (
        "flashcard_decks_validate_ownership_scope"
        in sql
    )

    assert (
        "before insert or update of user_id, subject_id, "
        "study_file_id, scope_type"
        in sql
    )

    assert (
        "from public.subjects where id = new.subject_id "
        "and user_id = new.user_id"
        in sql
    )

    assert (
        "from public.study_files where id = "
        "new.study_file_id and user_id = new.user_id "
        "and subject_id = new.subject_id"
        in sql
    )


def test_deck_updated_at_trigger_exists() -> None:
    """Deck updates must refresh updated_at automatically."""

    sql = _migration_sql()

    assert "set_flashcard_deck_updated_at" in sql
    assert "flashcard_decks_set_updated_at" in sql
    assert "new.updated_at = now()" in sql


def test_rls_is_enabled_for_both_tables() -> None:
    """Both Flashcard tables must be protected by RLS."""

    sql = _migration_sql()

    assert (
        "alter table public.flashcard_decks "
        "enable row level security"
        in sql
    )

    assert (
        "alter table public.flashcards "
        "enable row level security"
        in sql
    )


def test_authenticated_privileges_are_read_delete_only() -> None:
    """Browser clients must not directly create generated data."""

    sql = _migration_sql()

    assert (
        "grant select, delete on table "
        "public.flashcard_decks to authenticated"
        in sql
    )

    assert (
        "grant select on table "
        "public.flashcards to authenticated"
        in sql
    )

    assert (
        "grant all on table "
        "public.flashcard_decks to service_role"
        in sql
    )

    assert (
        "grant all on table "
        "public.flashcards to service_role"
        in sql
    )


def test_deck_owner_policies_exist() -> None:
    """Students may read and delete only their own decks."""

    sql = _migration_sql()

    assert '"flashcard_decks_select_own"' in sql
    assert '"flashcard_decks_delete_own"' in sql

    assert "auth.uid() = user_id" in sql


def test_card_select_policy_uses_parent_deck_owner() -> None:
    """Students may read cards only through owned decks."""

    sql = _migration_sql()

    assert '"flashcards_select_owned_deck"' in sql

    assert (
        "from public.flashcard_decks"
        in sql
    )

    assert (
        "flashcard_decks.id = flashcards.deck_id"
        in sql
    )

    assert (
        "flashcard_decks.user_id = auth.uid()"
        in sql
    )