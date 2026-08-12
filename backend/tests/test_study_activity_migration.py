# File: /backend/tests/test_study_activity_migration.py
# Purpose: Protects the Study Activity timer migrations,
# security boundary, state model, and trusted transition RPCs.

from pathlib import Path

BASE_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260812060559_create_study_activity_sessions.sql"
)

TIMED_BREAKS_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260812142227_add_timed_study_breaks.sql"
)


def _migration_sql(
    path: Path,
) -> str:
    return path.read_text(
        encoding="utf-8",
    ).lower()


def test_study_activity_migration_exists() -> None:
    assert BASE_MIGRATION_PATH.is_file()


def test_study_activity_migration_creates_actual_activity_table() -> None:
    sql = _migration_sql(
        BASE_MIGRATION_PATH,
    )

    assert (
        "create table public.study_activity_sessions"
        in sql
    )
    assert "focus_seconds integer not null" in sql
    assert "break_seconds integer not null" in sql
    assert "segment_started_at timestamptz" in sql
    assert "'running'" in sql
    assert "'paused'" in sql
    assert "'completed'" in sql
    assert "'focus'" in sql
    assert "'break'" in sql


def test_study_activity_migration_limits_one_unfinished_timer() -> None:
    sql = _migration_sql(
        BASE_MIGRATION_PATH,
    )

    assert (
        "study_activity_sessions_one_active_per_user_idx"
        in sql
    )
    assert "where status in" in sql
    assert "'running'" in sql
    assert "'paused'" in sql


def test_study_activity_migration_uses_trusted_atomic_transitions() -> None:
    sql = _migration_sql(
        BASE_MIGRATION_PATH,
    )

    assert (
        "public.transition_study_activity_session"
        in sql
    )
    assert "security definer" in sql
    assert "focus_seconds =" in sql
    assert "break_seconds =" in sql
    assert "p_action = 'pause'" in sql
    assert "p_action = 'resume'" in sql
    assert "p_action = 'start_break'" in sql
    assert "p_action = 'end_break'" in sql
    assert "p_action = 'complete'" in sql


def test_study_activity_migration_restricts_browser_mutation() -> None:
    sql = _migration_sql(
        BASE_MIGRATION_PATH,
    )

    assert (
        "revoke all\n"
        "on table public.study_activity_sessions\n"
        "from authenticated"
        in sql
    )
    assert (
        "grant select\n"
        "on table public.study_activity_sessions\n"
        "to authenticated"
        in sql
    )
    assert (
        "grant all\n"
        "on table public.study_activity_sessions\n"
        "to service_role"
        in sql
    )
    assert (
        "grant execute\n"
        "on function public.transition_study_activity_session"
        in sql
    )
    assert "to service_role" in sql


def test_study_activity_migration_enables_owner_scoped_rls() -> None:
    sql = _migration_sql(
        BASE_MIGRATION_PATH,
    )

    assert (
        "alter table public.study_activity_sessions\n"
        "enable row level security"
        in sql
    )
    assert "study_activity_sessions_select_own" in sql
    assert (
        "user_id = (\n"
        "        select auth.uid()\n"
        "    )"
        in sql
    )


def test_study_activity_migration_validates_schedule_target() -> None:
    sql = _migration_sql(
        BASE_MIGRATION_PATH,
    )

    assert "validate_study_activity_start_target" in sql
    assert "study activity subject is not owned" in sql
    assert "study activity plan is not owned" in sql
    assert "scheduled session is not owned" in sql
    assert (
        "plan does not match its scheduled session"
        in sql
    )
    assert (
        "subject does not match its scheduled session"
        in sql
    )


def test_timed_breaks_migration_exists() -> None:
    assert TIMED_BREAKS_MIGRATION_PATH.is_file()


def test_timed_breaks_migration_adds_persisted_deadline() -> None:
    sql = _migration_sql(
        TIMED_BREAKS_MIGRATION_PATH,
    )

    assert "break_ends_at timestamptz" in sql
    assert (
        "study_activity_sessions_break_deadline_state_check"
        in sql
    )
    assert "break_ends_at is not null" in sql
    assert "break_ends_at is null" in sql


def test_timed_breaks_migration_creates_duration_aware_rpc() -> None:
    sql = _migration_sql(
        TIMED_BREAKS_MIGRATION_PATH,
    )

    assert (
        "public.start_timed_study_activity_break"
        in sql
    )
    assert "p_break_minutes integer" in sql
    assert "p_break_minutes < 1" in sql
    assert "p_break_minutes > 180" in sql
    assert "make_interval(mins => p_break_minutes)" in sql
    assert "security definer" in sql
    assert "for update" in sql
    assert "focus_seconds = focus_seconds +" in sql


def test_timed_breaks_migration_keeps_legacy_break_compatible() -> None:
    sql = _migration_sql(
        TIMED_BREAKS_MIGRATION_PATH,
    )

    assert (
        "public.transition_study_activity_session"
        in sql
    )
    assert "p_action = 'start_break'" in sql
    assert "interval '5 minutes'" in sql
    assert "break_ends_at = null" in sql


def test_timed_breaks_migration_restricts_new_rpc_to_service_role() -> None:
    sql = _migration_sql(
        TIMED_BREAKS_MIGRATION_PATH,
    )

    function_signature = (
        "public.start_timed_study_activity_break"
        "(uuid, uuid, integer)"
    )

    assert (
        f"revoke all\non function {function_signature}\n"
        "from authenticated"
        in sql
    )
    assert (
        f"grant execute\non function {function_signature}\n"
        "to service_role"
        in sql
    )
