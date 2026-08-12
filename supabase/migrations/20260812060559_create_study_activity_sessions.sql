-- File: /supabase/migrations/20260812060559_create_study_activity_sessions.sql
-- Purpose: Creates durable authenticated study-activity timer
-- sessions for actual focus, break, pause, and completion tracking.

begin;

-- ============================================================
-- STUDY ACTIVITY SESSIONS
-- ============================================================

create table public.study_activity_sessions (
    id uuid primary key
        default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    subject_id uuid
        references public.subjects(id)
        on delete set null,

    study_plan_id uuid
        references public.study_plans(id)
        on delete set null,

    study_session_id uuid
        references public.study_sessions(id)
        on delete set null,

    title text not null,

    status text not null
        default 'running',

    mode text not null
        default 'focus',

    started_at timestamptz not null
        default now(),

    ended_at timestamptz,

    segment_started_at timestamptz
        default now(),

    focus_seconds integer not null
        default 0,

    break_seconds integer not null
        default 0,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint study_activity_sessions_title_length
        check (
            char_length(btrim(title))
                between 1 and 160
        ),

    constraint study_activity_sessions_status_allowed
        check (
            status in (
                'running',
                'paused',
                'completed'
            )
        ),

    constraint study_activity_sessions_mode_allowed
        check (
            mode in (
                'focus',
                'break'
            )
        ),

    constraint study_activity_sessions_focus_seconds_valid
        check (
            focus_seconds >= 0
        ),

    constraint study_activity_sessions_break_seconds_valid
        check (
            break_seconds >= 0
        ),

    constraint study_activity_sessions_end_order
        check (
            ended_at is null
            or ended_at >= started_at
        ),

    constraint study_activity_sessions_segment_order
        check (
            segment_started_at is null
            or segment_started_at >= started_at
        ),

    constraint study_activity_sessions_state_consistency
        check (
            (
                status = 'running'
                and ended_at is null
                and segment_started_at is not null
            )
            or
            (
                status = 'paused'
                and mode = 'focus'
                and ended_at is null
                and segment_started_at is null
            )
            or
            (
                status = 'completed'
                and mode = 'focus'
                and ended_at is not null
                and segment_started_at is null
            )
        )
);


comment on table public.study_activity_sessions is
    'Stores actual timer-recorded student study activity separately from planned study sessions.';


comment on column public.study_activity_sessions.subject_id is
    'Optional surviving link to the subject studied during this timer session.';


comment on column public.study_activity_sessions.study_plan_id is
    'Optional source study plan associated with the actual timer session.';


comment on column public.study_activity_sessions.study_session_id is
    'Optional scheduled study session that initiated this actual timer session.';


comment on column public.study_activity_sessions.status is
    'Timer lifecycle state: running, paused, or completed.';


comment on column public.study_activity_sessions.mode is
    'Current running segment mode: focus or break.';


comment on column public.study_activity_sessions.segment_started_at is
    'Start timestamp of the currently running focus or break segment. Null while paused or completed.';


comment on column public.study_activity_sessions.focus_seconds is
    'Accumulated completed focus seconds. Only focus time contributes to actual Study Time Analytics.';


comment on column public.study_activity_sessions.break_seconds is
    'Accumulated completed break seconds. Break time does not contribute to actual Study Time Analytics.';


-- ============================================================
-- ONE UNFINISHED TIMER PER STUDENT
-- ============================================================

create unique index
    study_activity_sessions_one_active_per_user_idx
on public.study_activity_sessions (
    user_id
)
where status in (
    'running',
    'paused'
);


create index
    study_activity_sessions_user_started_at_idx
on public.study_activity_sessions (
    user_id,
    started_at desc
);


create index
    study_activity_sessions_user_subject_started_at_idx
on public.study_activity_sessions (
    user_id,
    subject_id,
    started_at desc
);


create index
    study_activity_sessions_plan_idx
on public.study_activity_sessions (
    study_plan_id
)
where study_plan_id is not null;


create index
    study_activity_sessions_study_session_idx
on public.study_activity_sessions (
    study_session_id
)
where study_session_id is not null;


-- ============================================================
-- START-TARGET VALIDATION
-- ============================================================

create or replace function
    public.validate_study_activity_start_target()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
    v_session_user_id uuid;
    v_session_plan_id uuid;
    v_session_subject_id uuid;
begin
    if new.subject_id is null then
        raise exception
            'Study activity requires an owned subject.'
            using errcode = 'P0001';
    end if;

    if not exists (
        select 1
        from public.subjects
        where id = new.subject_id
          and user_id = new.user_id
    ) then
        raise exception
            'Study activity subject is not owned by the student.'
            using errcode = 'P0001';
    end if;

    if new.study_plan_id is not null
       and not exists (
            select 1
            from public.study_plans
            where id = new.study_plan_id
              and user_id = new.user_id
       ) then
        raise exception
            'Study activity plan is not owned by the student.'
            using errcode = 'P0001';
    end if;

    if new.study_session_id is not null then
        select
            user_id,
            study_plan_id,
            subject_id
        into
            v_session_user_id,
            v_session_plan_id,
            v_session_subject_id
        from public.study_sessions
        where id = new.study_session_id;

        if not found
           or v_session_user_id <> new.user_id then
            raise exception
                'Study activity scheduled session is not owned by the student.'
                using errcode = 'P0001';
        end if;

        if new.study_plan_id is null
           or new.study_plan_id <> v_session_plan_id then
            raise exception
                'Study activity plan does not match its scheduled session.'
                using errcode = 'P0001';
        end if;

        if new.subject_id <> v_session_subject_id then
            raise exception
                'Study activity subject does not match its scheduled session.'
                using errcode = 'P0001';
        end if;
    end if;

    return new;
end;
$$;


create trigger
    study_activity_sessions_validate_start_target
before insert
on public.study_activity_sessions
for each row
execute function
    public.validate_study_activity_start_target();


-- ============================================================
-- AUTOMATIC UPDATED_AT
-- ============================================================

create or replace function
    public.set_study_activity_updated_at()
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


create trigger
    study_activity_sessions_set_updated_at
before update
on public.study_activity_sessions
for each row
execute function
    public.set_study_activity_updated_at();


-- ============================================================
-- ATOMIC TIMER TRANSITIONS
-- ============================================================

create or replace function
    public.transition_study_activity_session(
        p_user_id uuid,
        p_activity_id uuid,
        p_action text
    )
returns setof public.study_activity_sessions
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_activity public.study_activity_sessions%rowtype;
    v_now timestamptz := now();
    v_elapsed_seconds integer := 0;
begin
    select *
    into v_activity
    from public.study_activity_sessions
    where id = p_activity_id
      and user_id = p_user_id
    for update;

    if not found then
        raise exception
            'Study activity session was not found.'
            using errcode = 'P0002';
    end if;

    if p_action = 'pause' then
        if v_activity.status <> 'running'
           or v_activity.mode <> 'focus'
           or v_activity.segment_started_at is null then
            raise exception
                'Only a running focus session can be paused.'
                using errcode = 'P0001';
        end if;

        v_elapsed_seconds :=
            greatest(
                0,
                floor(
                    extract(
                        epoch from (
                            v_now
                            - v_activity.segment_started_at
                        )
                    )
                )::integer
            );

        update public.study_activity_sessions
        set
            focus_seconds =
                focus_seconds
                + v_elapsed_seconds,
            status = 'paused',
            mode = 'focus',
            segment_started_at = null
        where id = p_activity_id
          and user_id = p_user_id;

    elsif p_action = 'resume' then
        if v_activity.status <> 'paused'
           or v_activity.segment_started_at is not null then
            raise exception
                'Only a paused study session can be resumed.'
                using errcode = 'P0001';
        end if;

        update public.study_activity_sessions
        set
            status = 'running',
            mode = 'focus',
            segment_started_at = v_now
        where id = p_activity_id
          and user_id = p_user_id;

    elsif p_action = 'start_break' then
        if v_activity.status <> 'running'
           or v_activity.mode <> 'focus'
           or v_activity.segment_started_at is null then
            raise exception
                'A break can start only from a running focus session.'
                using errcode = 'P0001';
        end if;

        v_elapsed_seconds :=
            greatest(
                0,
                floor(
                    extract(
                        epoch from (
                            v_now
                            - v_activity.segment_started_at
                        )
                    )
                )::integer
            );

        update public.study_activity_sessions
        set
            focus_seconds =
                focus_seconds
                + v_elapsed_seconds,
            mode = 'break',
            segment_started_at = v_now
        where id = p_activity_id
          and user_id = p_user_id;

    elsif p_action = 'end_break' then
        if v_activity.status <> 'running'
           or v_activity.mode <> 'break'
           or v_activity.segment_started_at is null then
            raise exception
                'Only a running break can be ended.'
                using errcode = 'P0001';
        end if;

        v_elapsed_seconds :=
            greatest(
                0,
                floor(
                    extract(
                        epoch from (
                            v_now
                            - v_activity.segment_started_at
                        )
                    )
                )::integer
            );

        update public.study_activity_sessions
        set
            break_seconds =
                break_seconds
                + v_elapsed_seconds,
            mode = 'focus',
            segment_started_at = v_now
        where id = p_activity_id
          and user_id = p_user_id;

    elsif p_action = 'complete' then
        if v_activity.status = 'completed' then
            raise exception
                'Completed study activity cannot be completed again.'
                using errcode = 'P0001';
        end if;

        if v_activity.status = 'running'
           and v_activity.segment_started_at is not null then

            v_elapsed_seconds :=
                greatest(
                    0,
                    floor(
                        extract(
                            epoch from (
                                v_now
                                - v_activity.segment_started_at
                            )
                        )
                    )::integer
                );

            if v_activity.mode = 'focus' then
                update public.study_activity_sessions
                set
                    focus_seconds =
                        focus_seconds
                        + v_elapsed_seconds,
                    status = 'completed',
                    mode = 'focus',
                    ended_at = v_now,
                    segment_started_at = null
                where id = p_activity_id
                  and user_id = p_user_id;
            else
                update public.study_activity_sessions
                set
                    break_seconds =
                        break_seconds
                        + v_elapsed_seconds,
                    status = 'completed',
                    mode = 'focus',
                    ended_at = v_now,
                    segment_started_at = null
                where id = p_activity_id
                  and user_id = p_user_id;
            end if;

        elsif v_activity.status = 'paused' then
            update public.study_activity_sessions
            set
                status = 'completed',
                mode = 'focus',
                ended_at = v_now,
                segment_started_at = null
            where id = p_activity_id
              and user_id = p_user_id;

        else
            raise exception
                'Study activity is not in a completable state.'
                using errcode = 'P0001';
        end if;

    else
        raise exception
            'Unsupported study activity transition.'
            using errcode = 'P0001';
    end if;

    return query
    select *
    from public.study_activity_sessions
    where id = p_activity_id
      and user_id = p_user_id;
end;
$$;


comment on function
    public.transition_study_activity_session(
        uuid,
        uuid,
        text
    )
is
    'Atomically accumulates timer duration and changes focus, pause, break, or completed state for one owned study activity session.';


-- ============================================================
-- TABLE PRIVILEGES
-- ============================================================

revoke all
on table public.study_activity_sessions
from anon;


revoke all
on table public.study_activity_sessions
from authenticated;


grant select
on table public.study_activity_sessions
to authenticated;


grant all
on table public.study_activity_sessions
to service_role;


-- ============================================================
-- RPC PRIVILEGES
-- ============================================================

revoke all
on function public.transition_study_activity_session(
    uuid,
    uuid,
    text
)
from public;


revoke all
on function public.transition_study_activity_session(
    uuid,
    uuid,
    text
)
from anon;


revoke all
on function public.transition_study_activity_session(
    uuid,
    uuid,
    text
)
from authenticated;


grant execute
on function public.transition_study_activity_session(
    uuid,
    uuid,
    text
)
to service_role;


-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.study_activity_sessions
enable row level security;


create policy
    study_activity_sessions_select_own
on public.study_activity_sessions
for select
to authenticated
using (
    user_id = (
        select auth.uid()
    )
);


notify pgrst, 'reload schema';

commit;