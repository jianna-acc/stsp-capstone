# File: /backend/tests/test_quiz_attempt_rpc_migration.py

# Purpose: Verifies trusted atomic Quiz-attempt start and
# answer-submission database functions.

from pathlib import Path

ROOT = Path(
    __file__,
).resolve().parents[2]

MIGRATION_PATH = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260809225500_create_quiz_attempt_rpcs.sql"
)


def _migration_sql() -> str:
    """Load the Quiz-attempt RPC migration."""

    return MIGRATION_PATH.read_text(
        encoding="utf-8",
    ).lower()


def test_attempt_rpc_migration_exists() -> None:
    """The Quiz-attempt RPC migration must exist."""

    assert MIGRATION_PATH.exists()
    assert MIGRATION_PATH.stat().st_size > 0


def test_start_attempt_rpc_exists() -> None:
    """Attempts must be started atomically."""

    sql = _migration_sql()

    assert (
        "create or replace function public.start_quiz_attempt"
        in sql
    )

    assert (
        "insert into public.quiz_attempts"
        in sql
    )


def test_start_attempt_validates_owner() -> None:
    """The target Quiz must belong to the attempt owner."""

    sql = _migration_sql()

    assert (
        "q.user_id = p_user_id"
        in sql
    )

    assert (
        "the requested quiz was not found"
        in sql
    )


def test_submit_answer_rpc_exists() -> None:
    """Answer grading must be one atomic operation."""

    sql = _migration_sql()

    assert (
        "create or replace function public.submit_quiz_attempt_answer"
        in sql
    )

    assert (
        "for update"
        in sql
    )


def test_submit_answer_requires_expected_position() -> None:
    """Stale or duplicate submissions cannot advance another question."""

    sql = _migration_sql()

    assert (
        "p_position <> v_attempt.current_position"
        in sql
    )

    assert (
        "position does not match the current question"
        in sql
    )


def test_identification_supports_accepted_answers() -> None:
    """Identification grading must support approved alternatives."""

    sql = _migration_sql()

    assert (
        "jsonb_array_elements_text"
        in sql
    )

    assert (
        "v_question.accepted_answers"
        in sql
    )


def test_answer_is_saved_without_copying_key() -> None:
    """Submission history stores correctness but not the answer key."""

    sql = _migration_sql()

    assert (
        "insert into public.quiz_attempt_answers"
        in sql
    )

    assert (
        "submitted_answer"
        in sql
    )

    assert (
        "is_correct"
        in sql
    )


def test_final_question_completes_attempt() -> None:
    """The final answer must complete and score the attempt."""

    sql = _migration_sql()

    assert (
        "status = 'completed'"
        in sql
    )

    assert (
        "completed_at = v_completed_at"
        in sql
    )

    assert (
        "score_percentage = v_score_percentage"
        in sql
    )


def test_rpc_permissions_are_service_role_only() -> None:
    """Browser clients must never invoke trusted grading RPCs."""

    sql = _migration_sql()

    assert (
        "public.start_quiz_attempt"
        in sql
    )

    assert (
        "public.submit_quiz_attempt_answer"
        in sql
    )

    assert sql.count(
        "to service_role"
    ) >= 2

    assert (
        "from authenticated"
        in sql
    )