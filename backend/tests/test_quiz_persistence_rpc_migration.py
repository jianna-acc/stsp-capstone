# File: /backend/tests/test_quiz_persistence_rpc_migration.py

# Purpose: Verifies the trusted atomic Quiz persistence
# database function and its restricted privileges.

from pathlib import Path

ROOT = Path(
    __file__,
).resolve().parents[2]

MIGRATION_PATH = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260809211600_create_quiz_persistence_rpc.sql"
)


def _migration_sql() -> str:
    """Load the Quiz persistence RPC migration."""

    return MIGRATION_PATH.read_text(
        encoding="utf-8",
    ).lower()


def test_quiz_persistence_rpc_migration_exists() -> None:
    """The Quiz persistence migration must exist."""

    assert MIGRATION_PATH.exists()

    assert (
        MIGRATION_PATH.stat().st_size
        > 0
    )


def test_quiz_persistence_rpc_is_created() -> None:
    """Atomic Quiz persistence must use one database function."""

    sql = _migration_sql()

    assert (
        "create or replace function "
        "public.create_quiz_with_questions"
        in sql
    )

    assert (
        "returns uuid"
        in sql
    )


def test_quiz_persistence_rpc_is_security_definer() -> None:
    """Only trusted backend execution may bypass browser access."""

    sql = _migration_sql()

    assert (
        "security definer"
        in sql
    )

    assert (
        "set search_path = public, pg_temp"
        in sql
    )


def test_quiz_persistence_rpc_validates_question_count() -> None:
    """Generated question count must match requested count."""

    sql = _migration_sql()

    assert (
        "jsonb_array_length(p_questions)"
        in sql
    )

    assert (
        "<> p_question_count"
        in sql
    )


def test_quiz_persistence_rpc_inserts_parent_and_children() -> None:
    """The function must persist both Quiz tables."""

    sql = _migration_sql()

    assert (
        "insert into public.quizzes"
        in sql
    )

    assert (
        "insert into public.quiz_questions"
        in sql
    )


def test_quiz_persistence_rpc_preserves_private_answer_data() -> None:
    """Question rows must persist answer and explanation data."""

    sql = _migration_sql()

    assert (
        "correct_answer"
        in sql
    )

    assert (
        "accepted_answers"
        in sql
    )

    assert (
        "explanation"
        in sql
    )


def test_quiz_persistence_rpc_validates_question_types() -> None:
    """Supported question structures must be enforced."""

    sql = _migration_sql()

    assert "'multiple_choice'" in sql
    assert "'true_false'" in sql
    assert "'identification'" in sql

    assert (
        "generated multiple-choice quiz data is invalid"
        in sql
    )

    assert (
        "generated true-or-false quiz data is invalid"
        in sql
    )

    assert (
        "generated identification quiz data is invalid"
        in sql
    )


def test_quiz_persistence_rpc_blocks_browser_execution() -> None:
    """Anonymous and authenticated clients cannot call the RPC."""

    sql = _migration_sql()

    assert (
        "from anon"
        in sql
    )

    assert (
        "from authenticated"
        in sql
    )

    assert (
        "to service_role"
        in sql
    )


def test_quiz_persistence_rpc_returns_created_id() -> None:
    """The function must return the newly saved Quiz UUID."""

    sql = _migration_sql()

    assert (
        "returning id"
        in sql
    )

    assert (
        "into v_quiz_id"
        in sql
    )

    assert (
        "return v_quiz_id"
        in sql
    )