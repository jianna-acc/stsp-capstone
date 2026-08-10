-- File: /supabase/migrations/20260809211600_create_quiz_persistence_rpc.sql
-- Purpose: Creates the trusted atomic persistence function for generated
-- quizzes and their private ordered question/answer records.

create or replace function public.create_quiz_with_questions(
    p_user_id uuid,
    p_subject_id uuid,
    p_study_file_id uuid,
    p_scope_type text,
    p_title text,
    p_quiz_type text,
    p_difficulty text,
    p_question_count integer,
    p_generation_model text,
    p_questions jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_quiz_id uuid;
begin
    if p_user_id is null then
        raise exception
            'Quiz owner is required.'
            using errcode = '23514';
    end if;

    if p_subject_id is null then
        raise exception
            'Quiz subject is required.'
            using errcode = '23514';
    end if;

    if p_scope_type not in (
        'subject',
        'file'
    ) then
        raise exception
            'Quiz scope is invalid.'
            using errcode = '23514';
    end if;

    if (
        p_scope_type = 'file'
        and p_study_file_id is null
    ) then
        raise exception
            'File-scope Quiz requires a study file.'
            using errcode = '23514';
    end if;

    if (
        p_scope_type = 'subject'
        and p_study_file_id is not null
    ) then
        raise exception
            'Subject-scope Quiz cannot store a study file.'
            using errcode = '23514';
    end if;

    if (
        p_title is null
        or char_length(
            btrim(p_title)
        ) not between 1 and 160
    ) then
        raise exception
            'Quiz title is invalid.'
            using errcode = '23514';
    end if;

    if p_quiz_type not in (
        'multiple_choice',
        'true_false',
        'identification',
        'mixed'
    ) then
        raise exception
            'Quiz type is invalid.'
            using errcode = '23514';
    end if;

    if p_difficulty not in (
        'easy',
        'medium',
        'hard'
    ) then
        raise exception
            'Quiz difficulty is invalid.'
            using errcode = '23514';
    end if;

    if (
        p_question_count < 1
        or p_question_count > 50
    ) then
        raise exception
            'Quiz question count is invalid.'
            using errcode = '23514';
    end if;

    if (
        p_generation_model is null
        or char_length(
            btrim(p_generation_model)
        ) < 1
    ) then
        raise exception
            'Quiz generation model is invalid.'
            using errcode = '23514';
    end if;

    if (
        p_questions is null
        or jsonb_typeof(p_questions) <> 'array'
    ) then
        raise exception
            'Quiz questions must be a JSON array.'
            using errcode = '23514';
    end if;

    if (
        jsonb_array_length(p_questions)
        <> p_question_count
    ) then
        raise exception
            'Generated Quiz count does not match the requested count.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        where
            jsonb_typeof(question) <> 'object'

            or not (question ? 'position')
            or not (question ? 'question_type')
            or not (question ? 'topic')
            or not (question ? 'question')
            or not (question ? 'choices')
            or not (question ? 'correct_answer')
            or not (question ? 'accepted_answers')
            or not (question ? 'explanation')

            or jsonb_typeof(
                question -> 'position'
            ) <> 'number'

            or jsonb_typeof(
                question -> 'question_type'
            ) <> 'string'

            or jsonb_typeof(
                question -> 'topic'
            ) <> 'string'

            or jsonb_typeof(
                question -> 'question'
            ) <> 'string'

            or jsonb_typeof(
                question -> 'choices'
            ) <> 'array'

            or jsonb_typeof(
                question -> 'correct_answer'
            ) <> 'string'

            or jsonb_typeof(
                question -> 'accepted_answers'
            ) <> 'array'

            or jsonb_typeof(
                question -> 'explanation'
            ) <> 'string'

            or char_length(
                btrim(
                    question ->> 'topic'
                )
            ) < 1

            or char_length(
                btrim(
                    question ->> 'question'
                )
            ) < 1

            or char_length(
                btrim(
                    question ->> 'correct_answer'
                )
            ) < 1

            or char_length(
                btrim(
                    question ->> 'explanation'
                )
            ) < 1
    ) then
        raise exception
            'Generated Quiz question data is invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        where (
            question ->> 'question_type'
        ) not in (
            'multiple_choice',
            'true_false',
            'identification'
        )
    ) then
        raise exception
            'Generated Quiz question type is invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        where
            (
                question ->> 'position'
            ) !~ '^[0-9]+$'
            or (
                question ->> 'position'
            )::integer < 1
            or (
                question ->> 'position'
            )::integer > p_question_count
    ) then
        raise exception
            'Generated Quiz question position is invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        cross join lateral jsonb_array_elements(
            question -> 'choices'
        ) as choice
        where
            jsonb_typeof(choice) <> 'string'
            or char_length(
                btrim(
                    choice #>> '{}'
                )
            ) < 1
    ) then
        raise exception
            'Generated Quiz choices are invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        cross join lateral jsonb_array_elements(
            question -> 'accepted_answers'
        ) as accepted_answer
        where
            jsonb_typeof(
                accepted_answer
            ) <> 'string'
            or char_length(
                btrim(
                    accepted_answer #>> '{}'
                )
            ) < 1
    ) then
        raise exception
            'Generated Quiz accepted answers are invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        where
            question ->> 'question_type'
                = 'multiple_choice'
            and (
                jsonb_array_length(
                    question -> 'choices'
                ) < 2
                or jsonb_array_length(
                    question -> 'accepted_answers'
                ) <> 0
                or not exists (
                    select 1
                    from jsonb_array_elements_text(
                        question -> 'choices'
                    ) as choice
                    where lower(
                        btrim(choice)
                    ) = lower(
                        btrim(
                            question ->> 'correct_answer'
                        )
                    )
                )
            )
    ) then
        raise exception
            'Generated multiple-choice Quiz data is invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        where
            question ->> 'question_type'
                = 'true_false'
            and (
                jsonb_array_length(
                    question -> 'choices'
                ) <> 2
                or jsonb_array_length(
                    question -> 'accepted_answers'
                ) <> 0
                or lower(
                    btrim(
                        question ->> 'correct_answer'
                    )
                ) not in (
                    'true',
                    'false'
                )
                or not (
                    exists (
                        select 1
                        from jsonb_array_elements_text(
                            question -> 'choices'
                        ) as choice
                        where lower(
                            btrim(choice)
                        ) = 'true'
                    )
                    and exists (
                        select 1
                        from jsonb_array_elements_text(
                            question -> 'choices'
                        ) as choice
                        where lower(
                            btrim(choice)
                        ) = 'false'
                    )
                )
            )
    ) then
        raise exception
            'Generated true-or-false Quiz data is invalid.'
            using errcode = '23514';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(p_questions) as question
        where
            question ->> 'question_type'
                = 'identification'
            and jsonb_array_length(
                question -> 'choices'
            ) <> 0
    ) then
        raise exception
            'Generated identification Quiz data is invalid.'
            using errcode = '23514';
    end if;

    insert into public.quizzes (
        user_id,
        subject_id,
        study_file_id,
        scope_type,
        title,
        quiz_type,
        difficulty,
        question_count,
        generation_model
    )
    values (
        p_user_id,
        p_subject_id,
        p_study_file_id,
        p_scope_type,
        btrim(p_title),
        p_quiz_type,
        p_difficulty,
        p_question_count,
        btrim(p_generation_model)
    )
    returning id
    into v_quiz_id;

    insert into public.quiz_questions (
        quiz_id,
        position,
        question_type,
        topic,
        question,
        choices,
        correct_answer,
        accepted_answers,
        explanation
    )
    select
        v_quiz_id,
        (
            generated_question.question
            ->> 'position'
        )::integer,
        generated_question.question
            ->> 'question_type',
        btrim(
            generated_question.question
            ->> 'topic'
        ),
        btrim(
            generated_question.question
            ->> 'question'
        ),
        generated_question.question
            -> 'choices',
        btrim(
            generated_question.question
            ->> 'correct_answer'
        ),
        generated_question.question
            -> 'accepted_answers',
        btrim(
            generated_question.question
            ->> 'explanation'
        )
    from jsonb_array_elements(
        p_questions
    ) as generated_question(
        question
    );

    return v_quiz_id;
end;
$$;


revoke execute on function
    public.create_quiz_with_questions(
        uuid,
        uuid,
        uuid,
        text,
        text,
        text,
        text,
        integer,
        text,
        jsonb
    )
from public;

revoke execute on function
    public.create_quiz_with_questions(
        uuid,
        uuid,
        uuid,
        text,
        text,
        text,
        text,
        integer,
        text,
        jsonb
    )
from anon;

revoke execute on function
    public.create_quiz_with_questions(
        uuid,
        uuid,
        uuid,
        text,
        text,
        text,
        text,
        integer,
        text,
        jsonb
    )
from authenticated;


grant execute on function
    public.create_quiz_with_questions(
        uuid,
        uuid,
        uuid,
        text,
        text,
        text,
        text,
        integer,
        text,
        jsonb
    )
to service_role;