-- File: /supabase/migrations/20260730151528_allow_powerpoint_in_study_files.sql
-- Purpose: Allows PowerPoint files in study-file records and
-- in the private study-materials Storage bucket.

-- Remove existing study_files CHECK constraints that validate mime_type.
do $$
declare
  constraint_record record;
begin
  for constraint_record in
    select
      conname
    from pg_constraint
    where conrelid = 'public.study_files'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%mime_type%'
  loop
    execute format(
      'alter table public.study_files drop constraint %I',
      constraint_record.conname
    );
  end loop;
end
$$;

-- Recreate the MIME-type constraint with PowerPoint support.
alter table public.study_files
  add constraint study_files_mime_type_allowed
  check (
    lower(mime_type) = any (
      array[
        'application/pdf',
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      ]::text[]
    )
  );

-- Keep the private Storage bucket restrictions aligned with the table.
update storage.buckets
set allowed_mime_types = array[
  'application/pdf',
  'text/plain',
  'image/jpeg',
  'image/png',
  'image/webp',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
]::text[]
where id = 'study-materials';