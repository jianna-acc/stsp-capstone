-- File: /supabase/migrations/<timestamp>_fix_replace_study_availability.sql
-- Purpose: Corrects JSON parsing and overlap validation in the
-- recurring study-availability replacement function.

begin;

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

    if jsonb_array_length(p_slots) = 0 then
        raise exception
            'At least one study period is required.'
            using errcode = '22023';
    end if;

    if jsonb_array_length(p_slots) > 30 then
        raise exception
            'A maximum of 30 study periods is allowed.'
            using errcode = '22023';
    end if;

    /*
     * Validate that every submitted object contains the required
     * day and time values before replacing existing records.
     */
    if exists (
        select 1
        from jsonb_array_elements(p_slots)
            as item(slot_value)
        where
            item.slot_value ->> 'day_of_week'
                is null
            or item.slot_value ->> 'start_time'
                is null
            or item.slot_value ->> 'end_time'
                is null
    ) then
        raise exception
            'Every study period requires a day, start time, and end time.'
            using errcode = '22023';
    end if;

    /*
     * Parse the JSON array with ordinality. Each object receives
     * an item number so different submitted periods can be
     * compared safely.
     */
    if exists (
        with parsed_slots as (
            select
                item.item_number,
                (
                    item.slot_value
                    ->> 'day_of_week'
                )::smallint as day_of_week,
                (
                    item.slot_value
                    ->> 'start_time'
                )::time as start_time,
                (
                    item.slot_value
                    ->> 'end_time'
                )::time as end_time
            from jsonb_array_elements(p_slots)
                with ordinality
                as item(
                    slot_value,
                    item_number
                )
        )
        select 1
        from parsed_slots as first_slot
        join parsed_slots as second_slot
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

    /*
     * This function executes as one database transaction. If the
     * insertion fails, the deletion is rolled back automatically.
     */
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
        (
            item.slot_value
            ->> 'day_of_week'
        )::smallint,
        (
            item.slot_value
            ->> 'start_time'
        )::time,
        (
            item.slot_value
            ->> 'end_time'
        )::time
    from jsonb_array_elements(p_slots)
        as item(slot_value);
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

notify pgrst, 'reload schema';

commit;