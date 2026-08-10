# File: /backend/tests/test_quiz_attempt_migration.py

# Purpose: Verifies the Quiz attempt and submitted-answer
# database foundation, ownership controls, and RLS contract.

from pathlib import Path

ROOT = Path(
    __file__,
).resolve().parents[2]

MIGRATION_PATH = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260809223500_create_quiz_attempt_foundation.sql"
)


def _migration_sql() -> str:
    """Load the Quiz-attempt migration."""

    return MIGRATION_PATH.read_text(
        encoding="utf-8",
    ).lower()


def test_quiz_attempt_migration_exists() -> None:
    """The Quiz-attempt migration must exist locally."""

    assert MIGRATION_PATH.exists()

    assert (
        MIGRATION_PATH.stat().st_size
        > 0
    )


def test_migration_creates_attempt_tables() -> None:
    """Attempt and submitted-answer persistence must exist."""

    sql = _migration_sql()

    assert (
        "create table public.quiz_attempts"
        in sql
    )

    assert (
        "create table public.quiz_attempt_answers"
        in sql
    )


def test_quiz_attempt_has_required_fields() -> None:
    """Attempt progress and scoring fields must be persisted."""

    sql = _migration_sql()

    required_fields = (
        "user_id uuid not null",
        "quiz_id uuid not null",
        "status text not null",
        "current_position integer not null",
        "correct_count integer not null",
        "question_count integer not null",
        "score_percentage numeric(5, 2) not null",
        "started_at timestamptz not null",
        "completed_at timestamptz",
        "created_at timestamptz not null",
        "updated_at timestamptz not null",
    )

    for field in required_fields:
        assert field in sql


def test_attempt_answer_has_safe_scoring_fields() -> None:
    """Answer history must store submissions without copying keys."""

    sql = _migration_sql()

    required_fields = (
        "attempt_id uuid not null",
        "quiz_question_id uuid not null",
        "position integer not null",
        "topic text not null",
        "question_type text not null",
        "submitted_answer text not null",
        "is_correct boolean not null",
        "answered_at timestamptz not null",
    )

    for field in required_fields:
        assert field in sql


def test_attempt_answer_does_not_copy_private_answer_key() -> None:
    """Attempt history must not duplicate private Quiz answers."""

    sql = _migration_sql()

    answer_table_start = sql.index(
        "create table public.quiz_attempt_answers"
    )

    answer_table_end = sql.index(
        "create index quiz_attempts_user_created_at_idx"
    )

    answer_table_sql = sql[
        answer_table_start:answer_table_end
    ]

    assert "correct_answer" not in answer_table_sql
    assert "accepted_answers" not in answer_table_sql
    assert "explanation" not in answer_table_sql


def test_attempt_progress_constraints_exist() -> None:
    """Attempt state must enforce safe position and score ranges."""

    sql = _migration_sql()

    assert (
        "quiz_attempts_status_check"
        in sql
    )

    assert (
        "quiz_attempts_current_position_check"
        in sql
    )

    assert (
        "quiz_attempts_correct_count_check"
        in sql
    )

    assert (
        "quiz_attempts_score_percentage_check"
        in sql
    )

    assert (
        "quiz_attempts_completion_state_check"
        in sql
    )


def test_attempt_scope_validates_quiz_ownership() -> None:
    """Attempt owner and Quiz owner must be identical."""

    sql = _migration_sql()

    assert (
        "validate_quiz_attempt_scope"
        in sql
    )

    assert (
        "from public.quizzes"
        in sql
    )

    assert (
        "v_quiz_user_id <> new.user_id"
        in sql
    )

    assert (
        "v_quiz_question_count <> new.question_count"
        in sql
    )


def test_answer_scope_validates_question_membership() -> None:
    """Submitted answers must belong to the attempt's Quiz."""

    sql = _migration_sql()

    assert (
        "validate_quiz_attempt_answer_scope"
        in sql
    )

    assert (
        "from public.quiz_questions"
        in sql
    )

    assert (
        "quiz_id = v_quiz_id"
        in sql
    )

    assert (
        "position = new.position"
        in sql
    )

    assert (
        "question_type = new.question_type"
        in sql
    )


def test_completed_attempt_rejects_new_answers() -> None:
    """The database must protect completed attempts."""

    sql = _migration_sql()

    assert (
        "v_attempt_status <> 'in_progress'"
        in sql
    )

    assert (
        "completed quiz attempts cannot accept new answers"
        in sql
    )


def test_attempt_answer_uniqueness_is_enforced() -> None:
    """One attempt may answer each position only once."""

    sql = _migration_sql()

    assert (
        "quiz_attempt_answers_attempt_question_unique"
        in sql
    )

    assert (
        "quiz_attempt_answers_attempt_position_unique"
        in sql
    )


def test_attempt_tables_enable_rls() -> None:
    """Attempt and answer history must use Row Level Security."""

    sql = _migration_sql()

    assert (
        "alter table public.quiz_attempts"
        in sql
    )

    assert (
        "alter table public.quiz_attempt_answers"
        in sql
    )

    assert sql.count(
        "enable row level security"
    ) >= 2


def test_browser_writes_are_not_granted() -> None:
    """Authenticated browser clients may read but not write."""

    sql = _migration_sql()

    assert (
        "grant select\non table public.quiz_attempts"
        in sql
    )

    assert (
        "grant select\non table public.quiz_attempt_answers"
        in sql
    )

    assert (
        "grant all\non table public.quiz_attempts\nto service_role"
        in sql
    )

    assert (
        "grant all\non table public.quiz_attempt_answers\nto service_role"
        in sql
    )


def test_owned_select_policies_exist() -> None:
    """Authenticated reads must remain ownership scoped."""

    sql = _migration_sql()

    assert (
        '"quiz_attempts_select_own"'
        in sql
    )

    assert (
        '"quiz_attempt_answers_select_own"'
        in sql
    )

    assert (
        "auth.uid() = user_id"
        in sql
    )

    assert (
        "quiz_attempts.user_id"
        in sql
    )