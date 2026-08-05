# File: /backend/tests/test_ai_retrieval_migration.py

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIRECTORY = ROOT / "supabase" / "migrations"
RETRIEVAL_MIGRATION_PATTERN = (
    "*_create_ai_chunk_retrieval_search.sql"
)


def _retrieval_migrations() -> list[Path]:
    """Return the Phase 5A retrieval migration paths."""

    return sorted(
        MIGRATIONS_DIRECTORY.glob(
            RETRIEVAL_MIGRATION_PATTERN,
        )
    )


def _normalize_sql(sql_text: str) -> str:
    """Normalize SQL whitespace for stable contract assertions."""

    return " ".join(
        sql_text.lower().split()
    )


@pytest.fixture(scope="module")
def migration_path() -> Path:
    """Return the single retrieval-search migration."""

    migration_paths = _retrieval_migrations()

    assert len(migration_paths) == 1, (
        "Expected exactly one retrieval-search migration, "
        f"but found {len(migration_paths)}."
    )

    return migration_paths[0]


@pytest.fixture(scope="module")
def sql_text(migration_path: Path) -> str:
    """Read the retrieval migration as UTF-8 text."""

    return migration_path.read_text(
        encoding="utf-8",
    )


@pytest.fixture(scope="module")
def normalized_sql(sql_text: str) -> str:
    """Return normalized lowercase SQL."""

    return _normalize_sql(
        sql_text,
    )


def test_exactly_one_retrieval_migration_exists() -> None:
    """Only one migration should define the retrieval RPC."""

    migration_paths = _retrieval_migrations()

    assert len(migration_paths) == 1


def test_migration_has_correct_file_path_comment(
    migration_path: Path,
    sql_text: str,
) -> None:
    """The migration should begin with its repository filepath."""

    relative_path = migration_path.relative_to(
        ROOT,
    ).as_posix()

    first_line = sql_text.splitlines()[0]

    assert first_line == f"-- File: /{relative_path}"


def test_function_signature_and_defaults_are_present(
    normalized_sql: str,
) -> None:
    """The SQL should expose the approved retrieval parameters."""

    expected_terms = (
        (
            "create or replace function "
            "public.search_study_file_ai_chunks("
        ),
        "p_user_id uuid",
        "p_query_embedding jsonb",
        "p_match_count integer default 8",
        (
            "p_similarity_threshold "
            "double precision default 0.60"
        ),
        "p_study_file_id uuid default null",
        "p_subject_id uuid default null",
        "returns table (",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_return_contract_contains_source_metadata(
    normalized_sql: str,
) -> None:
    """The RPC should return context and citation metadata."""

    expected_fields = (
        "chunk_id uuid",
        "study_file_id uuid",
        "subject_id uuid",
        "source_name text",
        "chunk_index integer",
        "content text",
        "start_offset integer",
        "end_offset integer",
        "chunk_metadata jsonb",
        "embedding_model text",
        "similarity_score double precision",
    )

    for field in expected_fields:
        assert field in normalized_sql

    return_section = normalized_sql.split(
        "returns table (",
        maxsplit=1,
    )[1].split(
        ") language",
        maxsplit=1,
    )[0]

    assert "embedding extensions.vector" not in return_section


def test_function_execution_settings_are_restricted(
    normalized_sql: str,
) -> None:
    """The function should use approved trusted settings."""

    expected_terms = (
        "language plpgsql",
        "stable",
        "security definer",
        "set search_path = ''",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_identity_and_retrieval_parameter_validation(
    normalized_sql: str,
) -> None:
    """User, count, and threshold bounds should be enforced."""

    expected_terms = (
        "if p_user_id is null then",
        "p_match_count is null",
        "p_match_count < 1",
        "p_match_count > 20",
        "p_similarity_threshold is null",
        "p_similarity_threshold < 0::double precision",
        "p_similarity_threshold > 1::double precision",
        "the retrieval user id is required.",
        "the retrieval match count must be between 1 and 20.",
        "the similarity threshold must be between 0 and 1.",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_query_embedding_json_validation_is_present(
    normalized_sql: str,
) -> None:
    """The query embedding should be validated before conversion."""

    expected_terms = (
        "if p_query_embedding is null then",
        "jsonb_typeof(",
        "is distinct from 'array'",
        "jsonb_array_length(",
        "<> 768",
        "jsonb_array_elements(",
        "is distinct from 'number'",
        "the query embedding is required.",
        "the query embedding must be a json array.",
        "the query embedding must contain exactly 768 values.",
        "every query embedding value must be numeric.",
        "the query embedding cannot be a zero vector.",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_query_embedding_conversion_uses_vector_768(
    normalized_sql: str,
) -> None:
    """The JSON array should become a 768-dimensional vector."""

    expected_terms = (
        "v_query_vector extensions.vector(768)",
        "p_query_embedding::text",
        "as extensions.vector(768)",
        "the query embedding could not be converted",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_retrieval_enforces_ownership_and_ready_status(
    normalized_sql: str,
) -> None:
    """Only owned chunks from ready files should be eligible."""

    expected_terms = (
        "from public.study_file_ai_chunks as ai_chunk",
        "inner join public.study_files as study_file",
        "study_file.id = ai_chunk.study_file_id",
        "ai_chunk.user_id = p_user_id",
        "study_file.user_id = p_user_id",
        "study_file.processing_status = 'ready'",
        "ai_chunk.embedding_dimensions = 768",
        "ai_chunk.embedding_task_type = 'retrieval_document'",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_optional_file_and_subject_scopes_are_supported(
    normalized_sql: str,
) -> None:
    """The search should support optional file and subject scopes."""

    expected_terms = (
        "p_study_file_id is null",
        "ai_chunk.study_file_id = p_study_file_id",
        "p_subject_id is null",
        "study_file.subject_id = p_subject_id",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_cosine_similarity_and_threshold_are_present(
    normalized_sql: str,
) -> None:
    """The RPC should calculate and filter cosine similarity."""

    assert normalized_sql.count(
        "operator(extensions.<=>)"
    ) >= 3

    expected_terms = (
        "1::double precision",
        "as similarity_score",
        "- p_similarity_threshold",
    )

    for term in expected_terms:
        assert term in normalized_sql


def test_distance_ordering_is_index_compatible_and_stable(
    normalized_sql: str,
) -> None:
    """Results should order by distance before deterministic ties."""

    expected_order = (
        "order by "
        "ai_chunk.embedding "
        "operator(extensions.<=>) "
        "v_query_vector asc, "
        "ai_chunk.study_file_id asc, "
        "ai_chunk.chunk_index asc "
        "limit p_match_count;"
    )

    assert expected_order in normalized_sql
    assert "order by similarity_score" not in normalized_sql


def test_function_execution_is_service_role_only(
    normalized_sql: str,
) -> None:
    """Only the trusted backend service role may execute it."""

    function_name = (
        "public.search_study_file_ai_chunks"
    )

    revoke_prefix = (
        f"revoke all on function {function_name}"
    )

    assert normalized_sql.count(
        revoke_prefix
    ) == 3

    assert "from public;" in normalized_sql
    assert "from anon;" in normalized_sql
    assert "from authenticated;" in normalized_sql

    assert (
        f"grant execute on function {function_name}"
        in normalized_sql
    )

    assert "to service_role;" in normalized_sql


def test_retrieval_migration_is_read_only(
    normalized_sql: str,
) -> None:
    """The search function should not change stored data."""

    forbidden_statements = (
        "insert into public.study_file_ai_chunks",
        "update public.study_file_ai_chunks",
        "delete from public.study_file_ai_chunks",
        "truncate public.study_file_ai_chunks",
        "drop table public.study_file_ai_chunks",
        "alter table public.study_file_ai_chunks",
    )

    for statement in forbidden_statements:
        assert statement not in normalized_sql


def test_security_sensitive_objects_are_fully_qualified(
    normalized_sql: str,
) -> None:
    """Security-definer SQL should qualify trusted objects."""

    expected_terms = (
        "public.search_study_file_ai_chunks",
        "public.study_file_ai_chunks",
        "public.study_files",
        "extensions.vector(768)",
        "operator(extensions.<=>)",
    )

    for term in expected_terms:
        assert term in normalized_sql
