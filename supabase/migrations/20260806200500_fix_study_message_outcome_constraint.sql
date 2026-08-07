-- File: /supabase/migrations/20260806200500_fix_study_message_outcome_constraint.sql
-- Purpose: Ensures assistant messages require a valid outcome
-- instead of allowing a null result through SQL CHECK semantics.

alter table public.study_messages
drop constraint study_messages_role_outcome_check;

alter table public.study_messages
add constraint study_messages_role_outcome_check
check (
    (
        role = 'user'
        and outcome is null
        and sources = '[]'::jsonb
    )
    or
    (
        role = 'assistant'
        and outcome is not null
        and outcome in (
            'answered',
            'no_context'
        )
    )
);

comment on constraint
    study_messages_role_outcome_check
on public.study_messages
is
    'User messages require no outcome or sources; assistant messages require an answered or no_context outcome.';