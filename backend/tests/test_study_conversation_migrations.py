# File: /backend/tests/test_study_conversation_migrations.py
# Purpose: Protects the Study Assistant conversation and message
# persistence migrations from accidental schema or security regressions.

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

MIGRATIONS_DIRECTORY = (
    REPOSITORY_ROOT
    / "supabase"
    / "migrations"
)

CONVERSATION_MIGRATION_PATH = (
    MIGRATIONS_DIRECTORY
    / "20260806192800_create_study_conversations_and_messages.sql"
)

OUTCOME_FIX_MIGRATION_PATH = (
    MIGRATIONS_DIRECTORY
    / "20260806200500_fix_study_message_outcome_constraint.sql"
)


def _read_sql(
    migration_path: Path,
) -> str:
    """Read one required migration as normalized SQL."""

    assert migration_path.is_file(), (
        f"Required migration is missing: {migration_path}"
    )

    migration_text = migration_path.read_text(
        encoding="utf-8",
    )

    assert migration_text.strip(), (
        f"Migration is empty: {migration_path}"
    )

    return re.sub(
        r"\s+",
        " ",
        migration_text.lower(),
    ).strip()


def _assert_sql_terms(
    sql_text: str,
    required_terms: tuple[str, ...],
) -> None:
    """Assert that all normalized SQL fragments are present."""

    missing_terms = tuple(
        term
        for term in required_terms
        if re.sub(
            r"\s+",
            " ",
            term.lower(),
        ).strip()
        not in sql_text
    )

    assert not missing_terms, (
        "Migration is missing required SQL terms: "
        + ", ".join(missing_terms)
    )


def test_conversation_migration_files_exist() -> None:
    """Both Phase 5G migration files must remain available."""

    assert CONVERSATION_MIGRATION_PATH.is_file()
    assert OUTCOME_FIX_MIGRATION_PATH.is_file()


def test_conversation_migration_creates_required_tables() -> None:
    """Conversation and message tables must retain core columns."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            "create table public.study_conversations",
            "create table public.study_messages",
            "user_id uuid not null",
            "title text not null",
            "subject_id uuid",
            "study_file_id uuid",
            "last_message_at timestamptz not null",
            "conversation_id uuid not null",
            "role text not null",
            "content text not null",
            "outcome text",
            "sources jsonb not null",
        ),
    )


def test_conversation_migration_retains_foreign_keys() -> None:
    """Conversation ownership and cascading messages must be enforced."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            "references auth.users(id) on delete cascade",
            "references public.subjects(id) on delete set null",
            "references public.study_files(id) on delete set null",
            (
                "references public.study_conversations(id) "
                "on delete cascade"
            ),
        ),
    )


def test_conversation_migration_retains_message_constraints() -> None:
    """Message roles, contents, sources, and outcomes stay controlled."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            "constraint study_messages_role_check",
            "role in ( 'user', 'assistant' )",
            "constraint study_messages_content_check",
            "char_length(btrim(content)) between 1 and 50000",
            "constraint study_messages_sources_array_check",
            "jsonb_typeof(sources) = 'array'",
            "constraint study_messages_role_outcome_check",
        ),
    )


def test_conversation_migration_retains_indexes() -> None:
    """Conversation sorting and message loading indexes must remain."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            "create index study_conversations_user_recent_idx",
            "create index study_conversations_subject_idx",
            "create index study_conversations_study_file_idx",
            "create index study_messages_conversation_created_idx",
        ),
    )


def test_conversation_migration_retains_filter_validation() -> None:
    """Conversation filters must continue to validate ownership."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                "create or replace function "
                "public.validate_study_conversation_filters()"
            ),
            "security definer",
            "subject.user_id = new.user_id",
            (
                "selected_file_user_id "
                "is distinct from new.user_id"
            ),
            "new.subject_id := selected_file_subject_id",
            (
                "selected_file_subject_id "
                "is distinct from new.subject_id"
            ),
            "create trigger study_conversations_validate_filters",
        ),
    )


def test_conversation_migration_retains_timestamp_triggers() -> None:
    """Conversation timestamps must update after changes and messages."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                "create or replace function "
                "public.set_study_conversation_updated_at()"
            ),
            "new.updated_at := now()",
            (
                "create or replace function "
                "public.touch_study_conversation_from_message()"
            ),
            "last_message_at = greatest",
            "create trigger study_conversations_set_updated_at",
            "create trigger study_messages_touch_conversation",
        ),
    )


def test_conversation_migration_enables_rls() -> None:
    """Both persisted chat tables must keep RLS enabled."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                "alter table public.study_conversations "
                "enable row level security"
            ),
            (
                "alter table public.study_messages "
                "enable row level security"
            ),
        ),
    )


def test_conversation_migration_retains_owner_policies() -> None:
    """Conversation access must stay limited to each owner."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                '"users can view their own study conversations" '
                "on public.study_conversations for select"
            ),
            (
                '"users can create their own study conversations" '
                "on public.study_conversations for insert"
            ),
            (
                '"users can update their own study conversations" '
                "on public.study_conversations for update"
            ),
            (
                '"users can delete their own study conversations" '
                "on public.study_conversations for delete"
            ),
            "auth.uid() = user_id",
        ),
    )


def test_conversation_migration_retains_message_policies() -> None:
    """Messages must remain accessible only through owned chats."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                '"users can view messages from their conversations" '
                "on public.study_messages for select"
            ),
            (
                '"users can add messages to their conversations" '
                "on public.study_messages for insert"
            ),
            (
                "conversation.id = "
                "study_messages.conversation_id"
            ),
            "conversation.user_id = auth.uid()",
        ),
    )


def test_conversation_migration_retains_safe_grants() -> None:
    """Anonymous access stays revoked and authenticated grants stay narrow."""

    sql_text = _read_sql(
        CONVERSATION_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                "revoke all on table "
                "public.study_conversations from anon"
            ),
            (
                "revoke all on table "
                "public.study_messages from anon"
            ),
            (
                "grant select, insert, update, delete "
                "on table public.study_conversations "
                "to authenticated"
            ),
            (
                "grant select, insert "
                "on table public.study_messages "
                "to authenticated"
            ),
        ),
    )


def test_outcome_fix_requires_assistant_outcome() -> None:
    """The corrective migration must reject null assistant outcomes."""

    sql_text = _read_sql(
        OUTCOME_FIX_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            (
                "alter table public.study_messages "
                "drop constraint "
                "study_messages_role_outcome_check"
            ),
            (
                "alter table public.study_messages "
                "add constraint "
                "study_messages_role_outcome_check"
            ),
            "role = 'assistant'",
            "outcome is not null",
            "outcome in ( 'answered', 'no_context' )",
        ),
    )


def test_outcome_fix_preserves_user_message_rules() -> None:
    """User messages must still have no outcome or source metadata."""

    sql_text = _read_sql(
        OUTCOME_FIX_MIGRATION_PATH,
    )

    _assert_sql_terms(
        sql_text,
        (
            "role = 'user'",
            "outcome is null",
            "sources = '[]'::jsonb",
        ),
    )