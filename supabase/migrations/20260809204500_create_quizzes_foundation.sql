-- File: /supabase/migrations/20260809204500_create_quizzes_foundation.sql
-- Purpose: Creates persistent quizzes and private quiz-question answer
-- storage with ownership validation, indexes, timestamps, privileges,
-- and Row Level Security.

create table public.quizzes (
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

    quiz_type text not null,

    difficulty text not null,

    question_count integer not null,

    generation_model text not null,

    generation_count integer not null
        default 1,

    generated_at timestamptz not null
        default now(),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint quizzes_scope_type_check
        check (
            scope_type in (
                'subject',
                'file'
            )
        ),

    constraint quizzes_scope_file_check
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

    constraint quizzes_title_check
        check (
            char_length(
                btrim(title)
            ) between 1 and 160
        ),

    constraint quizzes_type_check
        check (
            quiz_type in (
                'multiple_choice',
                'true_false',
                'identification',
                'mixed'
            )
        ),

    constraint quizzes_difficulty_check
        check (
            difficulty in (
                'easy',
                'medium',
                'hard'
            )
        ),

    constraint quizzes_question_count_check
        check (
            question_count between 1 and 50
        ),

    constraint quizzes_generation_model_check
        check (
            char_length(
                btrim(generation_model)
            ) >= 1
        ),

    constraint quizzes_generation_count_check
        check (
            generation_count >= 1
        )
);


create table public.quiz_questions (
    id uuid primary key default gen_random_uuid(),

    quiz_id uuid not null
        references public.quizzes(id)
        on delete cascade,

    position integer not null,

    question_type text not null,

    topic text not null,

    question text not null,

    choices jsonb not null
        default '[]'::jsonb,

    correct_answer text not null,

    accepted_answers jsonb not null
        default '[]'::jsonb,

    explanation text not null,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint quiz_questions_position_check
        check (
            position >= 1
        ),

    constraint quiz_questions_type_check
        check (
            question_type in (
                'multiple_choice',
                'true_false',
                'identification'
            )
        ),

    constraint quiz_questions_topic_check
        check (
            char_length(
                btrim(topic)
            ) >= 1
        ),

    constraint quiz_questions_question_check
        check (
            char_length(
                btrim(question)
            ) >= 1
        ),

    constraint quiz_questions_choices_array_check
        check (
            jsonb_typeof(choices) = 'array'
        ),

    constraint quiz_questions_answer_check
        check (
            char_length(
                btrim(correct_answer)
            ) >= 1
        ),

    constraint quiz_questions_accepted_answers_array_check
        check (
            jsonb_typeof(accepted_answers) = 'array'
        ),

    constraint quiz_questions_explanation_check
        check (
            char_length(
                btrim(explanation)
            ) >= 1
        ),

    constraint quiz_questions_type_structure_check
        check (
            (
                question_type = 'multiple_choice'
                and jsonb_array_length(choices) >= 2
                and jsonb_array_length(accepted_answers) = 0
            )
            or
            (
                question_type = 'true_false'
                and jsonb_array_length(choices) = 2
                and jsonb_array_length(accepted_answers) = 0
            )
            or
            (
                question_type = 'identification'
                and jsonb_array_length(choices) = 0
            )
        ),

    constraint quiz_questions_quiz_position_unique
        unique (
            quiz_id,
            position
        )
);


create index quizzes_user_created_at_idx
on public.quizzes (
    user_id,
    created_at desc
);


create index quizzes_user_subject_idx
on public.quizzes (
    user_id,
    subject_id
);


create index quizzes_user_study_file_idx
on public.quizzes (
    user_id,
    study_file_id
)
where study_file_id is not null;


create index quiz_questions_quiz_idx
on public.quiz_questions (
    quiz_id
);


create or replace function public.validate_quiz_ownership_scope()
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
            'Quiz subject does not belong to the quiz owner.'
            using errcode = '23514';
    end if;

    if new.scope_type = 'file' then
        if new.study_file_id is null then
            raise exception
                'File-scope quiz requires a study file.'
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
                'Quiz study file does not belong to the quiz owner and subject.'
                using errcode = '23514';
        end if;

    elsif new.scope_type = 'subject' then
        if new.study_file_id is not null then
            raise exception
                'Subject-scope quiz cannot store a study file.'
                using errcode = '23514';
        end if;
    end if;

    return new;
end;
$$;


create trigger quizzes_validate_ownership_scope
before insert or update of
    user_id,
    subject_id,
    study_file_id,
    scope_type
on public.quizzes
for each row
execute function public.validate_quiz_ownership_scope();


create or replace function public.set_quiz_updated_at()
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


create trigger quizzes_set_updated_at
before update
on public.quizzes
for each row
execute function public.set_quiz_updated_at();


create or replace function public.set_quiz_question_updated_at()
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


create trigger quiz_questions_set_updated_at
before update
on public.quiz_questions
for each row
execute function public.set_quiz_question_updated_at();


alter table public.quizzes
enable row level security;


alter table public.quiz_questions
enable row level security;


revoke all
on table public.quizzes
from anon;


revoke all
on table public.quizzes
from authenticated;


revoke all
on table public.quiz_questions
from anon;


revoke all
on table public.quiz_questions
from authenticated;


grant select, delete
on table public.quizzes
to authenticated;


grant all
on table public.quizzes
to service_role;


grant all
on table public.quiz_questions
to service_role;


create policy "quizzes_select_own"
on public.quizzes
for select
to authenticated
using (
    auth.uid() = user_id
);


create policy "quizzes_delete_own"
on public.quizzes
for delete
to authenticated
using (
    auth.uid() = user_id
);