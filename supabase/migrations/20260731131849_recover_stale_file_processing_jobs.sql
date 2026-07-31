-- File: /supabase/migrations/<timestamp>_recover_stale_file_processing_jobs.sql
-- Purpose: Requeues abandoned file-processing jobs or marks
-- them failed after the maximum number of attempts.

begin;

create or replace function public.recover_stale_file_processing_jobs(
  p_stale_after_minutes integer default 30,
  p_max_attempts integer default 3
)
returns table (
  requeued_count integer,
  failed_count integer
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_requeued_count integer := 0;
  v_failed_count integer := 0;
begin
  if p_stale_after_minutes < 1 then
    raise exception
      'p_stale_after_minutes must be at least 1.'
      using errcode = '22023';
  end if;

  if p_max_attempts < 1 then
    raise exception
      'p_max_attempts must be at least 1.'
      using errcode = '22023';
  end if;

  with stale_jobs as (
    select
      processing_job.id,
      processing_job.study_file_id
    from public.file_processing_jobs as processing_job
    inner join public.study_files as study_file
      on study_file.id =
        processing_job.study_file_id
    where processing_job.status = 'processing'
      and study_file.processing_status in (
        'reading',
        'indexing'
      )
      and coalesce(
        processing_job.updated_at,
        processing_job.started_at
      ) <
        now()
        - make_interval(
            mins => p_stale_after_minutes
          )
      and processing_job.attempt_count <
        p_max_attempts
    order by
      processing_job.updated_at asc,
      processing_job.id asc
    for update
      of processing_job,
      study_file
    skip locked
  ),
  requeued_jobs as (
    update public.file_processing_jobs
    set
      status = 'queued',
      started_at = null,
      completed_at = null,
      error_code = 'STALE_JOB_REQUEUED',
      error_message =
        'The previous processing attempt stopped unexpectedly and was requeued.',
      updated_at = now()
    where id in (
      select id
      from stale_jobs
    )
    returning study_file_id
  ),
  requeued_files as (
    update public.study_files
    set
      processing_status = 'queued',
      processed_at = null,
      failure_code = null,
      failure_message = null,
      updated_at = now()
    where id in (
      select study_file_id
      from requeued_jobs
    )
    returning id
  )
  select count(*)::integer
  into v_requeued_count
  from requeued_files;

  with exhausted_jobs as (
    select
      processing_job.id,
      processing_job.study_file_id
    from public.file_processing_jobs as processing_job
    inner join public.study_files as study_file
      on study_file.id =
        processing_job.study_file_id
    where processing_job.status = 'processing'
      and study_file.processing_status in (
        'reading',
        'indexing'
      )
      and coalesce(
        processing_job.updated_at,
        processing_job.started_at
      ) <
        now()
        - make_interval(
            mins => p_stale_after_minutes
          )
      and processing_job.attempt_count >=
        p_max_attempts
    order by
      processing_job.updated_at asc,
      processing_job.id asc
    for update
      of processing_job,
      study_file
    skip locked
  ),
  failed_jobs as (
    update public.file_processing_jobs
    set
      status = 'failed',
      completed_at = now(),
      error_code = 'MAX_PROCESSING_ATTEMPTS',
      error_message =
        'File processing stopped after reaching the maximum number of attempts.',
      updated_at = now()
    where id in (
      select id
      from exhausted_jobs
    )
    returning study_file_id
  ),
  failed_files as (
    update public.study_files
    set
      processing_status = 'failed',
      processed_at = null,
      failure_code = 'MAX_PROCESSING_ATTEMPTS',
      failure_message =
        'The file could not be processed after multiple attempts.',
      updated_at = now()
    where id in (
      select study_file_id
      from failed_jobs
    )
    returning id
  )
  select count(*)::integer
  into v_failed_count
  from failed_files;

  return query
  select
    v_requeued_count,
    v_failed_count;
end;
$$;

revoke all
on function public.recover_stale_file_processing_jobs(
  integer,
  integer
)
from public, anon, authenticated;

grant execute
on function public.recover_stale_file_processing_jobs(
  integer,
  integer
)
to service_role;

commit;