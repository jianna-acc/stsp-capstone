-- File: /supabase/migrations/<timestamp>_create_learning_profile_data_functions.sql
-- Purpose: Adds atomic subject and availability replacement functions
-- and resets onboarding completion when learning-profile data changes.

begin;

-- ============================================================
-- Reset onboarding completion after relevant profile changes
-- ============================================================

create or replace function
    public.reset_profile_onboarding_completion()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    update public.profiles
    set
        onboarding_completed = false,
        onboarding_completed_at = null
    where id = new.id
      and (
          onboarding_completed = true
          or onboarding_completed_at is not null
      );

    return new;
end;
$$;

comment on function
    public.reset_profile_onboarding_completion()
is
    'Resets onboarding completion when required student-profile fields change.';

revoke all
on function
    public.reset_profile_onboarding_completion()
from public;

drop trigger if exists
    profiles_reset_onboarding_completion
on public.profiles;

create trigger
    profiles_reset_onboarding_completion
after update of
    full_name,
    school_name,
    program_name,
    year_level,
    timezone
on public.profiles
for each row
when (
    old.full_name is distinct from new.full_name
    or old.school_name is distinct from new.school_name
    or old.program_name is distinct from new.program_name
    or old.year_level is distinct from new.year_level
    or old.timezone is distinct from new.timezone
)
execute function
    public.reset_profile_onboarding_completion();

-- ============================================================
-- Reset completion after learning-data changes
-- ============================================================

create or replace function
    public.reset_learning_data_onboarding_completion()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    affected_user_id uuid;
begin
    if tg_op = 'DELETE' then
        affected_user_id := old.user_id;
    else
        affected_user_id := new.user_id;
    end if;

    update public.profiles
    set
        onboarding_completed = false,
        onboarding_completed_at = null
    where id = affected_user_id
      and (
          onboarding_completed = true
          or onboarding_completed_at is not null
      );

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

comment on function
    public.reset_learning_data_onboarding_completion()
is
    'Resets onboarding completion when required learning-profile data changes.';

revoke all
on function
    public.reset_learning_data_onboarding_completion()
from public;

drop trigger if exists
    learning_profiles_reset_onboarding_completion
on public.learning_profiles;

create trigger
    learning_profiles_reset_onboarding_completion
after insert or update or delete
on public.learning_profiles
for each row
execute function
    public.reset_learning_data_onboarding_completion();

drop trigger if exists
    learning_profile_subjects_reset_onboarding_completion
on public.learning_profile_subjects;

create trigger
    learning_profile_subjects_reset_onboarding_completion
after insert or update or delete
on public.learning_profile_subjects
for each row
execute function
    public.reset_learning_data_onboarding_completion();

drop trigger if exists
    study_availability_reset_onboarding_completion
on public.study_availability;

create trigger
    study_availability_reset_onboarding_completion
after insert or update or delete
on public.study_availability
for each row
execute function
    public.reset_learning_data_onboarding_completion();

-- ============================================================
-- Atomically replace subject-confidence records
-- ============================================================

create or replace function
    public.replace_learning_profile_subjects(
        p_subjects jsonb
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

    if p_subjects is null then
        raise exception
            'Subject information is required.'
            using errcode = '22023';
    end if;

    if jsonb_typeof(p_subjects) <> 'array' then
        raise exception
            'Subject information must be a JSON array.'
            using errcode = '22023';
    end if;

    if jsonb_array_length(p_subjects) > 30 then
        raise exception
            'A maximum of 30 subjects is allowed.'
            using errcode = '22023';
    end if;

    /*
     * The unique subject index and table constraints validate
     * subject names, strength values, and confidence values.
     *
     * Because this function runs within one database
     * transaction, a failed insert also rolls back the delete.
     */
    delete from public.learning_profile_subjects
    where user_id = current_user_id;

    insert into public.learning_profile_subjects (
        user_id,
        subject_name,
        subject_strength,
        confidence_level
    )
    select
        current_user_id,
        btrim(subject.subject_name),
        lower(btrim(subject.subject_strength)),
        subject.confidence_level
    from jsonb_to_recordset(p_subjects)
        as subject (
            subject_name text,
            subject_strength text,
            confidence_level smallint
        );
end;
$$;

comment on function
    public.replace_learning_profile_subjects(jsonb)
is
    'Atomically replaces the current authenticated student subject-confidence records.';

revoke all
on function
    public.replace_learning_profile_subjects(jsonb)
from public;

grant execute
on function
    public.replace_learning_profile_subjects(jsonb)
to authenticated;

grant execute
on function
    public.replace_learning_profile_subjects(jsonb)
to service_role;

-- ============================================================
-- Atomically replace recurring study availability
-- ============================================================

create or replace function
    public.replace_study_availability(
        p_slots jsonb
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

    if p_slots is null then
        raise exception
            'Study availability is required.'
            using errcode = '22023';
    end if;

    if jsonb_typeof(p_slots) <> 'array' then
        raise exception
            'Study availability must be a JSON array.'
            using errcode = '22023';
    end if;

    if jsonb_array_length(p_slots) > 30 then
        raise exception
            'A maximum of 30 study periods is allowed.'
            using errcode = '22023';
    end if;

    /*
     * Reject overlapping periods for the same weekday.
     */
    if exists (
        with slots as (
            select
                slot.item_number,
                slot.day_of_week,
                slot.start_time,
                slot.end_time
            from jsonb_to_recordset(p_slots)
                with ordinality
                as slot (
                    day_of_week smallint,
                    start_time time,
                    end_time time,
                    item_number bigint
                )
        )
        select 1
        from slots as first_slot
        join slots as second_slot
          on first_slot.item_number
                < second_slot.item_number
         and first_slot.day_of_week
                = second_slot.day_of_week
         and first_slot.start_time
                < second_slot.end_time
         and second_slot.start_time
                < first_slot.end_time
    ) then
        raise exception
            'Study periods cannot overlap.'
            using errcode = '22023';
    end if;

    delete from public.study_availability
    where user_id = current_user_id;

    insert into public.study_availability (
        user_id,
        day_of_week,
        start_time,
        end_time
    )
    select
        current_user_id,
        slot.day_of_week,
        slot.start_time,
        slot.end_time
    from jsonb_to_recordset(p_slots)
        as slot (
            day_of_week smallint,
            start_time time,
            end_time time
        );
end;
$$;

comment on function
    public.replace_study_availability(jsonb)
is
    'Atomically replaces the current authenticated student recurring study availability.';

revoke all
on function
    public.replace_study_availability(jsonb)
from public;

grant execute
on function
    public.replace_study_availability(jsonb)
to authenticated;

grant execute
on function
    public.replace_study_availability(jsonb)
to service_role;

commit;