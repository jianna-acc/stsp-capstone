-- File: create_file_processing_queue_function.sql
-- Purpose: Atomically marks a completed Storage upload as queued
-- and creates or resets its file-processing job.

begin;

create or replace function public.queue_study_file_processing(
  p_study_file_id uuid
)
returns setof public.study_files
language plpgsql
security invoker
set search_path = public
as $$
declare
  current_user_id uuid;
  queued_file public.study_files%rowtype;
begin
  current_user_id := auth.uid();

  if current_user_id is null then
    raise exception 'Authentication is required.'
      using errcode = '42501';
  end if;

  /*
   * Lock and verify the student-owned file before changing it.
   */
  select *
  into queued_file
  from public.study_files
  where id = p_study_file_id
    and user_id = current_user_id
  for update;

  if not found then
    raise exception 'The study file was not found.'
      using errcode = 'P0002';
  end if;

  if queued_file.processing_status <> 'uploading' then
    raise exception
      'Only a completed upload can be queued for processing.'
      using errcode = 'P0001';
  end if;

  /*
   * The file has reached Supabase Storage, but its contents have
   * not yet been extracted by FastAPI.
   */
  update public.study_files
  set
    processing_status = 'queued',
    failure_code = null,
    failure_message = null,
    processed_at = null,
    updated_at = now()
  where id = queued_file.id
    and user_id = current_user_id
  returning *
  into queued_file;

  /*
   * Create the first processing job, or reset an existing job
   * when the same failed file was uploaded again.
   */
  insert into public.file_processing_jobs (
    user_id,
    study_file_id,
    status,
    attempt_count,
    started_at,
    completed_at,
    error_code,
    error_message
  )
  values (
    current_user_id,
    queued_file.id,
    'queued',
    0,
    null,
    null,
    null,
    null
  )
  on conflict (study_file_id)
  do update
  set
    user_id = excluded.user_id,
    status = 'queued',
    attempt_count = 0,
    started_at = null,
    completed_at = null,
    error_code = null,
    error_message = null,
    updated_at = now();

  return next queued_file;
end;
$$;

revoke all
on function public.queue_study_file_processing(uuid)
from public;

grant execute
on function public.queue_study_file_processing(uuid)
to authenticated;

commit;