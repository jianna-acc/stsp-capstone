-- File: /supabase/migrations/<TIMESTAMP>_create_subject_file_foundation.sql
-- Purpose: Creates student-owned subjects, study-file metadata,
-- processing states, duplicate protection, and private Storage policies.

begin;

-- ============================================================
-- SUBJECTS
-- ============================================================

create table public.subjects (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    name text not null,
    color text not null default 'violet',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint subjects_name_length
        check (
            char_length(btrim(name))
            between 1 and 80
        ),

    constraint subjects_color_length
        check (
            char_length(btrim(color))
            between 1 and 40
        ),

    constraint subjects_id_user_unique
        unique (id, user_id)
);

comment on table public.subjects is
    'Stores academic subjects created by authenticated students.';

comment on column public.subjects.user_id is
    'The authenticated student who owns the subject.';

comment on column public.subjects.name is
    'Student-facing academic subject name.';

comment on column public.subjects.color is
    'Mantine-compatible color identifier used by the interface.';

create unique index subjects_user_name_unique
    on public.subjects (
        user_id,
        lower(btrim(name))
    );

create index subjects_user_created_at_index
    on public.subjects (
        user_id,
        created_at desc
    );

-- ============================================================
-- STUDY FILES
-- ============================================================

create table public.study_files (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    subject_id uuid not null,

    topic text not null,
    original_filename text not null,
    storage_path text not null,
    mime_type text not null,
    size_bytes bigint not null,

    processing_status text not null
        default 'uploading',

    failure_code text,
    failure_message text,
    processed_at timestamptz,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint study_files_subject_owner_fk
        foreign key (subject_id, user_id)
        references public.subjects(id, user_id)
        on delete restrict,

    constraint study_files_topic_length
        check (
            char_length(btrim(topic))
            between 1 and 120
        ),

    constraint study_files_filename_length
        check (
            char_length(btrim(original_filename))
            between 1 and 255
        ),

    constraint study_files_filename_has_no_path
        check (
            position('/' in original_filename) = 0
            and position('\' in original_filename) = 0
        ),

    constraint study_files_storage_path_length
        check (
            char_length(btrim(storage_path))
            between 1 and 1024
        ),

    constraint study_files_storage_path_unique
        unique (storage_path),

    constraint study_files_supported_mime_type
        check (
            mime_type in (
                'application/pdf',
                'text/plain',
                'image/jpeg',
                'image/png',
                'image/webp'
            )
        ),

    constraint study_files_size_range
        check (
            size_bytes between 1 and 20971520
        ),

    constraint study_files_processing_status_allowed
        check (
            processing_status in (
                'uploading',
                'reading',
                'indexing',
                'ready',
                'failed'
            )
        ),

    constraint study_files_failure_code_length
        check (
            failure_code is null
            or char_length(failure_code) <= 80
        ),

    constraint study_files_failure_message_length
        check (
            failure_message is null
            or char_length(failure_message) <= 500
        )
);

comment on table public.study_files is
    'Stores metadata and processing states for private student learning materials.';

comment on column public.study_files.topic is
    'Student-provided topic describing the learning material.';

comment on column public.study_files.original_filename is
    'Original filename displayed to the student.';

comment on column public.study_files.storage_path is
    'Private object path inside the study-materials Storage bucket.';

comment on column public.study_files.processing_status is
    'Internal status: uploading, reading, indexing, ready, or failed.';

comment on column public.study_files.failure_message is
    'Safe student-facing failure explanation without internal technical details.';

create unique index study_files_user_subject_filename_unique
    on public.study_files (
        user_id,
        subject_id,
        lower(btrim(original_filename))
    );

create index study_files_user_subject_created_index
    on public.study_files (
        user_id,
        subject_id,
        created_at desc
    );

create index study_files_user_status_index
    on public.study_files (
        user_id,
        processing_status
    );

-- ============================================================
-- UPDATED-AT TRIGGERS
-- ============================================================

create or replace function public.set_subject_file_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

comment on function public.set_subject_file_updated_at() is
    'Refreshes updated_at for Phase 3 subject and file records.';

create trigger subjects_set_updated_at
before update on public.subjects
for each row
execute function public.set_subject_file_updated_at();

create trigger study_files_set_updated_at
before update on public.study_files
for each row
execute function public.set_subject_file_updated_at();

-- ============================================================
-- TABLE PERMISSIONS
-- ============================================================

revoke all on table public.subjects from anon;
revoke all on table public.study_files from anon;

grant select, insert, update, delete
    on table public.subjects
    to authenticated;

grant select, insert, update, delete
    on table public.study_files
    to authenticated;

grant all
    on table public.subjects
    to service_role;

grant all
    on table public.study_files
    to service_role;

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.subjects
    enable row level security;

alter table public.study_files
    enable row level security;

create policy subjects_select_own
on public.subjects
for select
to authenticated
using (
    user_id = (select auth.uid())
);

create policy subjects_insert_own
on public.subjects
for insert
to authenticated
with check (
    user_id = (select auth.uid())
);

create policy subjects_update_own
on public.subjects
for update
to authenticated
using (
    user_id = (select auth.uid())
)
with check (
    user_id = (select auth.uid())
);

create policy subjects_delete_own
on public.subjects
for delete
to authenticated
using (
    user_id = (select auth.uid())
);

create policy study_files_select_own
on public.study_files
for select
to authenticated
using (
    user_id = (select auth.uid())
);

create policy study_files_insert_own
on public.study_files
for insert
to authenticated
with check (
    user_id = (select auth.uid())
    and exists (
        select 1
        from public.subjects
        where subjects.id = study_files.subject_id
          and subjects.user_id = (select auth.uid())
    )
);

create policy study_files_update_own
on public.study_files
for update
to authenticated
using (
    user_id = (select auth.uid())
)
with check (
    user_id = (select auth.uid())
    and exists (
        select 1
        from public.subjects
        where subjects.id = study_files.subject_id
          and subjects.user_id = (select auth.uid())
    )
);

create policy study_files_delete_own
on public.study_files
for delete
to authenticated
using (
    user_id = (select auth.uid())
);

-- ============================================================
-- PRIVATE STORAGE BUCKET
-- ============================================================

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'study-materials',
    'study-materials',
    false,
    20971520,
    array[
        'application/pdf',
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/webp'
    ]::text[]
)
on conflict (id)
do update set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

-- Object paths must begin with the authenticated student's UUID:
--
-- USER_ID/SUBJECT_ID/FILE_ID/SAFE_FILENAME
--
-- Example:
-- 5a1.../ac2.../7de.../lecture-1.pdf

drop policy if exists study_materials_insert_own
    on storage.objects;

create policy study_materials_insert_own
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'study-materials'
    and (storage.foldername(name))[1]
        = (select auth.uid()::text)
);

drop policy if exists study_materials_select_own
    on storage.objects;

create policy study_materials_select_own
on storage.objects
for select
to authenticated
using (
    bucket_id = 'study-materials'
    and (storage.foldername(name))[1]
        = (select auth.uid()::text)
);

drop policy if exists study_materials_delete_own
    on storage.objects;

create policy study_materials_delete_own
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'study-materials'
    and (storage.foldername(name))[1]
        = (select auth.uid()::text)
);

commit;