# File: /backend/tests/test_ai_vector_migration.py
# Purpose: Verifies the Phase 4D vector-schema migration contract
# without requiring Docker or changing the remote database.

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIRECTORY = REPOSITORY_ROOT / "supabase" / "migrations"

MIGRATION_FILES = tuple(
    MIGRATIONS_DIRECTORY.glob(
        "*_create_ai_chunk_vector_foundation.sql",
    ),
)


def load_migration_sql() -> str:
    """Return normalized Phase 4D migration SQL."""

    assert len(MIGRATION_FILES) == 1

    sql = (
        MIGRATION_FILES[0]
        .read_text(
            encoding="utf-8-sig",
        )
        .lower()
    )

    return re.sub(
        r"\s+",
        " ",
        sql,
    )


def test_vector_migration_exists_once() -> None:
    """The vector foundation must have one migration file."""

    assert len(MIGRATION_FILES) == 1

    assert MIGRATION_FILES[0].name.endswith(
        "_create_ai_chunk_vector_foundation.sql",
    )


def test_migration_enables_vector_extension() -> None:
    """The migration must enable pgvector in extensions."""

    sql = load_migration_sql()

    assert ("create extension if not exists vector with schema extensions;") in sql


def test_migration_creates_fixed_dimension_ai_table() -> None:
    """AI chunks must use a separate 768-dimensional table."""

    sql = load_migration_sql()

    assert ("create table public.study_file_ai_chunks") in sql

    assert ("embedding extensions.vector(768) not null") in sql

    assert ("unique ( study_file_id, chunk_index )") in sql


def test_migration_adds_cosine_hnsw_index() -> None:
    """The embedding column must have a cosine HNSW index."""

    sql = load_migration_sql()

    assert "using hnsw" in sql

    assert ("embedding extensions.vector_cosine_ops") in sql


def test_migration_uses_owner_only_read_access() -> None:
    """Students may read only their own stored AI chunks."""

    sql = load_migration_sql()

    assert ("alter table public.study_file_ai_chunks enable row level security") in sql

    assert ("create policy study_file_ai_chunks_select_own") in sql

    assert ("grant select on table public.study_file_ai_chunks to authenticated") in sql


def test_persistence_rpc_is_service_role_only() -> None:
    """Embedding writes must remain backend-only."""

    sql = load_migration_sql()

    assert ("create or replace function public.replace_study_file_ai_chunks") in sql

    assert "security definer" in sql
    assert "set search_path = ''" in sql

    assert ("grant execute on function public.replace_study_file_ai_chunks") in sql

    assert "to service_role" in sql


def test_persistence_rpc_requires_active_indexing() -> None:
    """The RPC must require the active processing state."""

    sql = load_migration_sql()

    assert ("study_files.processing_status = 'indexing'") in sql

    assert ("file_processing_jobs.status = 'processing'") in sql


def test_persistence_rpc_is_idempotent() -> None:
    """Retries must update rows and remove stale chunks."""

    sql = load_migration_sql()

    assert ("on conflict ( study_file_id, chunk_index ) do update") in sql

    assert ("delete from public.study_file_ai_chunks") in sql

    assert ("chunk_index >= v_expected_chunk_index") in sql
