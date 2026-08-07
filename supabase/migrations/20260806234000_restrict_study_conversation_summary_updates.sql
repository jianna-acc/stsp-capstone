-- File: /supabase/migrations/20260806234000_restrict_study_conversation_summary_updates.sql
-- Purpose: Prevents authenticated clients from modifying internal
-- Study Assistant summary state while preserving normal metadata edits.

revoke update
on table public.study_conversations
from authenticated;

grant update (
    title,
    subject_id,
    study_file_id
)
on table public.study_conversations
to authenticated;

grant update
on table public.study_conversations
to service_role;

comment on table
    public.study_conversations
is
    'Saved Study Assistant conversations. Authenticated clients may update normal metadata, while internal summary state is backend-managed.';
