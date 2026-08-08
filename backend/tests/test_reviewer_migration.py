# File: /backend/tests/test_reviewer_migration.py
# Purpose: Verifies the Phase 6A reviewer database migration contract.

from pathlib import Path

ROOT = Path(
    __file__,
).resolve().parents[2]

MIGRATION_PATH = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260808053929_create_reviewers_foundation.sql"
)


def _migration_sql() -> str:
    """Load the reviewer foundation migration."""

    return MIGRATION_PATH.read_text(
        encoding="utf-8",
    ).lower()


def test_reviewer_migration_exists_and_is_not_empty() -> None:
    """The real reviewer migration must exist locally."""

    assert MIGRATION_PATH.exists()

    assert (
        MIGRATION_PATH.stat().st_size
        > 0
    )


def test_reviewer_migration_creates_reviewers_table() -> None:
    """The migration must create reviewer persistence."""

    sql = _migration_sql()

    assert (
        "create table public.reviewers"
        in sql
    )


def test_reviewer_migration_has_required_columns() -> None:
    """Core reviewer fields must be represented."""

    sql = _migration_sql()

    required_columns = (
        "user_id uuid not null",
        "subject_id uuid not null",
        "study_file_id uuid",
        "scope_type text not null",
        "title text not null",
        "reviewer_length text not null",
        "content jsonb not null",
        "sources jsonb not null",
        "generation_model text not null",
        "generation_count integer not null",
        "generated_at timestamptz not null",
        "created_at timestamptz not null",
        "updated_at timestamptz not null",
    )

    for column in required_columns:
        assert column in sql


def test_reviewer_migration_enforces_scope_rules() -> None:
    """Subject and file reviewer scopes must be constrained."""

    sql = _migration_sql()

    assert (
        "reviewers_scope_type_check"
        in sql
    )

    assert (
        "reviewers_scope_file_check"
        in sql
    )

    assert "'subject'" in sql
    assert "'file'" in sql


def test_reviewer_migration_enforces_content_contracts() -> None:
    """Structured content and source metadata must stay typed."""

    sql = _migration_sql()

    assert (
        "reviewers_content_object_check"
        in sql
    )

    assert (
        "jsonb_typeof(content) = 'object'"
        in sql
    )

    assert (
        "reviewers_sources_array_check"
        in sql
    )

    assert (
        "jsonb_typeof(sources) = 'array'"
        in sql
    )


def test_reviewer_migration_enforces_generation_count() -> None:
    """Generation count must remain positive."""

    sql = _migration_sql()

    assert (
        "reviewers_generation_count_check"
        in sql
    )

    assert (
        "generation_count >= 1"
        in sql
    )


def test_reviewer_migration_validates_source_ownership() -> None:
    """Reviewer subject/file ownership must be validated."""

    sql = _migration_sql()

    assert (
        "validate_reviewer_ownership_scope"
        in sql
    )

    assert (
        "reviewers_validate_ownership_scope"
        in sql
    )

    assert (
        "from public.subjects"
        in sql
    )

    assert (
        "from public.study_files"
        in sql
    )

    assert (
        "subject_id = new.subject_id"
        in sql
    )

    assert (
        "user_id = new.user_id"
        in sql
    )


def test_reviewer_migration_updates_timestamp() -> None:
    """Updates must refresh the reviewer timestamp."""

    sql = _migration_sql()

    assert (
        "set_reviewer_updated_at"
        in sql
    )

    assert (
        "reviewers_set_updated_at"
        in sql
    )

    assert (
        "new.updated_at = now()"
        in sql
    )


def test_reviewer_migration_enables_rls() -> None:
    """Reviewer records must be protected by RLS."""

    sql = _migration_sql()

    assert (
        "alter table public.reviewers"
        in sql
    )

    assert (
        "enable row level security"
        in sql
    )


def test_reviewer_migration_restricts_browser_writes() -> None:
    """Authenticated browsers may read/delete but not write reviewers."""

    sql = _migration_sql()

    assert (
        "revoke all"
        in sql
    )

    assert (
        "from authenticated"
        in sql
    )

    assert (
        "grant select, delete"
        in sql
    )

    assert (
        "to authenticated"
        in sql
    )


def test_reviewer_migration_has_owned_policies() -> None:
    """Read/delete policies must require authenticated ownership."""

    sql = _migration_sql()

    assert (
        '"reviewers_select_own"'
        in sql
    )

    assert (
        '"reviewers_delete_own"'
        in sql
    )

    assert (
        "auth.uid() = user_id"
        in sql
    )