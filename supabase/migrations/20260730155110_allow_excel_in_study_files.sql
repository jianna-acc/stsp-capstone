-- File: /supabase/migrations/<timestamp>_allow_excel_in_study_files.sql
-- Purpose: Allows legacy and modern Excel spreadsheets in
-- study-file records and the private study-materials bucket.

-- The PowerPoint migration created this named constraint.
-- Replace it with an expanded version that also allows Excel.
alter table public.study_files
  drop constraint if exists study_files_mime_type_allowed;

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
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ]::text[]
    )
  );

-- Keep the private Storage bucket restrictions aligned
-- with the study_files table constraint.
update storage.buckets
set allowed_mime_types = array[
  'application/pdf',
  'text/plain',
  'image/jpeg',
  'image/png',
  'image/webp',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]::text[]
where id = 'study-materials';