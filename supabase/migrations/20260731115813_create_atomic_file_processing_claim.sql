-- File: create_atomic_file_processing_claim.sql
-- Purpose: Allows a trusted background worker to atomically
-- claim one queued file-processing job without duplicate work.

begin;

create or replace function public.claim_next_file_processing_job()
returns table (
  processing_job_id uuid,
  study_file_id uuid
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_processing_job_id uuid;
  v_study_file_id uuid;
begin
  select
    processing_job.id,
    processing_job.study_file_id
  into
    v_processing_job_id,
    v_study_file_id
  from public.file_processing_jobs as processing_job
  inner join public.study_files as study_file
    on study_file.id = processing_job.study_file_id
  where processing_job.status = 'queued'
    and study_file.processing_status = 'queued'
  order by
    processing_job.updated_at asc,
    processing_job.id asc
  for update of processing_job, study_file
  skip locked
  limit 1;

  if v_processing_job_id is null then
    return;
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
  where id = v_processing_job_id
    and status = 'queued';

  if not found then
    raise exception
      'The queued processing job could not be claimed.'
      using errcode = 'P0001';
  end if;

  update public.study_files
  set
    processing_status = 'reading',
    processed_at = null,
    failure_code = null,
    failure_message = null,
    updated_at = now()
  where id = v_study_file_id
    and processing_status = 'queued';

  if not found then
    raise exception
      'The queued study file could not be claimed.'
      using errcode = 'P0002';
  end if;

  return query
  select
    v_processing_job_id,
    v_study_file_id;
end;
$$;

revoke all
on function public.claim_next_file_processing_job()
from public, anon, authenticated;

grant execute
on function public.claim_next_file_processing_job()
to service_role;

commit;