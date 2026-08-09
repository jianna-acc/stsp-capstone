-- File: /supabase/migrations/20260809153000_add_output_confidence_and_task_output_type.sql
-- Purpose: Adds reusable learning-output confidence ratings and
-- classifies academic tasks by the type of output they require.

-- ============================================================
-- Learning output confidence
-- ============================================================

create table public.learning_output_confidences (
    id uuid primary key
        default gen_random_uuid(),

    user_id uuid
        not null
        references public.profiles(id)
        on delete cascade,

    output_type text
        not null,

    confidence_level smallint
        not null,

    created_at timestamptz
        not null
        default now(),

    updated_at timestamptz
        not null
        default now(),

    constraint learning_output_confidences_output_type_allowed
        check (
            output_type in (
                'writing',
                'computation',
                'research',
                'presentation',
                'creative',
                'reading_analysis',
                'memorization'
            )
        ),

    constraint learning_output_confidences_confidence_range
        check (
            confidence_level between 1 and 5
        ),

    constraint learning_output_confidences_user_output_unique
        unique (
            user_id,
            output_type
        )
);


comment on table
    public.learning_output_confidences
is
    'Stores each student''s confidence in common academic output types.';


comment on column
    public.learning_output_confidences.output_type
is
    'Academic output skill such as writing, computation, research, presentation, creative work, reading analysis, or memorization.';


comment on column
    public.learning_output_confidences.confidence_level
is
    'Student confidence from 1, very low, through 5, very high.';


-- ============================================================
-- updated_at trigger
-- ============================================================

create or replace function
    public.set_learning_output_confidence_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


create trigger
    learning_output_confidences_set_updated_at
before update
on public.learning_output_confidences
for each row
execute function
    public.set_learning_output_confidence_updated_at();


-- ============================================================
-- Reset completed onboarding after confidence changes
-- ============================================================

create trigger
    learning_output_confidences_reset_onboarding_completion
after insert or update or delete
on public.learning_output_confidences
for each row
execute function
    public.reset_learning_data_onboarding_completion();


-- ============================================================
-- Row Level Security
-- ============================================================

alter table
    public.learning_output_confidences
enable row level security;


create policy
    "Students can view their own output confidence"
on public.learning_output_confidences
for select
to authenticated
using (
    user_id = auth.uid()
);


create policy
    "Students can create their own output confidence"
on public.learning_output_confidences
for insert
to authenticated
with check (
    user_id = auth.uid()
);


create policy
    "Students can update their own output confidence"
on public.learning_output_confidences
for update
to authenticated
using (
    user_id = auth.uid()
)
with check (
    user_id = auth.uid()
);


create policy
    "Students can delete their own output confidence"
on public.learning_output_confidences
for delete
to authenticated
using (
    user_id = auth.uid()
);


grant select, insert, update, delete
on public.learning_output_confidences
to authenticated;


-- ============================================================
-- Atomically replace output-confidence ratings
-- ============================================================

create or replace function
    public.replace_learning_output_confidences(
        p_confidences jsonb
    )
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid := auth.uid();
begin
    if current_user_id is null then
        raise exception
            'Authentication is required.'
            using errcode = '42501';
    end if;

    if p_confidences is null then
        raise exception
            'Output confidence information is required.'
            using errcode = '22023';
    end if;

    if jsonb_typeof(p_confidences) <> 'array' then
        raise exception
            'Output confidence information must be a JSON array.'
            using errcode = '22023';
    end if;

    if jsonb_array_length(p_confidences) <> 7 then
        raise exception
            'Confidence ratings are required for all seven output types.'
            using errcode = '22023';
    end if;

    delete from
        public.learning_output_confidences
    where
        user_id = current_user_id;

    insert into public.learning_output_confidences (
        user_id,
        output_type,
        confidence_level
    )
    select
        current_user_id,
        lower(
            btrim(
                confidence.output_type
            )
        ),
        confidence.confidence_level
    from jsonb_to_recordset(
        p_confidences
    ) as confidence (
        output_type text,
        confidence_level smallint
    );

    /*
     * Seven rows are required above. Because the table only
     * permits seven unique output types, a successful insert
     * guarantees that every supported output type appears once.
     */
end;
$$;


comment on function
    public.replace_learning_output_confidences(jsonb)
is
    'Atomically replaces all seven academic-output confidence ratings for the authenticated student.';


revoke all
on function
    public.replace_learning_output_confidences(jsonb)
from public;


grant execute
on function
    public.replace_learning_output_confidences(jsonb)
to authenticated;


grant execute
on function
    public.replace_learning_output_confidences(jsonb)
to service_role;


-- ============================================================
-- Academic task output type
-- ============================================================

alter table public.academic_tasks
add column output_type text
    not null
    default 'other';


alter table public.academic_tasks
add constraint academic_tasks_output_type_valid
check (
    output_type in (
        'writing',
        'computation',
        'research',
        'presentation',
        'creative',
        'reading_analysis',
        'memorization',
        'mixed',
        'other'
    )
);


comment on column
    public.academic_tasks.output_type
is
    'Primary kind of academic output required by the task and used to match the student''s output-confidence profile.';


create index academic_tasks_user_output_type_idx
on public.academic_tasks (
    user_id,
    output_type
);