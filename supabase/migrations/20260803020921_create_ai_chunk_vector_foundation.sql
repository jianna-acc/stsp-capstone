-- File: /supabase/migrations/20260803020921_create_ai_chunk_vector_foundation.sql
-- Purpose: Enables pgvector and creates secure, idempotent
-- persistence for AI-oriented study-file chunks and embeddings.

begin;

-- ============================================================
-- PGVECTOR EXTENSION
-- ============================================================

create schema if not exists extensions;

create extension if not exists vector
with schema extensions;

-- ============================================================
-- AI-ORIENTED STUDY-FILE CHUNKS
-- ============================================================

create table public.study_file_ai_chunks (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    study_file_id uuid not null
        references public.study_files(id)
        on delete cascade,

    chunk_index integer not null,

    content text not null,

    start_offset integer not null,
    end_offset integer not null,

    source_name text,

    embedding_model text not null,
    embedding_dimensions integer not null
        default 768,

    embedding_task_type text not null
        default 'retrieval_document',

    embedding extensions.vector(768) not null,

    chunk_metadata jsonb not null
        default '{}'::jsonb,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint study_file_ai_chunks_index_nonnegative
        check (
            chunk_index >= 0
        ),

    constraint study_file_ai_chunks_content_present
        check (
            char_length(btrim(content)) > 0
            and content = btrim(content)
        ),

    constraint study_file_ai_chunks_offsets_valid
        check (
            start_offset >= 0
            and end_offset > start_offset
        ),

    constraint study_file_ai_chunks_content_offset_match
        check (
            char_length(content)
                = end_offset - start_offset
        ),

    constraint study_file_ai_chunks_source_name_length
        check (
            source_name is null
            or char_length(btrim(source_name))
                between 1 and 255
        ),

    constraint study_file_ai_chunks_model_length
        check (
            char_length(btrim(embedding_model))
                between 1 and 120
        ),

    constraint study_file_ai_chunks_dimensions_fixed
        check (
            embedding_dimensions = 768
        ),

    constraint study_file_ai_chunks_task_type_allowed
        check (
            embedding_task_type = 'retrieval_document'
        ),

    constraint study_file_ai_chunks_metadata_object
        check (
            jsonb_typeof(chunk_metadata) = 'object'
        ),

    constraint study_file_ai_chunks_file_index_unique
        unique (
            study_file_id,
            chunk_index
        )
);

comment on table public.study_file_ai_chunks is
    'Stores deterministic AI chunks and 768-dimensional embeddings for private study files.';

comment on column public.study_file_ai_chunks.user_id is
    'Authenticated student who owns the source study file.';

comment on column public.study_file_ai_chunks.study_file_id is
    'Private study file from which this AI chunk was prepared.';

comment on column public.study_file_ai_chunks.chunk_index is
    'Contiguous material-scoped index beginning at zero.';

comment on column public.study_file_ai_chunks.content is
    'Normalized text sent to the configured embedding provider.';

comment on column public.study_file_ai_chunks.start_offset is
    'Inclusive character offset inside the normalized material text.';

comment on column public.study_file_ai_chunks.end_offset is
    'Exclusive character offset inside the normalized material text.';

comment on column public.study_file_ai_chunks.embedding_model is
    'Embedding model that generated the stored vector.';

comment on column public.study_file_ai_chunks.embedding is
    '768-dimensional retrieval-document embedding.';

-- ============================================================
-- STANDARD INDEXES
-- ============================================================

create index study_file_ai_chunks_user_id_idx
    on public.study_file_ai_chunks(user_id);

create index study_file_ai_chunks_study_file_id_idx
    on public.study_file_ai_chunks(study_file_id);

create index study_file_ai_chunks_user_file_idx
    on public.study_file_ai_chunks(
        user_id,
        study_file_id
    );

create index study_file_ai_chunks_model_idx
    on public.study_file_ai_chunks(
        embedding_model
    );

-- ============================================================
-- HNSW COSINE-SIMILARITY INDEX
-- ============================================================

create index study_file_ai_chunks_embedding_hnsw_idx
    on public.study_file_ai_chunks
    using hnsw (
        embedding extensions.vector_cosine_ops
    )
    with (
        m = 16,
        ef_construction = 64
    );

-- ============================================================
-- UPDATED-AT TRIGGER
-- ============================================================

create trigger study_file_ai_chunks_set_updated_at
before update on public.study_file_ai_chunks
for each row
execute function public.set_current_updated_at();

-- ============================================================
-- TABLE PERMISSIONS
-- ============================================================

revoke all
    on table public.study_file_ai_chunks
    from public;

revoke all
    on table public.study_file_ai_chunks
    from anon;

revoke all
    on table public.study_file_ai_chunks
    from authenticated;

grant select
    on table public.study_file_ai_chunks
    to authenticated;

grant all
    on table public.study_file_ai_chunks
    to service_role;

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.study_file_ai_chunks
    enable row level security;

create policy study_file_ai_chunks_select_own
on public.study_file_ai_chunks
for select
to authenticated
using (
    user_id = (
        select auth.uid()
    )
    and exists (
        select 1
        from public.study_files
        where study_files.id
            = study_file_ai_chunks.study_file_id
          and study_files.user_id
            = (
                select auth.uid()
            )
    )
);

-- Direct writes from authenticated clients are intentionally
-- unavailable. Embeddings are written only through the trusted
-- service-role RPC below.

-- ============================================================
-- IDEMPOTENT EMBEDDING PERSISTENCE
-- ============================================================

create or replace function public.replace_study_file_ai_chunks(
    p_study_file_id uuid,
    p_embedding_model text,
    p_embedding_dimensions integer,
    p_original_character_count integer,
    p_chunks jsonb
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_user_id uuid;

    v_chunk jsonb;
    v_chunk_index integer;
    v_expected_chunk_index integer := 0;

    v_content text;
    v_start_offset integer;
    v_end_offset integer;

    v_source_name text;

    v_embedding_json jsonb;
    v_embedding extensions.vector(768);

    v_chunk_metadata jsonb;
begin
    if nullif(
        btrim(p_embedding_model),
        ''
    ) is null then
        raise exception
            'The embedding model is required.'
            using errcode = '22023';
    end if;

    if char_length(
        btrim(p_embedding_model)
    ) > 120 then
        raise exception
            'The embedding model name is too long.'
            using errcode = '22023';
    end if;

    if p_embedding_dimensions <> 768 then
        raise exception
            'Embedding dimensions must equal 768.'
            using errcode = '22023';
    end if;

    if p_original_character_count < 1 then
        raise exception
            'Original character count must be positive.'
            using errcode = '22023';
    end if;

    if p_chunks is null
        or jsonb_typeof(p_chunks) <> 'array'
        or jsonb_array_length(p_chunks) = 0 then
        raise exception
            'At least one AI chunk is required.'
            using errcode = '22023';
    end if;

    if jsonb_array_length(p_chunks) > 10000 then
        raise exception
            'The AI chunk count exceeds the database limit.'
            using errcode = '22023';
    end if;

    select study_files.user_id
    into v_user_id
    from public.study_files
    where study_files.id = p_study_file_id
      and study_files.processing_status = 'indexing'
    for update;

    if not found then
        raise exception
            'Only an indexing study file can store AI chunks.'
            using errcode = 'P0001';
    end if;

    if not exists (
        select 1
        from public.file_processing_jobs
        where file_processing_jobs.study_file_id
            = p_study_file_id
          and file_processing_jobs.status
            = 'processing'
    ) then
        raise exception
            'An active processing job was not found.'
            using errcode = 'P0002';
    end if;

    for v_chunk in
        select chunk_item.value
        from jsonb_array_elements(p_chunks)
            as chunk_item(value)
    loop
        if jsonb_typeof(v_chunk) <> 'object' then
            raise exception
                'Every AI chunk must be a JSON object.'
                using errcode = '22023';
        end if;

        begin
            v_chunk_index :=
                (v_chunk ->> 'chunk_index')::integer;

            v_start_offset :=
                (v_chunk ->> 'start_offset')::integer;

            v_end_offset :=
                (v_chunk ->> 'end_offset')::integer;

        exception
            when invalid_text_representation
                or numeric_value_out_of_range then
                raise exception
                    'AI chunk indexes and offsets must be valid integers.'
                    using errcode = '22023';
        end;

        if v_chunk_index is null
            or v_start_offset is null
            or v_end_offset is null then
            raise exception
                'AI chunk indexes and offsets are required.'
                using errcode = '22023';
        end if;

        if v_chunk_index <> v_expected_chunk_index then
            raise exception
                'AI chunk indexes must be contiguous and begin at zero.'
                using errcode = '22023';
        end if;

        v_content := coalesce(
            v_chunk ->> 'content',
            ''
        );

        if nullif(
            btrim(v_content),
            ''
        ) is null then
            raise exception
                'AI chunk content cannot be empty.'
                using errcode = '22023';
        end if;

        if v_content <> btrim(v_content) then
            raise exception
                'AI chunk content must be normalized.'
                using errcode = '22023';
        end if;

        if v_start_offset < 0
            or v_end_offset <= v_start_offset then
            raise exception
                'AI chunk offsets are invalid.'
                using errcode = '22023';
        end if;

        if v_end_offset > p_original_character_count then
            raise exception
                'AI chunk offsets exceed the normalized material length.'
                using errcode = '22023';
        end if;

        if char_length(v_content)
            <> v_end_offset - v_start_offset then
            raise exception
                'AI chunk content does not match its offsets.'
                using errcode = '22023';
        end if;

        v_source_name := nullif(
            btrim(
                coalesce(
                    v_chunk ->> 'source_name',
                    ''
                )
            ),
            ''
        );

        if v_source_name is not null
            and char_length(v_source_name) > 255 then
            raise exception
                'AI chunk source name is too long.'
                using errcode = '22023';
        end if;

        v_embedding_json :=
            v_chunk -> 'embedding';

        if jsonb_typeof(v_embedding_json)
            is distinct from 'array' then
            raise exception
                'Every AI chunk must contain an embedding array.'
                using errcode = '22023';
        end if;

        if jsonb_array_length(v_embedding_json)
            <> p_embedding_dimensions then
            raise exception
                'An AI chunk embedding has the wrong dimensions.'
                using errcode = '22023';
        end if;

        if exists (
            select 1
            from jsonb_array_elements(
                v_embedding_json
            ) as embedding_item(value)
            where jsonb_typeof(
                embedding_item.value
            ) <> 'number'
        ) then
            raise exception
                'AI chunk embeddings must contain only numbers.'
                using errcode = '22023';
        end if;

        begin
            v_embedding := (
                v_embedding_json::text
            )::extensions.vector(768);

        exception
            when others then
                raise exception
                    'An AI chunk embedding could not be converted to vector(768).'
                    using errcode = '22023';
        end;

        v_chunk_metadata := coalesce(
            v_chunk -> 'metadata',
            '{}'::jsonb
        );

        if jsonb_typeof(v_chunk_metadata)
            is distinct from 'object' then
            raise exception
                'AI chunk metadata must be a JSON object.'
                using errcode = '22023';
        end if;

        insert into public.study_file_ai_chunks (
            user_id,
            study_file_id,
            chunk_index,
            content,
            start_offset,
            end_offset,
            source_name,
            embedding_model,
            embedding_dimensions,
            embedding_task_type,
            embedding,
            chunk_metadata
        )
        values (
            v_user_id,
            p_study_file_id,
            v_chunk_index,
            v_content,
            v_start_offset,
            v_end_offset,
            v_source_name,
            btrim(p_embedding_model),
            p_embedding_dimensions,
            'retrieval_document',
            v_embedding,
            v_chunk_metadata
        )
        on conflict (
            study_file_id,
            chunk_index
        )
        do update
        set
            user_id = excluded.user_id,
            content = excluded.content,
            start_offset = excluded.start_offset,
            end_offset = excluded.end_offset,
            source_name = excluded.source_name,
            embedding_model = excluded.embedding_model,
            embedding_dimensions =
                excluded.embedding_dimensions,
            embedding_task_type =
                excluded.embedding_task_type,
            embedding = excluded.embedding,
            chunk_metadata =
                excluded.chunk_metadata,
            updated_at = now();

        v_expected_chunk_index :=
            v_expected_chunk_index + 1;
    end loop;

    delete from public.study_file_ai_chunks
    where study_file_ai_chunks.study_file_id
        = p_study_file_id
      and study_file_ai_chunks.chunk_index
        >= v_expected_chunk_index;

    return v_expected_chunk_index;
end;
$$;

comment on function public.replace_study_file_ai_chunks(
    uuid,
    text,
    integer,
    integer,
    jsonb
) is
    'Idempotently upserts ordered AI chunks and removes obsolete trailing chunks for one actively processing study file.';

-- ============================================================
-- RPC PERMISSIONS
-- ============================================================

revoke all
on function public.replace_study_file_ai_chunks(
    uuid,
    text,
    integer,
    integer,
    jsonb
)
from public;

revoke all
on function public.replace_study_file_ai_chunks(
    uuid,
    text,
    integer,
    integer,
    jsonb
)
from anon;

revoke all
on function public.replace_study_file_ai_chunks(
    uuid,
    text,
    integer,
    integer,
    jsonb
)
from authenticated;

grant execute
on function public.replace_study_file_ai_chunks(
    uuid,
    text,
    integer,
    integer,
    jsonb
)
to service_role;

commit;
