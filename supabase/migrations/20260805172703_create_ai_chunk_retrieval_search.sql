-- File: /supabase/migrations/20260805172703_create_ai_chunk_retrieval_search.sql
-- Purpose: Adds the trusted Phase 5A cosine-similarity search RPC
-- for retrieving owned, ready, vector-indexed study-material chunks.

-- ============================================================
-- STUDY-MATERIAL AI CHUNK RETRIEVAL
-- ============================================================

create or replace function public.search_study_file_ai_chunks(
    p_user_id uuid,
    p_query_embedding jsonb,
    p_match_count integer default 8,
    p_similarity_threshold double precision default 0.60,
    p_study_file_id uuid default null,
    p_subject_id uuid default null
)
returns table (
    chunk_id uuid,
    study_file_id uuid,
    subject_id uuid,
    source_name text,
    chunk_index integer,
    content text,
    start_offset integer,
    end_offset integer,
    chunk_metadata jsonb,
    embedding_model text,
    similarity_score double precision
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
    v_query_vector extensions.vector(768);
begin
    -- --------------------------------------------------------
    -- REQUIRED IDENTITY VALIDATION
    -- --------------------------------------------------------

    if p_user_id is null then
        raise exception
            'The retrieval user ID is required.'
            using errcode = '22023';
    end if;

    -- --------------------------------------------------------
    -- RESULT-LIMIT VALIDATION
    -- --------------------------------------------------------

    if p_match_count is null
        or p_match_count < 1
        or p_match_count > 20 then
        raise exception
            'The retrieval match count must be between 1 and 20.'
            using errcode = '22023';
    end if;

    -- --------------------------------------------------------
    -- SIMILARITY-THRESHOLD VALIDATION
    -- --------------------------------------------------------

    if p_similarity_threshold is null
        or p_similarity_threshold < 0::double precision
        or p_similarity_threshold > 1::double precision then
        raise exception
            'The similarity threshold must be between 0 and 1.'
            using errcode = '22023';
    end if;

    -- --------------------------------------------------------
    -- QUERY-EMBEDDING JSON VALIDATION
    -- --------------------------------------------------------

    if p_query_embedding is null then
        raise exception
            'The query embedding is required.'
            using errcode = '22023';
    end if;

    if jsonb_typeof(
        p_query_embedding
    ) is distinct from 'array' then
        raise exception
            'The query embedding must be a JSON array.'
            using errcode = '22023';
    end if;

    if jsonb_array_length(
        p_query_embedding
    ) <> 768 then
        raise exception
            'The query embedding must contain exactly 768 values.'
            using errcode = '22023';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(
            p_query_embedding
        ) as query_element(value)
        where jsonb_typeof(
            query_element.value
        ) is distinct from 'number'
    ) then
        raise exception
            'Every query embedding value must be numeric.'
            using errcode = '22023';
    end if;

    if not exists (
        select 1
        from jsonb_array_elements(
            p_query_embedding
        ) as query_element(value)
        where (
            query_element.value::text
        )::numeric <> 0
    ) then
        raise exception
            'The query embedding cannot be a zero vector.'
            using errcode = '22023';
    end if;

    -- --------------------------------------------------------
    -- QUERY-VECTOR CONVERSION
    -- --------------------------------------------------------

    begin
        v_query_vector := cast(
            p_query_embedding::text
            as extensions.vector(768)
        );
    exception
        when others then
            raise exception
                'The query embedding could not be converted '
                'to a 768-dimensional vector.'
                using errcode = '22023';
    end;

    -- --------------------------------------------------------
    -- OWNED COSINE-SIMILARITY SEARCH
    -- --------------------------------------------------------

    return query
    select
        ai_chunk.id as chunk_id,
        ai_chunk.study_file_id,
        study_file.subject_id,
        ai_chunk.source_name,
        ai_chunk.chunk_index,
        ai_chunk.content,
        ai_chunk.start_offset,
        ai_chunk.end_offset,
        ai_chunk.chunk_metadata,
        ai_chunk.embedding_model,
        (
            1::double precision
            - (
                ai_chunk.embedding
                operator(extensions.<=>)
                v_query_vector
            )
        ) as similarity_score
    from public.study_file_ai_chunks as ai_chunk
    inner join public.study_files as study_file
        on study_file.id = ai_chunk.study_file_id
    where ai_chunk.user_id = p_user_id
      and study_file.user_id = p_user_id
      and study_file.processing_status = 'ready'
      and ai_chunk.embedding_dimensions = 768
      and ai_chunk.embedding_task_type
        = 'retrieval_document'
      and (
          p_study_file_id is null
          or ai_chunk.study_file_id
            = p_study_file_id
      )
      and (
          p_subject_id is null
          or study_file.subject_id
            = p_subject_id
      )
      and (
          ai_chunk.embedding
          operator(extensions.<=>)
          v_query_vector
      ) <= (
          1::double precision
          - p_similarity_threshold
      )
    order by
        ai_chunk.embedding
            operator(extensions.<=>)
            v_query_vector asc,
        ai_chunk.study_file_id asc,
        ai_chunk.chunk_index asc
    limit p_match_count;
end;
$$;

comment on function public.search_study_file_ai_chunks(
    uuid,
    jsonb,
    integer,
    double precision,
    uuid,
    uuid
) is
    'Returns ranked, owned, ready study-material AI chunks '
    'using a validated 768-dimensional cosine-similarity query.';

-- ============================================================
-- FUNCTION EXECUTION SECURITY
-- ============================================================

revoke all
on function public.search_study_file_ai_chunks(
    uuid,
    jsonb,
    integer,
    double precision,
    uuid,
    uuid
)
from public;

revoke all
on function public.search_study_file_ai_chunks(
    uuid,
    jsonb,
    integer,
    double precision,
    uuid,
    uuid
)
from anon;

revoke all
on function public.search_study_file_ai_chunks(
    uuid,
    jsonb,
    integer,
    double precision,
    uuid,
    uuid
)
from authenticated;

grant execute
on function public.search_study_file_ai_chunks(
    uuid,
    jsonb,
    integer,
    double precision,
    uuid,
    uuid
)
to service_role;
