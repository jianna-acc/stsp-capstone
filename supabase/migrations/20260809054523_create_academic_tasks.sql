-- File: /supabase/migrations/20260809054523_create_academic_tasks.sql
-- Purpose: Adds student-owned academic tasks with subject linkage,
-- deadlines, workload estimates, difficulty, task type, status,
-- validation, indexes, timestamps, and Row Level Security.

create table public.academic_tasks (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        default auth.uid()
        references auth.users(id)
        on delete cascade,

    subject_id uuid not null
        references public.subjects(id)
        on delete cascade,

    title text not null,

    description text,

    deadline timestamptz not null,

    estimated_minutes integer not null,

    difficulty text not null,

    task_type text not null,

    status text not null default 'pending',

    created_at timestamptz not null default now(),

    updated_at timestamptz not null default now(),

    constraint academic_tasks_title_not_blank
        check (
            char_length(btrim(title)) between 1 and 200
        ),

    constraint academic_tasks_description_length
        check (
            description is null
            or char_length(description) <= 5000
        ),

    constraint academic_tasks_estimated_minutes_range
        check (
            estimated_minutes between 1 and 10080
        ),

    constraint academic_tasks_difficulty_valid
        check (
            difficulty in (
                'easy',
                'medium',
                'hard'
            )
        ),

    constraint academic_tasks_task_type_valid
        check (
            task_type in (
                'assignment',
                'project',
                'exam',
                'quiz',
                'reading',
                'presentation',
                'research',
                'other'
            )
        ),

    constraint academic_tasks_status_valid
        check (
            status in (
                'pending',
                'in_progress',
                'completed',
                'cancelled'
            )
        )
);


-- ============================================================
-- Subject ownership integrity
-- ============================================================

create or replace function public.validate_academic_task_subject()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if not exists (
        select 1
        from public.subjects
        where subjects.id = new.subject_id
          and subjects.user_id = new.user_id
    ) then
        raise exception
            'Academic task subject must belong to the same student.';
    end if;

    return new;
end;
$$;


create trigger validate_academic_task_subject_trigger
before insert or update of user_id, subject_id
on public.academic_tasks
for each row
execute function public.validate_academic_task_subject();


-- ============================================================
-- Automatic updated_at handling
-- ============================================================

create or replace function public.set_academic_task_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


create trigger set_academic_task_updated_at_trigger
before update
on public.academic_tasks
for each row
execute function public.set_academic_task_updated_at();


-- ============================================================
-- Indexes
-- ============================================================

create index academic_tasks_user_id_idx
    on public.academic_tasks(user_id);


create index academic_tasks_subject_id_idx
    on public.academic_tasks(subject_id);


create index academic_tasks_user_deadline_idx
    on public.academic_tasks(user_id, deadline);


create index academic_tasks_user_status_idx
    on public.academic_tasks(user_id, status);


create index academic_tasks_user_subject_idx
    on public.academic_tasks(user_id, subject_id);


-- ============================================================
-- Row Level Security
-- ============================================================

alter table public.academic_tasks
enable row level security;


create policy "Students can view their own academic tasks"
on public.academic_tasks
for select
to authenticated
using (
    user_id = auth.uid()
);


create policy "Students can create their own academic tasks"
on public.academic_tasks
for insert
to authenticated
with check (
    user_id = auth.uid()
    and exists (
        select 1
        from public.subjects
        where subjects.id = academic_tasks.subject_id
          and subjects.user_id = auth.uid()
    )
);


create policy "Students can update their own academic tasks"
on public.academic_tasks
for update
to authenticated
using (
    user_id = auth.uid()
)
with check (
    user_id = auth.uid()
    and exists (
        select 1
        from public.subjects
        where subjects.id = academic_tasks.subject_id
          and subjects.user_id = auth.uid()
    )
);


create policy "Students can delete their own academic tasks"
on public.academic_tasks
for delete
to authenticated
using (
    user_id = auth.uid()
);


-- ============================================================
-- Permissions
-- ============================================================

grant select, insert, update, delete
on public.academic_tasks
to authenticated;