-- File: /supabase/migrations/20260810002500_create_study_plans_foundation.sql
-- Purpose: Creates student-owned study plans and scheduled study
-- sessions without depending on the unfinished Academic Tasks track.

begin;

-- ============================================================
-- STUDY PLANS
-- ============================================================

create table public.study_plans (
    id uuid primary key
        default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    title text not null,

    starts_on date not null,

    ends_on date not null,

    status text not null
        default 'active',

    generation_mode text not null
        default 'manual',

    generated_at timestamptz,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint study_plans_title_length
        check (
            char_length(btrim(title))
                between 1 and 160
        ),

    constraint study_plans_date_order
        check (
            starts_on <= ends_on
        ),

    constraint study_plans_date_span
        check (
            ends_on - starts_on <= 366
        ),

    constraint study_plans_status_allowed
        check (
            status in (
                'draft',
                'active',
                'completed',
                'archived'
            )
        ),

    constraint study_plans_generation_mode_allowed
        check (
            generation_mode in (
                'manual',
                'generated'
            )
        ),

    constraint study_plans_generation_consistency
        check (
            (
                generation_mode = 'manual'
                and generated_at is null
            )
            or
            (
                generation_mode = 'generated'
                and generated_at is not null
            )
        ),

    constraint study_plans_id_user_unique
        unique (
            id,
            user_id
        )
);

comment on table public.study_plans is
    'Stores dated study plans belonging to authenticated students.';

comment on column public.study_plans.starts_on is
    'First local calendar date covered by the study plan.';

comment on column public.study_plans.ends_on is
    'Last local calendar date covered by the study plan.';

comment on column public.study_plans.generation_mode is
    'Identifies whether the plan was manually created or scheduler generated.';

comment on column public.study_plans.generated_at is
    'Timestamp when an automatically generated plan was created.';


create index study_plans_user_dates_idx
    on public.study_plans (
        user_id,
        starts_on,
        ends_on
    );


create index study_plans_user_status_idx
    on public.study_plans (
        user_id,
        status,
        updated_at desc
    );


-- ============================================================
-- STUDY SESSIONS
-- ============================================================

create table public.study_sessions (
    id uuid primary key
        default gen_random_uuid(),

    study_plan_id uuid not null,

    user_id uuid not null,

    subject_id uuid not null,

    title text not null,

    starts_at timestamptz not null,

    ends_at timestamptz not null,

    status text not null
        default 'planned',

    origin text not null
        default 'manual',

    notes text,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint study_sessions_plan_owner_fk
        foreign key (
            study_plan_id,
            user_id
        )
        references public.study_plans (
            id,
            user_id
        )
        on delete cascade,

    constraint study_sessions_subject_owner_fk
        foreign key (
            subject_id,
            user_id
        )
        references public.subjects (
            id,
            user_id
        )
        on delete restrict,

    constraint study_sessions_title_length
        check (
            char_length(btrim(title))
                between 1 and 160
        ),

    constraint study_sessions_time_order
        check (
            starts_at < ends_at
        ),

    constraint study_sessions_duration_limit
        check (
            ends_at
                <= starts_at + interval '8 hours'
        ),

    constraint study_sessions_status_allowed
        check (
            status in (
                'planned',
                'completed',
                'skipped'
            )
        ),

    constraint study_sessions_origin_allowed
        check (
            origin in (
                'manual',
                'generated'
            )
        ),

    constraint study_sessions_notes_length
        check (
            notes is null
            or char_length(btrim(notes))
                between 1 and 2000
        )
);

comment on table public.study_sessions is
    'Stores individual scheduled study periods inside a student study plan.';

comment on column public.study_sessions.subject_id is
    'Owned subject that the scheduled study session focuses on.';

comment on column public.study_sessions.starts_at is
    'Absolute start timestamp displayed using the student profile timezone.';

comment on column public.study_sessions.ends_at is
    'Absolute end timestamp displayed using the student profile timezone.';

comment on column public.study_sessions.origin is
    'Identifies whether the session was manually scheduled or generated.';

comment on column public.study_sessions.notes is
    'Optional student-facing notes for the scheduled study session.';


create index study_sessions_user_starts_at_idx
    on public.study_sessions (
        user_id,
        starts_at
    );


create index study_sessions_plan_starts_at_idx
    on public.study_sessions (
        study_plan_id,
        starts_at
    );


create index study_sessions_subject_starts_at_idx
    on public.study_sessions (
        user_id,
        subject_id,
        starts_at
    );


-- ============================================================
-- AUTOMATIC UPDATED_AT
-- ============================================================

create or replace function
    public.set_study_schedule_updated_at()
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


create trigger study_plans_set_updated_at
before update
on public.study_plans
for each row
execute function
    public.set_study_schedule_updated_at();


create trigger study_sessions_set_updated_at
before update
on public.study_sessions
for each row
execute function
    public.set_study_schedule_updated_at();


-- ============================================================
-- TABLE PRIVILEGES
-- ============================================================

revoke all
on table public.study_plans
from anon;


revoke all
on table public.study_sessions
from anon;


revoke all
on table public.study_plans
from authenticated;


revoke all
on table public.study_sessions
from authenticated;


grant select, delete
on table public.study_plans
to authenticated;


grant select, delete
on table public.study_sessions
to authenticated;


grant all
on table public.study_plans
to service_role;


grant all
on table public.study_sessions
to service_role;


-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.study_plans
enable row level security;


alter table public.study_sessions
enable row level security;


create policy study_plans_select_own
on public.study_plans
for select
to authenticated
using (
    user_id = (select auth.uid())
);


create policy study_plans_insert_own
on public.study_plans
for insert
to authenticated
with check (
    user_id = (select auth.uid())
);


create policy study_plans_update_own
on public.study_plans
for update
to authenticated
using (
    user_id = (select auth.uid())
)
with check (
    user_id = (select auth.uid())
);


create policy study_plans_delete_own
on public.study_plans
for delete
to authenticated
using (
    user_id = (select auth.uid())
);


create policy study_sessions_select_own
on public.study_sessions
for select
to authenticated
using (
    user_id = (select auth.uid())
);


create policy study_sessions_insert_own
on public.study_sessions
for insert
to authenticated
with check (
    user_id = (select auth.uid())
);


create policy study_sessions_update_own
on public.study_sessions
for update
to authenticated
using (
    user_id = (select auth.uid())
)
with check (
    user_id = (select auth.uid())
);


create policy study_sessions_delete_own
on public.study_sessions
for delete
to authenticated
using (
    user_id = (select auth.uid())
);


notify pgrst, 'reload schema';

commit;