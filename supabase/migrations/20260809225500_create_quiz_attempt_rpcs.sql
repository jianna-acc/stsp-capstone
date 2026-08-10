-- File: /supabase/migrations/20260809225500_create_quiz_attempt_rpcs.sql
-- Purpose: Creates trusted atomic Quiz-attempt operations for starting
-- attempts and grading one expected question at a time without exposing
-- private Quiz answer keys to authenticated browser clients.

create or replace function public.start_quiz_attempt(
    p_user_id uuid,
    p_quiz_id uuid
)
returns table (
    id uuid,
    quiz_id uuid,
    status text,
    current_position integer,
    correct_count integer,
    question_count integer,
    score_percentage numeric,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz,
    updated_at timestamptz
)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_question_count integer;
    v_attempt_id uuid;
begin
    if p_user_id is null then
        raise exception
            'Quiz attempt owner is required.'
            using errcode = '23514';
    end if;

    if p_quiz_id is null then
        raise exception
            'Quiz attempt target is required.'
            using errcode = '23514';
    end if;

    select
        q.question_count
    into
        v_question_count
    from public.quizzes as q
    where q.id = p_quiz_id
      and q.user_id = p_user_id;

    if not found then
        raise exception
            'The requested Quiz was not found.'
            using errcode = 'P0002';
    end if;

    insert into public.quiz_attempts (
        user_id,
        quiz_id,
        question_count
    )
    values (
        p_user_id,
        p_quiz_id,
        v_question_count
    )
    returning quiz_attempts.id
    into v_attempt_id;

    return query
    select
        qa.id,
        qa.quiz_id,
        qa.status,
        qa.current_position,
        qa.correct_count,
        qa.question_count,
        qa.score_percentage,
        qa.started_at,
        qa.completed_at,
        qa.created_at,
        qa.updated_at
    from public.quiz_attempts as qa
    where qa.id = v_attempt_id;
end;
$$;


revoke execute on function
    public.start_quiz_attempt(
        uuid,
        uuid
    )
from public;

revoke execute on function
    public.start_quiz_attempt(
        uuid,
        uuid
    )
from anon;

revoke execute on function
    public.start_quiz_attempt(
        uuid,
        uuid
    )
from authenticated;

grant execute on function
    public.start_quiz_attempt(
        uuid,
        uuid
    )
to service_role;


create or replace function public.submit_quiz_attempt_answer(
    p_user_id uuid,
    p_attempt_id uuid,
    p_position integer,
    p_submitted_answer text
)
returns table (
    attempt_id uuid,
    quiz_id uuid,
    status text,
    current_position integer,
    correct_count integer,
    question_count integer,
    score_percentage numeric,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz,
    updated_at timestamptz,
    quiz_question_id uuid,
    answered_position integer,
    is_correct boolean,
    correct_answer text,
    explanation text,
    next_position integer,
    attempt_completed boolean
)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_attempt public.quiz_attempts%rowtype;
    v_question public.quiz_questions%rowtype;

    v_normalized_submitted text;
    v_normalized_correct text;

    v_is_correct boolean;
    v_new_correct_count integer;
    v_new_position integer;
    v_score_percentage numeric(5, 2);
    v_completed boolean;
    v_completed_at timestamptz;
begin
    if p_user_id is null then
        raise exception
            'Quiz attempt owner is required.'
            using errcode = '23514';
    end if;

    if p_attempt_id is null then
        raise exception
            'Quiz attempt ID is required.'
            using errcode = '23514';
    end if;

    if (
        p_position is null
        or p_position < 1
    ) then
        raise exception
            'Quiz answer position is invalid.'
            using errcode = '23514';
    end if;

    if (
        p_submitted_answer is null
        or char_length(
            btrim(
                p_submitted_answer
            )
        ) < 1
    ) then
        raise exception
            'Submitted Quiz answer must not be empty.'
            using errcode = '23514';
    end if;

    if char_length(
        btrim(
            p_submitted_answer
        )
    ) > 4000 then
        raise exception
            'Submitted Quiz answer is too long.'
            using errcode = '23514';
    end if;

    select
        qa.*
    into
        v_attempt
    from public.quiz_attempts as qa
    where qa.id = p_attempt_id
      and qa.user_id = p_user_id
    for update;

    if not found then
        raise exception
            'The requested Quiz attempt was not found.'
            using errcode = 'P0002';
    end if;

    if v_attempt.status <> 'in_progress' then
        raise exception
            'The Quiz attempt is already completed.'
            using errcode = '23514';
    end if;

    if p_position <> v_attempt.current_position then
        raise exception
            'The Quiz answer position does not match the current question.'
            using errcode = '23514';
    end if;

    select
        qq.*
    into
        v_question
    from public.quiz_questions as qq
    where qq.quiz_id = v_attempt.quiz_id
      and qq.position = p_position;

    if not found then
        raise exception
            'The current Quiz question was not found.'
            using errcode = 'P0002';
    end if;

    v_normalized_submitted = lower(
        regexp_replace(
            btrim(
                p_submitted_answer
            ),
            '\s+',
            ' ',
            'g'
        )
    );

    v_normalized_correct = lower(
        regexp_replace(
            btrim(
                v_question.correct_answer
            ),
            '\s+',
            ' ',
            'g'
        )
    );

    if (
        v_question.question_type
        = 'identification'
    ) then
        v_is_correct = (
            v_normalized_submitted
            = v_normalized_correct
        )
        or exists (
            select 1
            from jsonb_array_elements_text(
                v_question.accepted_answers
            ) as accepted_answer(
                answer
            )
            where lower(
                regexp_replace(
                    btrim(
                        accepted_answer.answer
                    ),
                    '\s+',
                    ' ',
                    'g'
                )
            ) = v_normalized_submitted
        );
    else
        v_is_correct = (
            v_normalized_submitted
            = v_normalized_correct
        );
    end if;

    insert into public.quiz_attempt_answers (
        attempt_id,
        quiz_question_id,
        position,
        topic,
        question_type,
        submitted_answer,
        is_correct
    )
    values (
        v_attempt.id,
        v_question.id,
        v_question.position,
        v_question.topic,
        v_question.question_type,
        btrim(
            p_submitted_answer
        ),
        v_is_correct
    );

    v_new_correct_count = (
        v_attempt.correct_count
        + case
            when v_is_correct then 1
            else 0
          end
    );

    v_new_position = (
        v_attempt.current_position
        + 1
    );

    v_completed = (
        p_position
        = v_attempt.question_count
    );

    v_score_percentage = round(
        (
            v_new_correct_count::numeric
            / v_attempt.question_count::numeric
        )
        * 100,
        2
    );

    if v_completed then
        v_completed_at = now();

        update public.quiz_attempts
        set
            status = 'completed',
            current_position = v_new_position,
            correct_count = v_new_correct_count,
            score_percentage = v_score_percentage,
            completed_at = v_completed_at
        where quiz_attempts.id = v_attempt.id;
    else
        update public.quiz_attempts
        set
            current_position = v_new_position,
            correct_count = v_new_correct_count,
            score_percentage = v_score_percentage
        where quiz_attempts.id = v_attempt.id;
    end if;

    return query
    select
        updated_attempt.id,
        updated_attempt.quiz_id,
        updated_attempt.status,
        updated_attempt.current_position,
        updated_attempt.correct_count,
        updated_attempt.question_count,
        updated_attempt.score_percentage,
        updated_attempt.started_at,
        updated_attempt.completed_at,
        updated_attempt.created_at,
        updated_attempt.updated_at,
        v_question.id,
        v_question.position,
        v_is_correct,
        v_question.correct_answer,
        v_question.explanation,
        case
            when v_completed then null
            else v_new_position
        end,
        v_completed
    from public.quiz_attempts
        as updated_attempt
    where updated_attempt.id
        = v_attempt.id;
end;
$$;


revoke execute on function
    public.submit_quiz_attempt_answer(
        uuid,
        uuid,
        integer,
        text
    )
from public;

revoke execute on function
    public.submit_quiz_attempt_answer(
        uuid,
        uuid,
        integer,
        text
    )
from anon;

revoke execute on function
    public.submit_quiz_attempt_answer(
        uuid,
        uuid,
        integer,
        text
    )
from authenticated;

grant execute on function
    public.submit_quiz_attempt_answer(
        uuid,
        uuid,
        integer,
        text
    )
to service_role;