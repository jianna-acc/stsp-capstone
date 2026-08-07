-- File: /supabase/migrations/20260806223000_add_study_conversation_summary_state.sql
-- Purpose: Adds bounded internal summary state for older Study
-- Assistant conversation messages.

alter table public.study_conversations
add column summary_text text;

alter table public.study_conversations
add column summarized_message_count integer
not null
default 0;

alter table public.study_conversations
add column summary_updated_at timestamptz;

alter table public.study_conversations
add column summary_version integer
not null
default 1;

alter table public.study_conversations
add constraint
    study_conversations_summary_text_length_check
check (
    summary_text is null
    or char_length(
        btrim(
            summary_text
        )
    ) between 1 and 4000
);

alter table public.study_conversations
add constraint
    study_conversations_summary_message_count_check
check (
    summarized_message_count >= 0
);

alter table public.study_conversations
add constraint
    study_conversations_summary_version_check
check (
    summary_version between 1 and 100
);

alter table public.study_conversations
add constraint
    study_conversations_summary_state_check
check (
    (
        summary_text is null
        and summarized_message_count = 0
        and summary_updated_at is null
    )
    or
    (
        summary_text is not null
        and summarized_message_count > 0
        and summary_updated_at is not null
    )
);

comment on column
    public.study_conversations.summary_text
is
    'Deterministic bounded summary of older conversation messages; not factual study evidence.';

comment on column
    public.study_conversations.summarized_message_count
is
    'Number of oldest saved messages represented by the stored conversation summary.';

comment on column
    public.study_conversations.summary_updated_at
is
    'Timestamp when the stored conversation summary was last refreshed.';

comment on column
    public.study_conversations.summary_version
is
    'Version of the deterministic conversation-summary format.';
