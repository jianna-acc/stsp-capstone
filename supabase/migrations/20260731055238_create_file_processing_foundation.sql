-- File: /supabase/migrations/20260731055238_create_file_processing_foundation.sql
-- Purpose: Creates the database foundation for asynchronous
-- learning-material extraction, processing, and chunking.

begin;

-- ============================================================
-- Shared updated_at trigger function
-- ============================================================

create or replace function public.set_current_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ============================================================
-- Expand study_files processing statuses
-- ============================================================

do $$
declare
  constraint_record record;
begin
  for constraint_record in
    select conname
    from pg_constraint
    where conrelid = 'public.study_files'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%processing_status%'
  loop
    execute format(
      'alter table public.study_files drop constraint %I',
      constraint_record.conname
    );
  end loop;
end;
$$;

alter table public.study_files
  add constraint study_files_processing_status_allowed
  check (
    processing_status in (
      'uploading',
      'queued',
      'reading',
      'indexing',
      'ready',
      'failed'
    )
  );

-- ============================================================
-- File processing jobs
-- ============================================================

create table public.file_processing_jobs (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null
    references auth.users(id)
    on delete cascade,

  study_file_id uuid not null unique
    references public.study_files(id)
    on delete cascade,

  status text not null default 'queued'
    check (
      status in (
        'queued',
        'processing',
        'completed',
        'failed'
      )
    ),

  attempt_count integer not null default 0
    check (attempt_count >= 0),

  started_at timestamptz,
  completed_at timestamptz,

  error_code text,
  error_message text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index file_processing_jobs_user_id_idx
  on public.file_processing_jobs(user_id);

create index file_processing_jobs_status_idx
  on public.file_processing_jobs(status);

create index file_processing_jobs_created_at_idx
  on public.file_processing_jobs(created_at);

create trigger file_processing_jobs_set_updated_at
before update on public.file_processing_jobs
for each row
execute function public.set_current_updated_at();

-- ============================================================
-- Extracted complete file content
-- ============================================================

create table public.study_file_contents (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null
    references auth.users(id)
    on delete cascade,

  study_file_id uuid not null unique
    references public.study_files(id)
    on delete cascade,

  extracted_text text not null default '',

  page_count integer
    check (
      page_count is null
      or page_count >= 0
    ),

  slide_count integer
    check (
      slide_count is null
      or slide_count >= 0
    ),

  sheet_count integer
    check (
      sheet_count is null
      or sheet_count >= 0
    ),

  character_count integer not null default 0
    check (character_count >= 0),

  extraction_metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index study_file_contents_user_id_idx
  on public.study_file_contents(user_id);

create trigger study_file_contents_set_updated_at
before update on public.study_file_contents
for each row
execute function public.set_current_updated_at();

-- ============================================================
-- Smaller searchable file chunks
-- ============================================================

create table public.study_file_chunks (
  id uuid primary key default gen_random_uuid(),

  user_id uuid not null
    references auth.users(id)
    on delete cascade,

  study_file_id uuid not null
    references public.study_files(id)
    on delete cascade,

  chunk_index integer not null
    check (chunk_index >= 0),

  content text not null
    check (length(trim(content)) > 0),

  locator_type text
    check (
      locator_type is null
      or locator_type in (
        'page',
        'slide',
        'sheet',
        'section',
        'document'
      )
    ),

  locator_label text,

  token_count integer
    check (
      token_count is null
      or token_count >= 0
    ),

  chunk_metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),

  constraint study_file_chunks_file_index_unique
    unique (study_file_id, chunk_index)
);

create index study_file_chunks_user_id_idx
  on public.study_file_chunks(user_id);

create index study_file_chunks_study_file_id_idx
  on public.study_file_chunks(study_file_id);

create index study_file_chunks_locator_type_idx
  on public.study_file_chunks(locator_type);

-- ============================================================
-- Row Level Security
-- ============================================================

alter table public.file_processing_jobs
  enable row level security;

alter table public.study_file_contents
  enable row level security;

alter table public.study_file_chunks
  enable row level security;

-- ============================================================
-- file_processing_jobs policies
-- ============================================================

create policy file_processing_jobs_select_own
on public.file_processing_jobs
for select
to authenticated
using (
  user_id = auth.uid()
);

create policy file_processing_jobs_insert_own
on public.file_processing_jobs
for insert
to authenticated
with check (
  user_id = auth.uid()
  and exists (
    select 1
    from public.study_files
    where study_files.id =
      file_processing_jobs.study_file_id
      and study_files.user_id =
        auth.uid()
  )
);

create policy file_processing_jobs_update_own
on public.file_processing_jobs
for update
to authenticated
using (
  user_id = auth.uid()
)
with check (
  user_id = auth.uid()
  and exists (
    select 1
    from public.study_files
    where study_files.id =
      file_processing_jobs.study_file_id
      and study_files.user_id =
        auth.uid()
  )
);

create policy file_processing_jobs_delete_own
on public.file_processing_jobs
for delete
to authenticated
using (
  user_id = auth.uid()
);

-- ============================================================
-- study_file_contents policies
-- ============================================================

create policy study_file_contents_select_own
on public.study_file_contents
for select
to authenticated
using (
  user_id = auth.uid()
);

create policy study_file_contents_insert_own
on public.study_file_contents
for insert
to authenticated
with check (
  user_id = auth.uid()
  and exists (
    select 1
    from public.study_files
    where study_files.id =
      study_file_contents.study_file_id
      and study_files.user_id =
        auth.uid()
  )
);

create policy study_file_contents_update_own
on public.study_file_contents
for update
to authenticated
using (
  user_id = auth.uid()
)
with check (
  user_id = auth.uid()
  and exists (
    select 1
    from public.study_files
    where study_files.id =
      study_file_contents.study_file_id
      and study_files.user_id =
        auth.uid()
  )
);

create policy study_file_contents_delete_own
on public.study_file_contents
for delete
to authenticated
using (
  user_id = auth.uid()
);

-- ============================================================
-- study_file_chunks policies
-- ============================================================

create policy study_file_chunks_select_own
on public.study_file_chunks
for select
to authenticated
using (
  user_id = auth.uid()
);

create policy study_file_chunks_insert_own
on public.study_file_chunks
for insert
to authenticated
with check (
  user_id = auth.uid()
  and exists (
    select 1
    from public.study_files
    where study_files.id =
      study_file_chunks.study_file_id
      and study_files.user_id =
        auth.uid()
  )
);

create policy study_file_chunks_update_own
on public.study_file_chunks
for update
to authenticated
using (
  user_id = auth.uid()
)
with check (
  user_id = auth.uid()
  and exists (
    select 1
    from public.study_files
    where study_files.id =
      study_file_chunks.study_file_id
      and study_files.user_id =
        auth.uid()
  )
);

create policy study_file_chunks_delete_own
on public.study_file_chunks
for delete
to authenticated
using (
  user_id = auth.uid()
);

commit;
