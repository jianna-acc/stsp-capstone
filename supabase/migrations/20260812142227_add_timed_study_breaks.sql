alter table public.study_activity_sessions
add column if not exists break_ends_at timestamptz;

update public.study_activity_sessions
set break_ends_at = now()
where status = 'running'
  and mode = 'break'
  and break_ends_at is null;

create or replace function public.start_timed_study_activity_break(
    p_user_id uuid,
    p_activity_id uuid,
    p_break_minutes integer
)
returns setof public.study_activity_sessions
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_activity public.study_activity_sessions%rowtype;
    v_now timestamptz := clock_timestamp();
    v_elapsed_seconds integer;
begin
    if p_break_minutes < 1 or p_break_minutes > 180 then
        raise exception using
            errcode = 'P0001',
            message = 'Study break duration must be between 1 and 180 minutes.';
    end if;

    select *
    into v_activity
    from public.study_activity_sessions
    where id = p_activity_id
      and user_id = p_user_id
    for update;

    if not found then
        raise exception using
            errcode = 'P0002',
            message = 'Study activity was not found.';
    end if;

    if v_activity.status <> 'running'
       or v_activity.mode <> 'focus'
       or v_activity.ended_at is not null
       or v_activity.segment_started_at is null then
        raise exception using
            errcode = 'P0001',
            message = 'Study activity cannot start a break from its current state.';
    end if;

    v_elapsed_seconds := greatest(
        0,
        floor(
            extract(
                epoch from (
                    v_now - v_activity.segment_started_at
                )
            )
        )::integer
    );

    update public.study_activity_sessions
    set focus_seconds = focus_seconds + v_elapsed_seconds,
        mode = 'break',
        segment_started_at = v_now,
        break_ends_at = v_now + make_interval(mins => p_break_minutes),
        updated_at = v_now
    where id = p_activity_id
      and user_id = p_user_id
    returning * into v_activity;

    return next v_activity;
    return;
end;
$$;

create or replace function public.transition_study_activity_session(
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
    v_now timestamptz := clock_timestamp();
    v_elapsed_seconds integer;
    v_focus_seconds integer;
    v_break_seconds integer;
begin
    select *
    into v_activity
    from public.study_activity_sessions
    where id = p_activity_id
      and user_id = p_user_id
    for update;

    if not found then
        raise exception using
            errcode = 'P0002',
            message = 'Study activity was not found.';
    end if;

    if p_action = 'pause' then
        if v_activity.status <> 'running'
           or v_activity.mode <> 'focus'
           or v_activity.ended_at is not null
           or v_activity.segment_started_at is null then
            raise exception using
                errcode = 'P0001',
                message = 'Study activity cannot be paused from its current state.';
        end if;

        v_elapsed_seconds := greatest(
            0,
            floor(
                extract(
                    epoch from (
                        v_now - v_activity.segment_started_at
                    )
                )
            )::integer
        );

        update public.study_activity_sessions
        set focus_seconds = focus_seconds + v_elapsed_seconds,
            status = 'paused',
            mode = 'focus',
            segment_started_at = null,
            break_ends_at = null,
            updated_at = v_now
        where id = p_activity_id
          and user_id = p_user_id
        returning * into v_activity;

    elsif p_action = 'resume' then
        if v_activity.status <> 'paused'
           or v_activity.mode <> 'focus'
           or v_activity.ended_at is not null
           or v_activity.segment_started_at is not null then
            raise exception using
                errcode = 'P0001',
                message = 'Study activity cannot be resumed from its current state.';
        end if;

        update public.study_activity_sessions
        set status = 'running',
            mode = 'focus',
            segment_started_at = v_now,
            break_ends_at = null,
            updated_at = v_now
        where id = p_activity_id
          and user_id = p_user_id
        returning * into v_activity;

    elsif p_action = 'start_break' then
        if v_activity.status <> 'running'
           or v_activity.mode <> 'focus'
           or v_activity.ended_at is not null
           or v_activity.segment_started_at is null then
            raise exception using
                errcode = 'P0001',
                message = 'Study activity cannot start a break from its current state.';
        end if;

        v_elapsed_seconds := greatest(
            0,
            floor(
                extract(
                    epoch from (
                        v_now - v_activity.segment_started_at
                    )
                )
            )::integer
        );

        update public.study_activity_sessions
        set focus_seconds = focus_seconds + v_elapsed_seconds,
            mode = 'break',
            segment_started_at = v_now,
            break_ends_at = v_now + interval '5 minutes',
            updated_at = v_now
        where id = p_activity_id
          and user_id = p_user_id
        returning * into v_activity;

    elsif p_action = 'end_break' then
        if v_activity.status <> 'running'
           or v_activity.mode <> 'break'
           or v_activity.ended_at is not null
           or v_activity.segment_started_at is null then
            raise exception using
                errcode = 'P0001',
                message = 'Study activity cannot end a break from its current state.';
        end if;

        v_elapsed_seconds := greatest(
            0,
            floor(
                extract(
                    epoch from (
                        v_now - v_activity.segment_started_at
                    )
                )
            )::integer
        );

        update public.study_activity_sessions
        set break_seconds = break_seconds + v_elapsed_seconds,
            mode = 'focus',
            segment_started_at = v_now,
            break_ends_at = null,
            updated_at = v_now
        where id = p_activity_id
          and user_id = p_user_id
        returning * into v_activity;

    elsif p_action = 'complete' then
        if v_activity.status = 'completed'
           or v_activity.ended_at is not null then
            raise exception using
                errcode = 'P0001',
                message = 'Study activity is already completed.';
        end if;

        v_focus_seconds := v_activity.focus_seconds;
        v_break_seconds := v_activity.break_seconds;

        if v_activity.status = 'running' then
            if v_activity.segment_started_at is null then
                raise exception using
                    errcode = 'P0001',
                    message = 'Running study activity is missing its segment timestamp.';
            end if;

            v_elapsed_seconds := greatest(
                0,
                floor(
                    extract(
                        epoch from (
                            v_now - v_activity.segment_started_at
                        )
                    )
                )::integer
            );

            if v_activity.mode = 'focus' then
                v_focus_seconds := v_focus_seconds + v_elapsed_seconds;
            elsif v_activity.mode = 'break' then
                v_break_seconds := v_break_seconds + v_elapsed_seconds;
            else
                raise exception using
                    errcode = 'P0001',
                    message = 'Study activity mode is invalid.';
            end if;

        elsif v_activity.status = 'paused' then
            if v_activity.mode <> 'focus'
               or v_activity.segment_started_at is not null then
                raise exception using
                    errcode = 'P0001',
                    message = 'Paused study activity state is invalid.';
            end if;

        else
            raise exception using
                errcode = 'P0001',
                message = 'Study activity cannot be completed from its current state.';
        end if;

        update public.study_activity_sessions
        set focus_seconds = v_focus_seconds,
            break_seconds = v_break_seconds,
            status = 'completed',
            mode = 'focus',
            ended_at = v_now,
            segment_started_at = null,
            break_ends_at = null,
            updated_at = v_now
        where id = p_activity_id
          and user_id = p_user_id
        returning * into v_activity;

    else
        raise exception using
            errcode = 'P0001',
            message = 'Study activity transition action is invalid.';
    end if;

    return next v_activity;
    return;
end;
$$;

alter table public.study_activity_sessions
add constraint study_activity_sessions_break_deadline_state_check
check (
    (
        status = 'running'
        and mode = 'break'
        and break_ends_at is not null
    )
    or
    (
        not (
            status = 'running'
            and mode = 'break'
        )
        and break_ends_at is null
    )
);

revoke all
on function public.start_timed_study_activity_break(uuid, uuid, integer)
from public;

revoke all
on function public.start_timed_study_activity_break(uuid, uuid, integer)
from anon;

revoke all
on function public.start_timed_study_activity_break(uuid, uuid, integer)
from authenticated;

grant execute
on function public.start_timed_study_activity_break(uuid, uuid, integer)
to service_role;

revoke all
on function public.transition_study_activity_session(uuid, uuid, text)
from public;

revoke all
on function public.transition_study_activity_session(uuid, uuid, text)
from anon;

revoke all
on function public.transition_study_activity_session(uuid, uuid, text)
from authenticated;

grant execute
on function public.transition_study_activity_session(uuid, uuid, text)
to service_role;

notify pgrst, 'reload schema';
