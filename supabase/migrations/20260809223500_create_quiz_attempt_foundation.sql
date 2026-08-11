-- File: /supabase/migrations/20260809223500_create_quiz_attempt_foundation.sql
-- Purpose: Creates persistent Quiz attempts and submitted-answer history
-- with ownership validation, progress constraints, RLS, and safe analytics
-- fields while keeping private Quiz answer keys in quiz_questions.

create table public.quiz_attempts (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    quiz_id uuid not null
        references public.quizzes(id)
        on delete cascade,

    status text not null
        default 'in_progress',

    current_position integer not null
        default 1,

    correct_count integer not null
        default 0,

    question_count integer not null,

    score_percentage numeric(5, 2) not null
        default 0,

    started_at timestamptz not null
        default now(),

    completed_at timestamptz,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint quiz_attempts_status_check
        check (
            status in (
                'in_progress',
                'completed'
            )
        ),

    constraint quiz_attempts_question_count_check
        check (
            question_count between 1 and 50
        ),

    constraint quiz_attempts_current_position_check
        check (
            current_position between 1
            and question_count + 1
        ),

    constraint quiz_attempts_correct_count_check
        check (
            correct_count between 0
            and question_count
        ),

    constraint quiz_attempts_score_percentage_check
        check (
            score_percentage between 0 and 100
        ),

    constraint quiz_attempts_completion_state_check
        check (
            (
                status = 'in_progress'
                and completed_at is null
                and current_position between 1
                    and question_count
            )
            or
            (
                status = 'completed'
                and completed_at is not null
                and current_position = question_count + 1
            )
        )
);


create table public.quiz_attempt_answers (
    id uuid primary key default gen_random_uuid(),

    attempt_id uuid not null
        references public.quiz_attempts(id)
        on delete cascade,

    quiz_question_id uuid not null
        references public.quiz_questions(id)
        on delete cascade,

    position integer not null,

    topic text not null,

    question_type text not null,

    submitted_answer text not null,

    is_correct boolean not null,

    answered_at timestamptz not null
        default now(),

    created_at timestamptz not null
        default now(),

    constraint quiz_attempt_answers_position_check
        check (
            position >= 1
        ),

    constraint quiz_attempt_answers_topic_check
        check (
            char_length(
                btrim(topic)
            ) >= 1
        ),

    constraint quiz_attempt_answers_type_check
        check (
            question_type in (
                'multiple_choice',
                'true_false',
                'identification'
            )
        ),

    constraint quiz_attempt_answers_submitted_answer_check
        check (
            char_length(
                btrim(submitted_answer)
            ) between 1 and 4000
        ),

    constraint quiz_attempt_answers_attempt_question_unique
        unique (
            attempt_id,
            quiz_question_id
        ),

    constraint quiz_attempt_answers_attempt_position_unique
        unique (
            attempt_id,
            position
        )
);


create index quiz_attempts_user_created_at_idx
on public.quiz_attempts (
    user_id,
    created_at desc
);


create index quiz_attempts_user_quiz_idx
on public.quiz_attempts (
    user_id,
    quiz_id,
    created_at desc
);


create index quiz_attempt_answers_attempt_position_idx
on public.quiz_attempt_answers (
    attempt_id,
    position
);


create index quiz_attempt_answers_question_idx
on public.quiz_attempt_answers (
    quiz_question_id
);


create or replace function public.validate_quiz_attempt_scope()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_quiz_user_id uuid;
    v_quiz_question_count integer;
begin
    select
        user_id,
        question_count
    into
        v_quiz_user_id,
        v_quiz_question_count
    from public.quizzes
    where id = new.quiz_id;

    if not found then
        raise exception
            'Quiz attempt target was not found.'
            using errcode = '23514';
    end if;

    if v_quiz_user_id <> new.user_id then
        raise exception
            'Quiz attempt owner does not own the target quiz.'
            using errcode = '23514';
    end if;

    if v_quiz_question_count <> new.question_count then
        raise exception
            'Quiz attempt question count does not match the quiz.'
            using errcode = '23514';
    end if;

    return new;
end;
$$;


create trigger quiz_attempts_validate_scope
before insert or update of
    user_id,
    quiz_id,
    question_count
on public.quiz_attempts
for each row
execute function public.validate_quiz_attempt_scope();


create or replace function public.validate_quiz_attempt_answer_scope()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_quiz_id uuid;
    v_attempt_status text;
begin
    select
        quiz_id,
        status
    into
        v_quiz_id,
        v_attempt_status
    from public.quiz_attempts
    where id = new.attempt_id;

    if not found then
        raise exception
            'Quiz attempt answer target was not found.'
            using errcode = '23514';
    end if;

    if v_attempt_status <> 'in_progress' then
        raise exception
            'Completed Quiz attempts cannot accept new answers.'
            using errcode = '23514';
    end if;

    if not exists (
        select 1
        from public.quiz_questions
        where id = new.quiz_question_id
          and quiz_id = v_quiz_id
          and position = new.position
          and topic = new.topic
          and question_type = new.question_type
    ) then
        raise exception
            'Quiz attempt answer does not match the target question.'
            using errcode = '23514';
    end if;

    return new;
end;
$$;


create trigger quiz_attempt_answers_validate_scope
before insert or update of
    attempt_id,
    quiz_question_id,
    position,
    topic,
    question_type
on public.quiz_attempt_answers
for each row
execute function public.validate_quiz_attempt_answer_scope();


create or replace function public.set_quiz_attempt_updated_at()
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


create trigger quiz_attempts_set_updated_at
before update
on public.quiz_attempts
for each row
execute function public.set_quiz_attempt_updated_at();


alter table public.quiz_attempts
enable row level security;

alter table public.quiz_attempt_answers
enable row level security;


revoke all
on table public.quiz_attempts
from anon;

revoke all
on table public.quiz_attempts
from authenticated;

revoke all
on table public.quiz_attempt_answers
from anon;

revoke all
on table public.quiz_attempt_answers
from authenticated;


grant select
on table public.quiz_attempts
to authenticated;

grant select
on table public.quiz_attempt_answers
to authenticated;


grant all
on table public.quiz_attempts
to service_role;

grant all
on table public.quiz_attempt_answers
to service_role;


create policy "quiz_attempts_select_own"
on public.quiz_attempts
for select
to authenticated
using (
    auth.uid() = user_id
);


create policy "quiz_attempt_answers_select_own"
on public.quiz_attempt_answers
for select
to authenticated
using (
    exists (
        select 1
        from public.quiz_attempts
        where quiz_attempts.id
            = quiz_attempt_answers.attempt_id
          and quiz_attempts.user_id
            = auth.uid()
    )
);