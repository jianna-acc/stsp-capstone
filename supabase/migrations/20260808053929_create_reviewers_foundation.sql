-- File: /supabase/migrations/20260808053929_create_reviewers_foundation.sql
-- Purpose: Creates the persistent reviewer foundation, ownership validation,
-- indexes, timestamps, privileges, and Row Level Security policies.

create table public.reviewers (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    subject_id uuid not null
        references public.subjects(id)
        on delete cascade,

    study_file_id uuid
        references public.study_files(id)
        on delete cascade,

    scope_type text not null,

    title text not null,

    reviewer_length text not null,

    content jsonb not null,

    sources jsonb not null
        default '[]'::jsonb,

    generation_model text not null,

    generation_count integer not null
        default 1,

    generated_at timestamptz not null
        default now(),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint reviewers_scope_type_check
        check (
            scope_type in (
                'subject',
                'file'
            )
        ),

    constraint reviewers_scope_file_check
        check (
            (
                scope_type = 'file'
                and study_file_id is not null
            )
            or
            (
                scope_type = 'subject'
                and study_file_id is null
            )
        ),

    constraint reviewers_title_check
        check (
            char_length(
                btrim(title)
            ) between 1 and 160
        ),

    constraint reviewers_length_check
        check (
            reviewer_length in (
                'short',
                'medium',
                'long'
            )
        ),

    constraint reviewers_content_object_check
        check (
            jsonb_typeof(content) = 'object'
        ),

    constraint reviewers_sources_array_check
        check (
            jsonb_typeof(sources) = 'array'
        ),

    constraint reviewers_generation_model_check
        check (
            char_length(
                btrim(generation_model)
            ) >= 1
        ),

    constraint reviewers_generation_count_check
        check (
            generation_count >= 1
        )
);


create index reviewers_user_created_at_idx
    on public.reviewers (
        user_id,
        created_at desc
    );


create index reviewers_user_subject_idx
    on public.reviewers (
        user_id,
        subject_id
    );


create index reviewers_user_study_file_idx
    on public.reviewers (
        user_id,
        study_file_id
    )
    where study_file_id is not null;


create or replace function public.validate_reviewer_ownership_scope()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
    if not exists (
        select 1
        from public.subjects
        where id = new.subject_id
          and user_id = new.user_id
    ) then
        raise exception
            'Reviewer subject does not belong to the reviewer owner.'
            using errcode = '23514';
    end if;

    if new.scope_type = 'file' then
        if new.study_file_id is null then
            raise exception
                'File-scope reviewer requires a study file.'
                using errcode = '23514';
        end if;

        if not exists (
            select 1
            from public.study_files
            where id = new.study_file_id
              and user_id = new.user_id
              and subject_id = new.subject_id
        ) then
            raise exception
                'Reviewer study file does not belong to the reviewer owner and subject.'
                using errcode = '23514';
        end if;
    elsif new.scope_type = 'subject' then
        if new.study_file_id is not null then
            raise exception
                'Subject-scope reviewer cannot store a study file.'
                using errcode = '23514';
        end if;
    end if;

    return new;
end;
$$;


create trigger reviewers_validate_ownership_scope
before insert or update of
    user_id,
    subject_id,
    study_file_id,
    scope_type
on public.reviewers
for each row
execute function public.validate_reviewer_ownership_scope();


create or replace function public.set_reviewer_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
    new.updated_at = now();

    return new;
end;
$$;


create trigger reviewers_set_updated_at
before update
on public.reviewers
for each row
execute function public.set_reviewer_updated_at();


alter table public.reviewers
enable row level security;


revoke all
on table public.reviewers
from anon;


revoke all
on table public.reviewers
from authenticated;


grant select, delete
on table public.reviewers
to authenticated;


grant all
on table public.reviewers
to service_role;


create policy "reviewers_select_own"
on public.reviewers
for select
to authenticated
using (
    auth.uid() = user_id
);


create policy "reviewers_delete_own"
on public.reviewers
for delete
to authenticated
using (
    auth.uid() = user_id
);