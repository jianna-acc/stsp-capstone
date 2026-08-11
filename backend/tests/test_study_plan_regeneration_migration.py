# File: /backend/tests/test_study_plan_regeneration_migration.py
# Purpose: Verifies the Track D regeneration migration preserves
# manual sessions and restricts its privileged RPC to service_role.

from pathlib import Path

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260811002500_add_study_plan_regeneration_rpc.sql"
)


def _migration_sql() -> str:
    return (
        _MIGRATION_PATH
        .read_text(
            encoding="utf-8",
        )
        .lower()
    )


def test_regeneration_rpc_replaces_only_generated_sessions() -> None:
    sql = _migration_sql()

    assert (
        "origin = 'generated'"
        in sql
    )

    assert (
        "origin = 'manual'"
        in sql
    )

    assert (
        "delete from public.study_sessions"
        in sql
    )


def test_regeneration_rpc_keeps_same_study_plan() -> None:
    sql = _migration_sql()

    assert (
        "update public.study_plans"
        in sql
    )

    assert (
        "set generated_at"
        in sql
    )

    assert (
        "delete from public.study_plans"
        not in sql
    )


def test_regeneration_rpc_is_service_role_only() -> None:
    sql = _migration_sql()

    assert (
        "to service_role"
        in sql
    )

    assert (
        "from authenticated"
        in sql
    )