-- File: /supabase/migrations/<timestamp>_create_learning_profile_foundation.sql
-- Purpose: Creates the student learning-profile, subject-confidence,
-- study-availability, onboarding-progress, and completion foundations.

begin;

-- ============================================================
-- Extend the existing student profile
-- ============================================================

alter table public.profiles
    add column school_name text,
    add column program_name text,
    add column year_level text,
    add column timezone text
        not null
        default 'Asia/Manila',
    add column onboarding_current_step smallint
        not null
        default 1,
    add column onboarding_completed_at timestamptz;

-- Normalize any development records that were already marked
-- complete before the completion timestamp existed.
update public.profiles
set
    onboarding_current_step = 6,
    onboarding_completed_at = coalesce(
        onboarding_completed_at,
        now()
    )
where onboarding_completed = true;

alter table public.profiles
    add constraint profiles_school_name_length
        check (
            school_name is null
            or char_length(btrim(school_name))
                between 1 and 160
        ),

    add constraint profiles_program_name_length
        check (
            program_name is null
            or char_length(btrim(program_name))
                between 1 and 160
        ),

    add constraint profiles_year_level_length
        check (
            year_level is null
            or char_length(btrim(year_level))
                between 1 and 50
        ),

    add constraint profiles_timezone_length
        check (
            char_length(btrim(timezone))
                between 1 and 100
        ),

    add constraint profiles_onboarding_current_step_range
        check (
            onboarding_current_step
                between 1 and 6
        ),

    add constraint profiles_onboarding_completion_consistency
        check (
            (
                onboarding_completed = false
                and onboarding_completed_at is null
            )
            or
            (
                onboarding_completed = true
                and onboarding_completed_at is not null
            )
        );

comment on column public.profiles.school_name is
    'Optional school or educational institution entered during onboarding.';

comment on column public.profiles.program_name is
    'Optional degree program, strand, course, or academic track.';

comment on column public.profiles.year_level is
    'Optional academic year level entered by the student.';

comment on column public.profiles.timezone is
    'IANA timezone used when displaying study schedules and reminders.';

comment on column public.profiles.onboarding_current_step is
    'Last onboarding step saved by the student, from step 1 through step 6.';

comment on column public.profiles.onboarding_completed_at is
    'Timestamp recorded after all required learning-profile sections pass validation.';

-- The registration trigger already creates profile rows.
-- Students do not need permission to create another profile row.
revoke insert, update
on table public.profiles
from authenticated;

drop policy if exists
    "Students can create their own profile"
on public.profiles;

-- Students can update editable profile and progress fields.
-- They cannot directly update onboarding_completed or
-- onboarding_completed_at.
grant update (
    full_name,
    avatar_url,
    school_name,
    program_name,
    year_level,
    timezone,
    onboarding_current_step
)
on table public.profiles
to authenticated;

-- ============================================================
-- General learning preferences
-- ============================================================

create table public.learning_profiles (
    user_id uuid primary key
        references public.profiles (id)
        on delete cascade,

    preferred_study_duration_minutes smallint,

    preferred_study_times text[]
        not null
        default '{}'::text[],

    common_study_challenges text[]
        not null
        default '{}'::text[],

    estimated_task_completion_minutes smallint,

    preferred_learning_methods text[]
        not null
        default '{}'::text[],

    created_at timestamptz
        not null
        default now(),

    updated_at timestamptz
        not null
        default now(),

    constraint learning_profiles_study_duration_range
        check (
            preferred_study_duration_minutes is null
            or preferred_study_duration_minutes
                between 10 and 240
        ),

    constraint learning_profiles_task_completion_range
        check (
            estimated_task_completion_minutes is null
            or estimated_task_completion_minutes
                between 5 and 480
        ),

    constraint learning_profiles_study_times_allowed
        check (
            preferred_study_times
            <@ array[
                'early_morning',
                'morning',
                'afternoon',
                'evening',
                'late_night'
            ]::text[]
        ),

    constraint learning_profiles_study_times_count
        check (
            cardinality(preferred_study_times)
                <= 5
        ),

    constraint learning_profiles_challenges_allowed
        check (
            common_study_challenges
            <@ array[
                'procrastination',
                'distractions',
                'time_management',
                'motivation',
                'difficult_content',
                'heavy_workload',
                'forgetfulness',
                'test_anxiety',
                'other'
            ]::text[]
        ),

    constraint learning_profiles_challenges_count
        check (
            cardinality(common_study_challenges)
                <= 9
        ),

    constraint learning_profiles_methods_allowed
        check (
            preferred_learning_methods
            <@ array[
                'visual',
                'auditory',
                'reading_writing',
                'kinesthetic',
                'collaborative',
                'mixed'
            ]::text[]
        ),

    constraint learning_profiles_methods_count
        check (
            cardinality(preferred_learning_methods)
                <= 6
        )
);

comment on table public.learning_profiles is
    'Stores one set of general study preferences for each authenticated student.';

comment on column
    public.learning_profiles.preferred_study_duration_minutes
is
    'Preferred length of one focused study session in minutes.';

comment on column
    public.learning_profiles.preferred_study_times
is
    'Selected times of day when the student prefers to study.';

comment on column
    public.learning_profiles.common_study_challenges
is
    'Challenges commonly experienced by the student while studying.';

comment on column
    public.learning_profiles.estimated_task_completion_minutes
is
    'Student estimate for the duration of a typical academic task.';

comment on column
    public.learning_profiles.preferred_learning_methods
is
    'Learning approaches selected by the student.';

-- ============================================================
-- Strong subjects, weak subjects, and confidence
-- ============================================================

create table public.learning_profile_subjects (
    id uuid primary key
        default gen_random_uuid(),

    user_id uuid
        not null
        references public.profiles (id)
        on delete cascade,

    subject_name text
        not null,

    subject_strength text
        not null,

    confidence_level smallint
        not null,

    created_at timestamptz
        not null
        default now(),

    updated_at timestamptz
        not null
        default now(),

    constraint learning_profile_subjects_name_length
        check (
            char_length(btrim(subject_name))
                between 1 and 100
        ),

    constraint learning_profile_subjects_strength_allowed
        check (
            subject_strength in (
                'strong',
                'weak'
            )
        ),

    constraint learning_profile_subjects_confidence_range
        check (
            confidence_level
                between 1 and 5
        )
);

create unique index
    learning_profile_subjects_user_name_unique
on public.learning_profile_subjects (
    user_id,
    lower(btrim(subject_name))
);

comment on table public.learning_profile_subjects is
    'Stores strong or weak subjects and confidence ratings for each student.';

comment on column
    public.learning_profile_subjects.subject_strength
is
    'Classifies the subject as strong or weak for the student.';

comment on column
    public.learning_profile_subjects.confidence_level
is
    'Student confidence from 1, very low, through 5, very high.';

-- ============================================================
-- Available recurring study schedule
-- ============================================================

create table public.study_availability (
    id uuid primary key
        default gen_random_uuid(),

    user_id uuid
        not null
        references public.profiles (id)
        on delete cascade,

    day_of_week smallint
        not null,

    start_time time
        not null,

    end_time time
        not null,

    created_at timestamptz
        not null
        default now(),

    updated_at timestamptz
        not null
        default now(),

    constraint study_availability_day_range
        check (
            day_of_week between 1 and 7
        ),

    constraint study_availability_time_order
        check (
            start_time < end_time
        ),

    constraint study_availability_unique_period
        unique (
            user_id,
            day_of_week,
            start_time,
            end_time
        )
);

comment on table public.study_availability is
    'Stores recurring weekly periods when a student is available to study.';

comment on column public.study_availability.day_of_week is
    'ISO weekday number where 1 is Monday and 7 is Sunday.';

-- ============================================================
-- Row Level Security and database privileges
-- ============================================================

revoke all
on table public.learning_profiles
from anon;

revoke all
on table public.learning_profile_subjects
from anon;

revoke all
on table public.study_availability
from anon;

grant select, insert, update, delete
on table public.learning_profiles
to authenticated;

grant select, insert, update, delete
on table public.learning_profile_subjects
to authenticated;

grant select, insert, update, delete
on table public.study_availability
to authenticated;

grant select, insert, update, delete
on table public.learning_profiles
to service_role;

grant select, insert, update, delete
on table public.learning_profile_subjects
to service_role;

grant select, insert, update, delete
on table public.study_availability
to service_role;

alter table public.learning_profiles
enable row level security;

alter table public.learning_profile_subjects
enable row level security;

alter table public.study_availability
enable row level security;

-- Learning-profile policies

create policy
    "Students can view their own learning profile"
on public.learning_profiles
for select
to authenticated
using (
    (select auth.uid()) = user_id
);

create policy
    "Students can create their own learning profile"
on public.learning_profiles
for insert
to authenticated
with check (
    (select auth.uid()) = user_id
);

create policy
    "Students can update their own learning profile"
on public.learning_profiles
for update
to authenticated
using (
    (select auth.uid()) = user_id
)
with check (
    (select auth.uid()) = user_id
);

create policy
    "Students can delete their own learning profile"
on public.learning_profiles
for delete
to authenticated
using (
    (select auth.uid()) = user_id
);

-- Subject-confidence policies

create policy
    "Students can view their own subject profiles"
on public.learning_profile_subjects
for select
to authenticated
using (
    (select auth.uid()) = user_id
);

create policy
    "Students can create their own subject profiles"
on public.learning_profile_subjects
for insert
to authenticated
with check (
    (select auth.uid()) = user_id
);

create policy
    "Students can update their own subject profiles"
on public.learning_profile_subjects
for update
to authenticated
using (
    (select auth.uid()) = user_id
)
with check (
    (select auth.uid()) = user_id
);

create policy
    "Students can delete their own subject profiles"
on public.learning_profile_subjects
for delete
to authenticated
using (
    (select auth.uid()) = user_id
);

-- Study-availability policies

create policy
    "Students can view their own study availability"
on public.study_availability
for select
to authenticated
using (
    (select auth.uid()) = user_id
);

create policy
    "Students can create their own study availability"
on public.study_availability
for insert
to authenticated
with check (
    (select auth.uid()) = user_id
);

create policy
    "Students can update their own study availability"
on public.study_availability
for update
to authenticated
using (
    (select auth.uid()) = user_id
)
with check (
    (select auth.uid()) = user_id
);

create policy
    "Students can delete their own study availability"
on public.study_availability
for delete
to authenticated
using (
    (select auth.uid()) = user_id
);

-- ============================================================
-- Automatic updated_at timestamps
-- ============================================================

create trigger learning_profiles_set_updated_at
before update on public.learning_profiles
for each row
execute function public.set_updated_at();

create trigger learning_profile_subjects_set_updated_at
before update on public.learning_profile_subjects
for each row
execute function public.set_updated_at();

create trigger study_availability_set_updated_at
before update on public.study_availability
for each row
execute function public.set_updated_at();

-- ============================================================
-- Controlled onboarding-completion check
-- ============================================================

create or replace function
    public.complete_learning_profile_onboarding()
returns boolean
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

    -- Student-profile information must be complete.
    if not exists (
        select 1
        from public.profiles as profile
        where profile.id = current_user_id
          and nullif(
                btrim(profile.full_name),
                ''
              ) is not null
          and nullif(
                btrim(profile.school_name),
                ''
              ) is not null
          and nullif(
                btrim(profile.program_name),
                ''
              ) is not null
          and nullif(
                btrim(profile.year_level),
                ''
              ) is not null
          and nullif(
                btrim(profile.timezone),
                ''
              ) is not null
    ) then
        return false;
    end if;

    -- General learning preferences must be complete.
    if not exists (
        select 1
        from public.learning_profiles
            as learning_profile
        where learning_profile.user_id =
                current_user_id
          and learning_profile
                .preferred_study_duration_minutes
                is not null
          and cardinality(
                learning_profile
                    .preferred_study_times
              ) > 0
          and cardinality(
                learning_profile
                    .common_study_challenges
              ) > 0
          and learning_profile
                .estimated_task_completion_minutes
                is not null
          and cardinality(
                learning_profile
                    .preferred_learning_methods
              ) > 0
    ) then
        return false;
    end if;

    -- At least one strong subject is required.
    if not exists (
        select 1
        from public.learning_profile_subjects
        where user_id = current_user_id
          and subject_strength = 'strong'
    ) then
        return false;
    end if;

    -- At least one weak subject is required.
    if not exists (
        select 1
        from public.learning_profile_subjects
        where user_id = current_user_id
          and subject_strength = 'weak'
    ) then
        return false;
    end if;

    -- At least one available study period is required.
    if not exists (
        select 1
        from public.study_availability
        where user_id = current_user_id
    ) then
        return false;
    end if;

    update public.profiles
    set
        onboarding_current_step = 6,
        onboarding_completed = true,
        onboarding_completed_at = coalesce(
            onboarding_completed_at,
            now()
        )
    where id = current_user_id;

    return found;
end;
$$;

comment on function
    public.complete_learning_profile_onboarding()
is
    'Marks the current student onboarding complete only after all required learning-profile sections exist.';

revoke all
on function
    public.complete_learning_profile_onboarding()
from public;

grant execute
on function
    public.complete_learning_profile_onboarding()
to authenticated;

grant execute
on function
    public.complete_learning_profile_onboarding()
to service_role;

commit;