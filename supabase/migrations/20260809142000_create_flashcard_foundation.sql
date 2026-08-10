-- File: /supabase/migrations/20260809142000_create_flashcard_foundation.sql
-- Purpose: Creates persistent flashcard decks and cards with ownership
-- validation, constraints, indexes, privileges, and Row Level Security.

create table public.flashcard_decks (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    subject_id uuid not null
        references public.subjects(id)
        on delete cascade,

    study_file_id uuid
        references public.study_files(id)
        on delete cascade,

    scope_type text not null,

    title text not null,

    requested_card_count integer not null,

    sources jsonb not null
        default '[]'::jsonb,

    generation_model text not null,

    generation_count integer not null
        default 1,

    generated_at timestamptz not null
        default now(),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint flashcard_decks_scope_type_check
        check (
            scope_type in (
                'subject',
                'file'
            )
        ),

    constraint flashcard_decks_scope_file_check
        check (
            (
                scope_type = 'file'
                and study_file_id is not null
            )
            or
            (
                scope_type = 'subject'
                and study_file_id is null
            )
        ),

    constraint flashcard_decks_title_check
        check (
            char_length(
                btrim(title)
            ) between 1 and 160
        ),

    constraint flashcard_decks_requested_card_count_check
        check (
            requested_card_count between 5 and 50
        ),

    constraint flashcard_decks_sources_array_check
        check (
            jsonb_typeof(sources) = 'array'
        ),

    constraint flashcard_decks_generation_model_check
        check (
            char_length(
                btrim(generation_model)
            ) between 1 and 120
        ),

    constraint flashcard_decks_generation_count_check
        check (
            generation_count >= 1
        )
);


create table public.flashcards (
    id uuid primary key default gen_random_uuid(),

    deck_id uuid not null
        references public.flashcard_decks(id)
        on delete cascade,

    position integer not null,

    question text not null,

    answer text not null,

    created_at timestamptz not null
        default now(),

    constraint flashcards_position_check
        check (
            position >= 0
        ),

    constraint flashcards_question_check
        check (
            char_length(
                btrim(question)
            ) between 1 and 2000
        ),

    constraint flashcards_answer_check
        check (
            char_length(
                btrim(answer)
            ) between 1 and 4000
        ),

    constraint flashcards_deck_position_unique
        unique (
            deck_id,
            position
        )
);


create index flashcard_decks_user_created_at_idx
    on public.flashcard_decks (
        user_id,
        created_at desc
    );

create index flashcard_decks_user_subject_idx
    on public.flashcard_decks (
        user_id,
        subject_id
    );

create index flashcard_decks_user_study_file_idx
    on public.flashcard_decks (
        user_id,
        study_file_id
    )
    where study_file_id is not null;

create index flashcards_deck_position_idx
    on public.flashcards (
        deck_id,
        position
    );


create or replace function public.validate_flashcard_deck_ownership_scope()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
    if not exists (
        select 1
        from public.subjects
        where id = new.subject_id
          and user_id = new.user_id
    ) then
        raise exception
            'Flashcard deck subject does not belong to the deck owner.'
            using errcode = '23514';
    end if;

    if new.scope_type = 'file' then
        if new.study_file_id is null then
            raise exception
                'File-scope flashcard deck requires a study file.'
                using errcode = '23514';
        end if;

        if not exists (
            select 1
            from public.study_files
            where id = new.study_file_id
              and user_id = new.user_id
              and subject_id = new.subject_id
        ) then
            raise exception
                'Flashcard deck study file does not belong to the deck owner and subject.'
                using errcode = '23514';
        end if;

    elsif new.scope_type = 'subject' then
        if new.study_file_id is not null then
            raise exception
                'Subject-scope flashcard deck cannot store a study file.'
                using errcode = '23514';
        end if;
    end if;

    return new;
end;
$$;


create trigger flashcard_decks_validate_ownership_scope
before insert or update of
    user_id,
    subject_id,
    study_file_id,
    scope_type
on public.flashcard_decks
for each row
execute function public.validate_flashcard_deck_ownership_scope();


create or replace function public.set_flashcard_deck_updated_at()
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


create trigger flashcard_decks_set_updated_at
before update
on public.flashcard_decks
for each row
execute function public.set_flashcard_deck_updated_at();


alter table public.flashcard_decks
enable row level security;

alter table public.flashcards
enable row level security;


revoke all
on table public.flashcard_decks
from anon;

revoke all
on table public.flashcard_decks
from authenticated;

revoke all
on table public.flashcards
from anon;

revoke all
on table public.flashcards
from authenticated;


grant select, delete
on table public.flashcard_decks
to authenticated;

grant select
on table public.flashcards
to authenticated;

grant all
on table public.flashcard_decks
to service_role;

grant all
on table public.flashcards
to service_role;


create policy "flashcard_decks_select_own"
on public.flashcard_decks
for select
to authenticated
using (
    auth.uid() = user_id
);


create policy "flashcard_decks_delete_own"
on public.flashcard_decks
for delete
to authenticated
using (
    auth.uid() = user_id
);


create policy "flashcards_select_owned_deck"
on public.flashcards
for select
to authenticated
using (
    exists (
        select 1
        from public.flashcard_decks
        where flashcard_decks.id = flashcards.deck_id
          and flashcard_decks.user_id = auth.uid()
    )
);