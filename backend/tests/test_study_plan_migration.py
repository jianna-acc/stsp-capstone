# File: /backend/tests/test_study_plan_migration.py
# Purpose: Verifies the independent Track D study-plan database
# foundation, ownership protections, and security configuration.

import re
from pathlib import Path

_REPOSITORY_ROOT = Path(
    __file__,
).resolve().parents[2]

_MIGRATION_PATH = (
    _REPOSITORY_ROOT
    / "supabase"
    / "migrations"
    / "20260810002500_create_study_plans_foundation.sql"
)


def _migration_sql() -> str:
    """Return normalized Track D migration SQL."""

    sql = _MIGRATION_PATH.read_text(
        encoding="utf-8",
    )

    return re.sub(
        r"\s+",
        " ",
        sql.lower(),
    )


def test_study_plan_migration_exists() -> None:
    """Track D must provide its database foundation."""

    assert _MIGRATION_PATH.is_file()


def test_migration_creates_study_plan_tables() -> None:
    """Study plans and sessions must both be persistent."""

    sql = _migration_sql()

    assert (
        "create table public.study_plans"
        in sql
    )

    assert (
        "create table public.study_sessions"
        in sql
    )


def test_study_session_enforces_plan_ownership() -> None:
    """A session cannot reference another student's plan."""

    sql = _migration_sql()

    assert (
        "constraint study_sessions_plan_owner_fk"
        in sql
    )

    assert (
        "references public.study_plans ( id, user_id )"
        in sql
    )


def test_study_session_enforces_subject_ownership() -> None:
    """A session cannot reference another student's subject."""

    sql = _migration_sql()

    assert (
        "constraint study_sessions_subject_owner_fk"
        in sql
    )

    assert (
        "references public.subjects ( id, user_id )"
        in sql
    )


def test_migration_enables_row_level_security() -> None:
    """Both new tables must use Row Level Security."""

    sql = _migration_sql()

    assert (
        "alter table public.study_plans "
        "enable row level security"
        in sql
    )

    assert (
        "alter table public.study_sessions "
        "enable row level security"
        in sql
    )


def test_migration_defines_student_ownership_policies() -> None:
    """Authenticated students may only access owned rows."""

    sql = _migration_sql()

    assert "study_plans_select_own" in sql
    assert "study_plans_delete_own" in sql

    assert "study_sessions_select_own" in sql
    assert "study_sessions_delete_own" in sql

    assert (
        "user_id = (select auth.uid())"
        in sql
    )


def test_authenticated_students_cannot_write_directly() -> None:
    """Track D writes must pass through trusted backend services."""

    sql = _migration_sql()

    assert (
        "revoke all on table public.study_plans "
        "from authenticated"
        in sql
    )

    assert (
        "revoke all on table public.study_sessions "
        "from authenticated"
        in sql
    )

    assert (
        "grant select, delete "
        "on table public.study_plans "
        "to authenticated"
        in sql
    )

    assert (
        "grant select, delete "
        "on table public.study_sessions "
        "to authenticated"
        in sql
    )


def test_migration_is_independent_of_academic_tasks() -> None:
    """Track D foundation must not depend on unfinished Track C."""

    sql = _migration_sql()

    assert "academic_tasks" not in sql
    assert "academic_task_id" not in sql