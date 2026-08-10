# File: /backend/tests/test_quiz_migration.py

# Purpose: Verifies the Track B quiz database foundation,
# ownership rules, answer-key protection, and RLS contract.

from pathlib import Path

ROOT = Path(
    __file__,
).resolve().parents[2]

MIGRATION_PATH = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260809204500_create_quizzes_foundation.sql"
)


def _migration_sql() -> str:
    """Load the Quiz foundation migration."""

    return MIGRATION_PATH.read_text(
        encoding="utf-8",
    ).lower()


def test_quiz_migration_exists_and_is_not_empty() -> None:
    """The real Quiz migration must exist locally."""

    assert MIGRATION_PATH.exists()

    assert (
        MIGRATION_PATH.stat().st_size
        > 0
    )


def test_quiz_migration_creates_required_tables() -> None:
    """Quiz persistence must contain quizzes and questions."""

    sql = _migration_sql()

    assert (
        "create table public.quizzes"
        in sql
    )

    assert (
        "create table public.quiz_questions"
        in sql
    )


def test_quizzes_have_required_columns() -> None:
    """Core generated-quiz metadata must be represented."""

    sql = _migration_sql()

    required_columns = (
        "user_id uuid not null",
        "subject_id uuid not null",
        "study_file_id uuid",
        "scope_type text not null",
        "title text not null",
        "quiz_type text not null",
        "difficulty text not null",
        "question_count integer not null",
        "generation_model text not null",
        "generation_count integer not null",
        "generated_at timestamptz not null",
        "created_at timestamptz not null",
        "updated_at timestamptz not null",
    )

    for column in required_columns:
        assert column in sql


def test_quiz_questions_have_required_columns() -> None:
    """Question rows must preserve private scoring data."""

    sql = _migration_sql()

    required_columns = (
        "quiz_id uuid not null",
        "position integer not null",
        "question_type text not null",
        "topic text not null",
        "question text not null",
        "choices jsonb not null",
        "correct_answer text not null",
        "accepted_answers jsonb not null",
        "explanation text not null",
    )

    for column in required_columns:
        assert column in sql


def test_quiz_migration_enforces_scope_rules() -> None:
    """Subject and file Quiz scopes must remain distinct."""

    sql = _migration_sql()

    assert (
        "quizzes_scope_type_check"
        in sql
    )

    assert (
        "quizzes_scope_file_check"
        in sql
    )

    assert "'subject'" in sql
    assert "'file'" in sql


def test_quiz_migration_enforces_quiz_settings() -> None:
    """Quiz type, difficulty, and count must be constrained."""

    sql = _migration_sql()

    assert (
        "quizzes_type_check"
        in sql
    )

    assert (
        "'multiple_choice'"
        in sql
    )

    assert (
        "'true_false'"
        in sql
    )

    assert (
        "'identification'"
        in sql
    )

    assert (
        "'mixed'"
        in sql
    )

    assert (
        "quizzes_difficulty_check"
        in sql
    )

    assert "'easy'" in sql
    assert "'medium'" in sql
    assert "'hard'" in sql

    assert (
        "question_count between 1 and 50"
        in sql
    )


def test_quiz_question_json_fields_are_arrays() -> None:
    """Choices and alternative answers must stay JSON arrays."""

    sql = _migration_sql()

    assert (
        "quiz_questions_choices_array_check"
        in sql
    )

    assert (
        "jsonb_typeof(choices) = 'array'"
        in sql
    )

    assert (
        "quiz_questions_accepted_answers_array_check"
        in sql
    )

    assert (
        "jsonb_typeof(accepted_answers) = 'array'"
        in sql
    )


def test_question_structure_depends_on_question_type() -> None:
    """Database checks must guard basic answer structures."""

    sql = _migration_sql()

    assert (
        "quiz_questions_type_structure_check"
        in sql
    )

    assert (
        "jsonb_array_length(choices) >= 2"
        in sql
    )

    assert (
        "jsonb_array_length(choices) = 2"
        in sql
    )

    assert (
        "jsonb_array_length(choices) = 0"
        in sql
    )


def test_question_positions_are_unique_per_quiz() -> None:
    """One Quiz cannot contain duplicate question positions."""

    sql = _migration_sql()

    assert (
        "quiz_questions_quiz_position_unique"
        in sql
    )

    assert (
        "quiz_id,\n            position"
        in sql
    )


def test_quiz_generation_count_remains_positive() -> None:
    """Quiz regeneration count must remain positive."""

    sql = _migration_sql()

    assert (
        "quizzes_generation_count_check"
        in sql
    )

    assert (
        "generation_count >= 1"
        in sql
    )


def test_quiz_migration_validates_source_ownership() -> None:
    """Quiz subjects and files must belong to their owner."""

    sql = _migration_sql()

    assert (
        "validate_quiz_ownership_scope"
        in sql
    )

    assert (
        "quizzes_validate_ownership_scope"
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


def test_quiz_tables_update_timestamps() -> None:
    """Updates must refresh Quiz and question timestamps."""

    sql = _migration_sql()

    assert (
        "set_quiz_updated_at"
        in sql
    )

    assert (
        "quizzes_set_updated_at"
        in sql
    )

    assert (
        "set_quiz_question_updated_at"
        in sql
    )

    assert (
        "quiz_questions_set_updated_at"
        in sql
    )

    assert (
        "new.updated_at = now()"
        in sql
    )


def test_quiz_tables_enable_rls() -> None:
    """Both Quiz tables must be protected by RLS."""

    sql = _migration_sql()

    assert (
        "alter table public.quizzes"
        in sql
    )

    assert (
        "alter table public.quiz_questions"
        in sql
    )

    assert (
        sql.count(
            "enable row level security",
        )
        >= 2
    )


def test_quizzes_allow_owned_browser_read_and_delete() -> None:
    """Students may list/read/delete their Quiz metadata."""

    sql = _migration_sql()

    assert (
        "grant select, delete"
        in sql
    )

    assert (
        "on table public.quizzes"
        in sql
    )

    assert (
        '"quizzes_select_own"'
        in sql
    )

    assert (
        '"quizzes_delete_own"'
        in sql
    )

    assert (
        "auth.uid() = user_id"
        in sql
    )


def test_quiz_questions_revoke_authenticated_access() -> None:
    """Private answer-key rows must not be browser-readable."""

    sql = _migration_sql()

    expected_revoke = (
        "revoke all\n"
        "on table public.quiz_questions\n"
        "from authenticated"
    )

    assert expected_revoke in sql


def test_quiz_questions_are_service_role_only() -> None:
    """Trusted backend code must manage private question rows."""

    sql = _migration_sql()

    expected_grant = (
        "grant all\n"
        "on table public.quiz_questions\n"
        "to service_role"
    )

    assert expected_grant in sql


def test_quiz_question_answer_keys_have_no_browser_policy() -> None:
    """No authenticated RLS policy may expose question rows."""

    sql = _migration_sql()

    assert (
        'create policy "quiz_questions_'
        not in sql
    )