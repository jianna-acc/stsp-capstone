-- File: /supabase/migrations/20260809145600_create_flashcard_persistence_rpc.sql
-- Purpose: Creates the trusted atomic persistence function for generated
-- flashcard decks and their ordered flashcards.

create or replace function public.create_flashcard_deck_with_cards(
    p_user_id uuid,
    p_subject_id uuid,
    p_study_file_id uuid,
    p_scope_type text,
    p_title text,
    p_requested_card_count integer,
    p_sources jsonb,
    p_generation_model text,
    p_cards jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_deck_id uuid;
begin
    if p_user_id is null then
        raise exception
            'Flashcard deck owner is required.'
            using errcode = '23514';
    end if;

    if p_subject_id is null then
        raise exception
            'Flashcard deck subject is required.'
            using errcode = '23514';
    end if;

    if p_scope_type not in (
        'subject',
        'file'
    ) then
        raise exception
            'Flashcard deck scope is invalid.'
            using errcode = '23514';
    end if;

    if (
        p_scope_type = 'file'
        and p_study_file_id is null
    ) then
        raise exception
            'File-scope flashcard deck requires a study file.'
            using errcode = '23514';
    end if;

    if (
        p_scope_type = 'subject'
        and p_study_file_id is not null
    ) then
        raise exception
            'Subject-scope flashcard deck cannot store a study file.'
            using errcode = '23514';
    end if;

    if (
        p_requested_card_count < 5
        or p_requested_card_count > 50
    ) then
        raise exception
            'Flashcard requested card count is invalid.'
            using errcode = '23514';
    end if;

    if p_sources is null then
        p_sources := '[]'::jsonb;
    end if;

    if jsonb_typeof(p_sources) <> 'array' then
        raise exception
            'Flashcard sources must be a JSON array.'
            using errcode = '23514';
    end if;

    if (
        p_cards is null
        or jsonb_typeof(p_cards) <> 'array'
    ) then
        raise exception
            'Flashcard cards must be a JSON array.'
            using errcode = '23514';
    end if;

    if (
        jsonb_array_length(p_cards)
        <> p_requested_card_count
    ) then
        raise exception
            'Generated flashcard count does not match the requested count.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_cards) as card
        where
            jsonb_typeof(card) <> 'object'
            or not (card ? 'question')
            or not (card ? 'answer')
            or jsonb_typeof(card -> 'question') <> 'string'
            or jsonb_typeof(card -> 'answer') <> 'string'
            or char_length(
                btrim(card ->> 'question')
            ) not between 1 and 2000
            or char_length(
                btrim(card ->> 'answer')
            ) not between 1 and 4000
    ) then
        raise exception
            'Generated flashcard data is invalid.'
            using errcode = '23514';
    end if;

    insert into public.flashcard_decks (
        user_id,
        subject_id,
        study_file_id,
        scope_type,
        title,
        requested_card_count,
        sources,
        generation_model
    )
    values (
        p_user_id,
        p_subject_id,
        p_study_file_id,
        p_scope_type,
        btrim(p_title),
        p_requested_card_count,
        p_sources,
        btrim(p_generation_model)
    )
    returning id
    into v_deck_id;

    insert into public.flashcards (
        deck_id,
        position,
        question,
        answer
    )
    select
        v_deck_id,
        ordinality - 1,
        btrim(card ->> 'question'),
        btrim(card ->> 'answer')
    from jsonb_array_elements(p_cards)
        with ordinality as generated_card(
            card,
            ordinality
        );

    return v_deck_id;
end;
$$;


revoke execute on function
    public.create_flashcard_deck_with_cards(
        uuid,
        uuid,
        uuid,
        text,
        text,
        integer,
        jsonb,
        text,
        jsonb
    )
from public;

revoke execute on function
    public.create_flashcard_deck_with_cards(
        uuid,
        uuid,
        uuid,
        text,
        text,
        integer,
        jsonb,
        text,
        jsonb
    )
from anon;

revoke execute on function
    public.create_flashcard_deck_with_cards(
        uuid,
        uuid,
        uuid,
        text,
        text,
        integer,
        jsonb,
        text,
        jsonb
    )
from authenticated;


grant execute on function
    public.create_flashcard_deck_with_cards(
        uuid,
        uuid,
        uuid,
        text,
        text,
        integer,
        jsonb,
        text,
        jsonb
    )
to service_role;
