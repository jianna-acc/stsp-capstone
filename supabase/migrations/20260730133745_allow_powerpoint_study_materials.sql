-- File: /supabase/migrations/<timestamp>_allow_powerpoint_study_materials.sql
-- Purpose: Allows legacy and modern PowerPoint files in the
-- private study-materials Storage bucket.

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