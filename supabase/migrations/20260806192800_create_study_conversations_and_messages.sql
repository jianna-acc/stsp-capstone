-- File: /supabase/migrations/20260806192800_create_study_conversations_and_messages.sql
-- Purpose: Adds secure Study Assistant conversations, saved
-- messages, ownership validation, indexes, triggers, and RLS.

create table public.study_conversations (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    title text not null
        default 'New conversation',

    subject_id uuid
        references public.subjects(id)
        on delete set null,

    study_file_id uuid
        references public.study_files(id)
        on delete set null,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    last_message_at timestamptz not null
        default now(),

    constraint study_conversations_title_length_check
        check (
            char_length(btrim(title))
            between 1 and 120
        )
);

create table public.study_messages (
    id uuid primary key default gen_random_uuid(),

    conversation_id uuid not null
        references public.study_conversations(id)
        on delete cascade,

    role text not null,

    content text not null,

    outcome text,

    sources jsonb not null
        default '[]'::jsonb,

    created_at timestamptz not null
        default now(),

    constraint study_messages_role_check
        check (
            role in (
                'user',
                'assistant'
            )
        ),

    constraint study_messages_content_check
        check (
            char_length(btrim(content))
            between 1 and 50000
        ),

    constraint study_messages_sources_array_check
        check (
            jsonb_typeof(sources) = 'array'
        ),

    constraint study_messages_role_outcome_check
        check (
            (
                role = 'user'
                and outcome is null
                and sources = '[]'::jsonb
            )
            or
            (
                role = 'assistant'
                and outcome in (
                    'answered',
                    'no_context'
                )
            )
        )
);

create index study_conversations_user_recent_idx
    on public.study_conversations (
        user_id,
        last_message_at desc
    );

create index study_conversations_subject_idx
    on public.study_conversations (
        subject_id
    )
    where subject_id is not null;

create index study_conversations_study_file_idx
    on public.study_conversations (
        study_file_id
    )
    where study_file_id is not null;

create index study_messages_conversation_created_idx
    on public.study_messages (
        conversation_id,
        created_at,
        id
    );

create or replace function
public.validate_study_conversation_filters()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    selected_file_user_id uuid;
    selected_file_subject_id uuid;
begin
    if new.subject_id is not null then
        if not exists (
            select 1
            from public.subjects as subject
            where subject.id = new.subject_id
              and subject.user_id = new.user_id
        ) then
            raise exception
                'The selected subject does not belong to the conversation owner.'
                using errcode = '23514';
        end if;
    end if;

    if new.study_file_id is not null then
        select
            study_file.user_id,
            study_file.subject_id
        into
            selected_file_user_id,
            selected_file_subject_id
        from public.study_files as study_file
        where study_file.id = new.study_file_id;

        if not found then
            raise exception
                'The selected study file does not exist.'
                using errcode = '23514';
        end if;

        if selected_file_user_id
            is distinct from new.user_id then
            raise exception
                'The selected study file does not belong to the conversation owner.'
                using errcode = '23514';
        end if;

        if new.subject_id is null then
            new.subject_id :=
                selected_file_subject_id;
        elsif selected_file_subject_id
            is distinct from new.subject_id then
            raise exception
                'The selected study file does not belong to the selected subject.'
                using errcode = '23514';
        end if;
    end if;

    return new;
end;
$$;

create or replace function
public.set_study_conversation_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at := now();

    return new;
end;
$$;

create or replace function
public.touch_study_conversation_from_message()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    update public.study_conversations
    set
        last_message_at = greatest(
            last_message_at,
            new.created_at
        ),
        updated_at = now()
    where id = new.conversation_id;

    return new;
end;
$$;

create trigger study_conversations_validate_filters
before insert or update of
    user_id,
    subject_id,
    study_file_id
on public.study_conversations
for each row
execute function
    public.validate_study_conversation_filters();

create trigger study_conversations_set_updated_at
before update
on public.study_conversations
for each row
execute function
    public.set_study_conversation_updated_at();

create trigger study_messages_touch_conversation
after insert
on public.study_messages
for each row
execute function
    public.touch_study_conversation_from_message();

alter table public.study_conversations
    enable row level security;

alter table public.study_messages
    enable row level security;

create policy
    "Users can view their own study conversations"
on public.study_conversations
for select
to authenticated
using (
    auth.uid() = user_id
);

create policy
    "Users can create their own study conversations"
on public.study_conversations
for insert
to authenticated
with check (
    auth.uid() = user_id
);

create policy
    "Users can update their own study conversations"
on public.study_conversations
for update
to authenticated
using (
    auth.uid() = user_id
)
with check (
    auth.uid() = user_id
);

create policy
    "Users can delete their own study conversations"
on public.study_conversations
for delete
to authenticated
using (
    auth.uid() = user_id
);

create policy
    "Users can view messages from their conversations"
on public.study_messages
for select
to authenticated
using (
    exists (
        select 1
        from public.study_conversations
            as conversation
        where conversation.id =
            study_messages.conversation_id
          and conversation.user_id =
            auth.uid()
    )
);

create policy
    "Users can add messages to their conversations"
on public.study_messages
for insert
to authenticated
with check (
    exists (
        select 1
        from public.study_conversations
            as conversation
        where conversation.id =
            study_messages.conversation_id
          and conversation.user_id =
            auth.uid()
    )
);

revoke all
on table public.study_conversations
from anon;

revoke all
on table public.study_messages
from anon;

grant
    select,
    insert,
    update,
    delete
on table public.study_conversations
to authenticated;

grant
    select,
    insert
on table public.study_messages
to authenticated;

revoke all
on function
    public.validate_study_conversation_filters()
from public;

revoke all
on function
    public.set_study_conversation_updated_at()
from public;

revoke all
on function
    public.touch_study_conversation_from_message()
from public;

comment on table
    public.study_conversations
is
    'Saved Study Assistant conversations owned by authenticated users.';

comment on table
    public.study_messages
is
    'Saved user and assistant messages belonging to Study Assistant conversations.';

comment on column
    public.study_messages.sources
is
    'Safe citation metadata only; retrieved chunk text and embeddings are not stored.';