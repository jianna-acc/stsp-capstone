-- File: /supabase/migrations/20260811002500_add_study_plan_regeneration_rpc.sql
-- Purpose: Adds transactional generated-session replacement for
-- Track D study-plan regeneration while preserving manual sessions.

-- ============================================================
-- Align generated session titles with Academic Tasks
-- ============================================================

alter table public.study_sessions
drop constraint study_sessions_title_length;

alter table public.study_sessions
add constraint study_sessions_title_length
check (
    char_length(btrim(title))
        between 1 and 200
);


-- ============================================================
-- Transactional generated-session replacement
-- ============================================================

create or replace function
public.replace_generated_study_plan_sessions(
    p_user_id uuid,
    p_study_plan_id uuid,
    p_generated_at timestamptz,
    p_sessions jsonb
)
returns table (
    plan jsonb,
    sessions jsonb
)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_plan public.study_plans%rowtype;
begin
    -- Lock and validate the owned plan.
    select *
    into v_plan
    from public.study_plans
    where id = p_study_plan_id
      and user_id = p_user_id
    for update;

    if not found then
        raise exception
            'Study plan not found.'
            using errcode = 'P0002';
    end if;

    if v_plan.generation_mode <> 'generated' then
        raise exception
            'Only generated study plans can be regenerated.'
            using errcode = '22023';
    end if;

    if p_generated_at is null then
        raise exception
            'generated_at is required.'
            using errcode = '22023';
    end if;

    if (
        p_sessions is null
        or jsonb_typeof(p_sessions) <> 'array'
        or jsonb_array_length(p_sessions) = 0
        or jsonb_array_length(p_sessions) > 500
    ) then
        raise exception
            'Replacement sessions must contain between 1 and 500 items.'
            using errcode = '22023';
    end if;


    -- Reject replacement sessions outside the existing plan range.
    if exists (
        select 1
        from jsonb_to_recordset(
            p_sessions
        ) as replacement (
            subject_id uuid,
            title text,
            starts_at timestamptz,
            ends_at timestamptz
        )
        where replacement.starts_at::date
                < v_plan.starts_on
           or replacement.ends_at::date
                > v_plan.ends_on
    ) then
        raise exception
            'Replacement sessions must stay inside the study-plan range.'
            using errcode = '22023';
    end if;


    -- Defensive validation: generated sessions may not overlap
    -- manually created sessions already attached to the plan.
    if exists (
        select 1
        from jsonb_to_recordset(
            p_sessions
        ) as replacement (
            subject_id uuid,
            title text,
            starts_at timestamptz,
            ends_at timestamptz
        )
        join public.study_sessions existing
          on existing.study_plan_id = p_study_plan_id
         and existing.user_id = p_user_id
         and existing.origin = 'manual'
         and tstzrange(
                replacement.starts_at,
                replacement.ends_at,
                '[)'
             )
             &&
             tstzrange(
                existing.starts_at,
                existing.ends_at,
                '[)'
             )
    ) then
        raise exception
            'Generated sessions cannot overlap manual study sessions.'
            using errcode = '22023';
    end if;


    -- Remove only the previous generated sessions.
    delete from public.study_sessions
    where study_plan_id = p_study_plan_id
      and user_id = p_user_id
      and origin = 'generated';


    -- Persist the replacement generated sessions.
    insert into public.study_sessions (
        study_plan_id,
        user_id,
        subject_id,
        title,
        starts_at,
        ends_at,
        status,
        origin,
        notes
    )
    select
        p_study_plan_id,
        p_user_id,
        replacement.subject_id,
        replacement.title,
        replacement.starts_at,
        replacement.ends_at,
        'planned',
        'generated',
        null
    from jsonb_to_recordset(
        p_sessions
    ) as replacement (
        subject_id uuid,
        title text,
        starts_at timestamptz,
        ends_at timestamptz
    );


    -- Mark when this generated plan was most recently rebuilt.
    update public.study_plans
    set generated_at = p_generated_at
    where id = p_study_plan_id
      and user_id = p_user_id;


    -- Return the refreshed plan and ALL sessions.
    -- Manual sessions are intentionally included.
    return query
    select
        jsonb_build_object(
            'id',
            refreshed_plan.id,
            'title',
            refreshed_plan.title,
            'starts_on',
            refreshed_plan.starts_on,
            'ends_on',
            refreshed_plan.ends_on,
            'status',
            refreshed_plan.status,
            'generation_mode',
            refreshed_plan.generation_mode,
            'generated_at',
            refreshed_plan.generated_at,
            'created_at',
            refreshed_plan.created_at,
            'updated_at',
            refreshed_plan.updated_at
        ),
        coalesce(
            (
                select jsonb_agg(
                    jsonb_build_object(
                        'id',
                        session.id,
                        'study_plan_id',
                        session.study_plan_id,
                        'subject_id',
                        session.subject_id,
                        'title',
                        session.title,
                        'starts_at',
                        session.starts_at,
                        'ends_at',
                        session.ends_at,
                        'status',
                        session.status,
                        'origin',
                        session.origin,
                        'notes',
                        session.notes,
                        'created_at',
                        session.created_at,
                        'updated_at',
                        session.updated_at
                    )
                    order by
                        session.starts_at,
                        session.id
                )
                from public.study_sessions session
                where session.study_plan_id
                        = p_study_plan_id
                  and session.user_id
                        = p_user_id
            ),
            '[]'::jsonb
        )
    from public.study_plans refreshed_plan
    where refreshed_plan.id
            = p_study_plan_id
      and refreshed_plan.user_id
            = p_user_id;
end;
$$;


-- This function uses SECURITY DEFINER and therefore must only
-- be callable by the trusted backend service-role client.

revoke all
on function public.replace_generated_study_plan_sessions(
    uuid,
    uuid,
    timestamptz,
    jsonb
)
from public;

revoke all
on function public.replace_generated_study_plan_sessions(
    uuid,
    uuid,
    timestamptz,
    jsonb
)
from anon;

revoke all
on function public.replace_generated_study_plan_sessions(
    uuid,
    uuid,
    timestamptz,
    jsonb
)
from authenticated;

grant execute
on function public.replace_generated_study_plan_sessions(
    uuid,
    uuid,
    timestamptz,
    jsonb
)
to service_role;