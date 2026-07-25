-- File: /supabase/migrations/20260725030919_create_profiles_foundation.sql
-- Purpose: Creates the student profile table, security policies,
-- timestamps, and automatic profile creation for new users.

begin;

-- ============================================================
-- Student profiles
-- ============================================================

create table public.profiles (
    id uuid primary key
        references auth.users (id)
        on delete cascade,

    full_name text not null default '',
    avatar_url text,
    onboarding_completed boolean not null default false,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint profiles_full_name_length
        check (char_length(full_name) <= 120),

    constraint profiles_avatar_url_length
        check (
            avatar_url is null
            or char_length(avatar_url) <= 2048
        )
);

comment on table public.profiles is
    'Stores application profile information for authenticated students.';

comment on column public.profiles.id is
    'Matches the student identifier from auth.users.';

comment on column public.profiles.full_name is
    'Student display name used throughout the application.';

comment on column public.profiles.avatar_url is
    'Optional URL for the student profile image.';

comment on column public.profiles.onboarding_completed is
    'Reports whether the student has completed the learning-profile onboarding flow.';

-- Anonymous visitors cannot access profile rows.
revoke all on table public.profiles from anon;

-- Authenticated students may read, create, and update only
-- rows allowed by the Row Level Security policies below.
grant select, insert, update
on table public.profiles
to authenticated;

-- Trusted server-side services may manage profile rows.
grant select, insert, update, delete
on table public.profiles
to service_role;

alter table public.profiles
enable row level security;

-- ============================================================
-- Profile Row Level Security policies
-- ============================================================

create policy "Students can view their own profile"
on public.profiles
for select
to authenticated
using (
    (select auth.uid()) = id
);

create policy "Students can create their own profile"
on public.profiles
for insert
to authenticated
with check (
    (select auth.uid()) = id
);

create policy "Students can update their own profile"
on public.profiles
for update
to authenticated
using (
    (select auth.uid()) = id
)
with check (
    (select auth.uid()) = id
);

-- ============================================================
-- Automatic updated_at timestamp
-- ============================================================

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger profiles_set_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

revoke all
on function public.set_updated_at()
from public;

-- ============================================================
-- Automatic profile creation after registration
-- ============================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (
        id,
        full_name
    )
    values (
        new.id,
        left(
            coalesce(
                new.raw_user_meta_data ->> 'full_name',
                ''
            ),
            120
        )
    )
    on conflict (id) do nothing;

    return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();

revoke all
on function public.handle_new_user()
from public;

commit;