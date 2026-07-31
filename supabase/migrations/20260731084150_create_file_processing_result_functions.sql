-- File: create_file_processing_result_functions.sql
-- Purpose: Adds transactional database functions for starting,
-- indexing, completing, and failing file-processing jobs.

begin;

-- ============================================================
-- Start processing
-- ============================================================

create or replace function public.start_study_file_processing(
  p_study_file_id uuid
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.study_files
  set
    processing_status = 'reading',
    failure_code = null,
    failure_message = null,
    processed_at = null,
    updated_at = now()
  where id = p_study_file_id
    and processing_status = 'queued';

  if not found then
    raise exception
      'Only a queued study file can begin processing.'
      using errcode = 'P0001';
  end if;

  update public.file_processing_jobs
  set
    status = 'processing',
    attempt_count = attempt_count + 1,
    started_at = now(),
    completed_at = null,
    error_code = null,
    error_message = null,
    updated_at = now()
  where study_file_id = p_study_file_id
    and status = 'queued';

  if not found then
    raise exception
      'A queued processing job was not found.'
      using errcode = 'P0002';
  end if;
end;
$$;

-- ============================================================
-- Mark indexing
-- ============================================================

create or replace function public.mark_study_file_indexing(
  p_study_file_id uuid
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.study_files
  set
    processing_status = 'indexing',
    updated_at = now()
  where id = p_study_file_id
    and processing_status = 'reading';

  if not found then
    raise exception
      'Only a file being read can move to indexing.'
      using errcode = 'P0001';

  end if;

  if not exists (
    select 1
    from public.file_processing_jobs
    where study_file_id = p_study_file_id
      and status = 'processing'
  ) then
    raise exception
      'An active processing job was not found.'
      using errcode = 'P0002';
  end if;
end;
$$;

-- ============================================================
-- Complete processing
-- ============================================================

create or replace function public.complete_study_file_processing(
  p_study_file_id uuid,
  p_extracted_text text,
  p_page_count integer,
  p_slide_count integer,
  p_sheet_count integer,
  p_character_count integer,
  p_extraction_metadata jsonb,
  p_chunks jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_chunk jsonb;
begin
  if nullif(trim(p_extracted_text), '') is null then
    raise exception
      'Extracted text cannot be empty.'
      using errcode = '22023';
  end if;

  if p_character_count < 1 then
    raise exception
      'Character count must be greater than zero.'
      using errcode = '22023';
  end if;

  if p_chunks is null
    or jsonb_typeof(p_chunks) <> 'array'
    or jsonb_array_length(p_chunks) = 0 then
    raise exception
      'At least one extracted chunk is required.'
      using errcode = '22023';
  end if;

  select user_id
  into v_user_id
  from public.study_files
  where id = p_study_file_id
    and processing_status = 'indexing'
  for update;

  if not found then
    raise exception
      'Only an indexing study file can be completed.'
      using errcode = 'P0001';
  end if;

  if not exists (
    select 1
    from public.file_processing_jobs
    where study_file_id = p_study_file_id
      and status = 'processing'
  ) then
    raise exception
      'An active processing job was not found.'
      using errcode = 'P0002';
  end if;

  insert into public.study_file_contents (
    user_id,
    study_file_id,
    extracted_text,
    page_count,
    slide_count,
    sheet_count,
    character_count,
    extraction_metadata
  )
  values (
    v_user_id,
    p_study_file_id,
    p_extracted_text,
    p_page_count,
    p_slide_count,
    p_sheet_count,
    p_character_count,
    coalesce(
      p_extraction_metadata,
      '{}'::jsonb
    )
  )
  on conflict (study_file_id)
  do update
  set
    user_id = excluded.user_id,
    extracted_text = excluded.extracted_text,
    page_count = excluded.page_count,
    slide_count = excluded.slide_count,
    sheet_count = excluded.sheet_count,
    character_count = excluded.character_count,
    extraction_metadata =
      excluded.extraction_metadata,
    updated_at = now();

  delete from public.study_file_chunks
  where study_file_id = p_study_file_id;

  for v_chunk in
    select value
    from jsonb_array_elements(p_chunks)
  loop
    insert into public.study_file_chunks (
      user_id,
      study_file_id,
      chunk_index,
      content,
      locator_type,
      locator_label,
      token_count,
      chunk_metadata
    )
    values (
      v_user_id,
      p_study_file_id,
      (v_chunk ->> 'chunk_index')::integer,
      v_chunk ->> 'content',
      nullif(
        v_chunk ->> 'locator_type',
        ''
      ),
      nullif(
        v_chunk ->> 'locator_label',
        ''
      ),
      nullif(
        v_chunk ->> 'token_count',
        ''
      )::integer,
      coalesce(
        v_chunk -> 'metadata',
        '{}'::jsonb
      )
    );
  end loop;

  update public.file_processing_jobs
  set
    status = 'completed',
    completed_at = now(),
    error_code = null,
    error_message = null,
    updated_at = now()
  where study_file_id = p_study_file_id
    and status = 'processing';

  if not found then
    raise exception
      'The processing job could not be completed.'
      using errcode = 'P0002';
  end if;

  update public.study_files
  set
    processing_status = 'ready',
    processed_at = now(),
    failure_code = null,
    failure_message = null,
    updated_at = now()
  where id = p_study_file_id
    and processing_status = 'indexing';

  if not found then
    raise exception
      'The study file could not be marked ready.'
      using errcode = 'P0002';
  end if;
end;
$$;

-- ============================================================
-- Fail processing
-- ============================================================

create or replace function public.fail_study_file_processing(
  p_study_file_id uuid,
  p_error_code text,
  p_error_message text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.study_files
  set
    processing_status = 'failed',
    failure_code = left(
      coalesce(
        nullif(trim(p_error_code), ''),
        'PROCESSING_FAILED'
      ),
      100
    ),
    failure_message = left(
      coalesce(
        nullif(trim(p_error_message), ''),
        'The file could not be processed.'
      ),
      1000
    ),
    processed_at = null,
    updated_at = now()
  where id = p_study_file_id
    and processing_status in (
      'queued',
      'reading',
      'indexing'
    );

  update public.file_processing_jobs
  set
    status = 'failed',
    completed_at = now(),
    error_code = left(
      coalesce(
        nullif(trim(p_error_code), ''),
        'PROCESSING_FAILED'
      ),
      100
    ),
    error_message = left(
      coalesce(
        nullif(trim(p_error_message), ''),
        'The file could not be processed.'
      ),
      1000
    ),
    updated_at = now()
  where study_file_id = p_study_file_id
    and status in (
      'queued',
      'processing'
    );
end;
$$;

-- ============================================================
-- Permissions
-- ============================================================

revoke all
on function public.start_study_file_processing(uuid)
from public, anon, authenticated;

revoke all
on function public.mark_study_file_indexing(uuid)
from public, anon, authenticated;

revoke all
on function public.complete_study_file_processing(
  uuid,
  text,
  integer,
  integer,
  integer,
  integer,
  jsonb,
  jsonb
)
from public, anon, authenticated;

revoke all
on function public.fail_study_file_processing(
  uuid,
  text,
  text
)
from public, anon, authenticated;

grant execute
on function public.start_study_file_processing(uuid)
to service_role;

grant execute
on function public.mark_study_file_indexing(uuid)
to service_role;

grant execute
on function public.complete_study_file_processing(
  uuid,
  text,
  integer,
  integer,
  integer,
  integer,
  jsonb,
  jsonb
)
to service_role;

grant execute
on function public.fail_study_file_processing(
  uuid,
  text,
  text
)
to service_role;

commit;