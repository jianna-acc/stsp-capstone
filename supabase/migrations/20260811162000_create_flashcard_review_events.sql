-- File: /supabase/migrations/20260811162000_create_flashcard_review_events.sql
-- Purpose: Stores authenticated Flashcard self-assessment review events
-- for durable study-performance analytics.

create table public.flashcard_review_events (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    deck_id uuid not null
        references public.flashcard_decks(id)
        on delete cascade,

    card_position integer not null,

    outcome text not null,

    reviewed_at timestamptz not null
        default now(),

    created_at timestamptz not null
        default now(),

    constraint flashcard_review_events_card_position_check
        check (
            card_position >= 0
        ),

    constraint flashcard_review_events_outcome_check
        check (
            outcome in (
                'known',
                'review_again'
            )
        )
);


create index flashcard_review_events_user_reviewed_at_idx
on public.flashcard_review_events (
    user_id,
    reviewed_at desc
);


create index flashcard_review_events_deck_reviewed_at_idx
on public.flashcard_review_events (
    deck_id,
    reviewed_at desc
);


create or replace function
public.validate_flashcard_review_event_scope()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
    if not exists (
        select 1
        from public.flashcard_decks
        join public.flashcards
          on flashcards.deck_id
             = flashcard_decks.id
        where flashcard_decks.id
              = new.deck_id
          and flashcard_decks.user_id
              = new.user_id
          and flashcards.position
              = new.card_position
    ) then
        raise exception
            'Flashcard review target does not belong to the review owner.'
            using errcode = '23514';
    end if;

    return new;
end;
$$;


create trigger flashcard_review_events_validate_scope
before insert or update of
    user_id,
    deck_id,
    card_position
on public.flashcard_review_events
for each row
execute function
public.validate_flashcard_review_event_scope();


alter table public.flashcard_review_events
enable row level security;


revoke all
on table public.flashcard_review_events
from anon;

revoke all
on table public.flashcard_review_events
from authenticated;


grant select
on table public.flashcard_review_events
to authenticated;


grant all
on table public.flashcard_review_events
to service_role;


create policy "flashcard_review_events_select_own"
on public.flashcard_review_events
for select
to authenticated
using (
    auth.uid() = user_id
);


comment on table public.flashcard_review_events is
    'Stores durable Flashcard self-assessment review events for study analytics.';

comment on column public.flashcard_review_events.outcome is
    'Student self-assessment: known or review_again.';