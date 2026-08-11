// File: /frontend/features/quizzes/history-api.test.ts
// Purpose: Tests authenticated saved-Quiz listing, retrieval,
// attempt history, completed review, and deletion requests.

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks =
  vi.hoisted(
    () => ({
      getSession:
        vi.fn(),

      fetch:
        vi.fn(),
    }),
  );

vi.mock(
  "@/lib/supabase/client",
  () => ({
    createClient:
      () => ({
        auth: {
          getSession:
            mocks.getSession,
        },
      }),
  }),
);

import {
  deleteSavedQuiz,
  getQuizAttemptReview,
  getSavedQuiz,
  listQuizAttempts,
  listSavedQuizzes,
} from "./history-api";

const QUIZ_ID =
  "11111111-1111-4111-8111-111111111111";

const ATTEMPT_ID =
  "22222222-2222-4222-8222-222222222222";

const QUESTION_ID =
  "33333333-3333-4333-8333-333333333333";

const ANSWER_ID =
  "44444444-4444-4444-8444-444444444444";

const SUBJECT_ID =
  "55555555-5555-4555-8555-555555555555";

const COMPLETED_ATTEMPT = {
  id:
    ATTEMPT_ID,

  quiz_id:
    QUIZ_ID,

  status:
    "completed",

  current_position:
    3,

  correct_count:
    1,

  question_count:
    2,

  score_percentage:
    50,

  started_at:
    "2026-08-10T10:00:00Z",

  completed_at:
    "2026-08-10T10:05:00Z",

  created_at:
    "2026-08-10T10:00:00Z",

  updated_at:
    "2026-08-10T10:05:00Z",
};

const QUIZ_QUESTION = {
  id:
    QUESTION_ID,

  position:
    1,

  question_type:
    "identification",

  topic:
    "Cells",

  question:
    "What organelle contains genetic material?",

  choices:
    [],
};

const SAVED_QUIZ = {
  id:
    QUIZ_ID,

  subject_id:
    SUBJECT_ID,

  study_file_id:
    null,

  scope_type:
    "subject",

  title:
    "Cell Biology Practice",

  quiz_type:
    "mixed",

  difficulty:
    "medium",

  question_count:
    2,

  questions: [
    QUIZ_QUESTION,

    {
      id:
        "66666666-6666-4666-8666-666666666666",

      position:
        2,

      question_type:
        "true_false",

      topic:
        "Cells",

      question:
        "Cells contain membranes.",

      choices: [
        "True",
        "False",
      ],
    },
  ],

  generation_model:
    "test-model",

  generation_count:
    1,

  generated_at:
    "2026-08-10T09:55:00Z",

  created_at:
    "2026-08-10T09:55:00Z",

  updated_at:
    "2026-08-10T09:55:00Z",
};

function authenticate():
void {
  mocks.getSession
    .mockResolvedValue({
      data: {
        session: {
          access_token:
            "test-access-token",
        },
      },

      error:
        null,
    });
}

describe(
  "saved Quiz history API",
  () => {
    const originalApiUrl =
      process.env
        .NEXT_PUBLIC_API_BASE_URL;

    beforeEach(
      () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          "http://localhost:8000";

        mocks.getSession
          .mockReset();

        mocks.fetch
          .mockReset();

        vi.stubGlobal(
          "fetch",
          mocks.fetch,
        );

        authenticate();
      },
    );

    afterEach(
      () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          originalApiUrl;

        vi.unstubAllGlobals();
      },
    );

    it(
      "lists the authenticated student's saved Quizzes",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
                items: [
                  {
                    id:
                      QUIZ_ID,

                    subject_id:
                      SUBJECT_ID,

                    study_file_id:
                      null,

                    scope_type:
                      "subject",

                    title:
                      "Cell Biology Practice",

                    quiz_type:
                      "mixed",

                    difficulty:
                      "medium",

                    question_count:
                      2,

                    attempt_count:
                      1,

                    latest_attempt:
                      COMPLETED_ATTEMPT,

                    generated_at:
                      "2026-08-10T09:55:00Z",

                    created_at:
                      "2026-08-10T09:55:00Z",

                    updated_at:
                      "2026-08-10T09:55:00Z",
                  },
                ],
              }),
              {
                status:
                  200,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        const result =
          await listSavedQuizzes();

        expect(
          result.items,
        ).toHaveLength(
          1,
        );

        expect(
          result.items[0]
            .latest_attempt
            ?.score_percentage,
        ).toBe(
          50,
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          "http://localhost:8000/api/quizzes",
          expect.objectContaining({
            method:
              "GET",

            headers: {
              Authorization:
                "Bearer test-access-token",
            },
          }),
        );
      },
    );

    it(
      "loads one saved Quiz for taking or retaking",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify(
                SAVED_QUIZ,
              ),
              {
                status:
                  200,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        const result =
          await getSavedQuiz(
            QUIZ_ID,
          );

        expect(
          result.id,
        ).toBe(
          QUIZ_ID,
        );

        expect(
          result.questions,
        ).toHaveLength(
          2,
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          `http://localhost:8000/api/quizzes/${QUIZ_ID}`,
          expect.objectContaining({
            method:
              "GET",
          }),
        );
      },
    );

    it(
      "loads attempt history for one saved Quiz",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
                quiz_id:
                  QUIZ_ID,

                items: [
                  COMPLETED_ATTEMPT,
                ],
              }),
              {
                status:
                  200,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        const result =
          await listQuizAttempts(
            QUIZ_ID,
          );

        expect(
          result.quiz_id,
        ).toBe(
          QUIZ_ID,
        );

        expect(
          result.items[0]
            .status,
        ).toBe(
          "completed",
        );
      },
    );

    it(
      "loads a completed attempt review with correct answers",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
                attempt:
                  COMPLETED_ATTEMPT,

                answers: [
                  {
                    answer_id:
                      ANSWER_ID,

                    question:
                      QUIZ_QUESTION,

                    submitted_answer:
                      "Nucleus",

                    is_correct:
                      true,

                    correct_answer:
                      "Nucleus",

                    explanation:
                      "The nucleus contains the cell's genetic material.",

                    answered_at:
                      "2026-08-10T10:02:00Z",
                  },

                  {
                    answer_id:
                      "77777777-7777-4777-8777-777777777777",

                    question: {
                      id:
                        "66666666-6666-4666-8666-666666666666",

                      position:
                        2,

                      question_type:
                        "true_false",

                      topic:
                        "Cells",

                      question:
                        "Cells contain membranes.",

                      choices: [
                        "True",
                        "False",
                      ],
                    },

                    submitted_answer:
                      "False",

                    is_correct:
                      false,

                    correct_answer:
                      "True",

                    explanation:
                      "Cell membranes surround cells.",

                    answered_at:
                      "2026-08-10T10:04:00Z",
                  },
                ],

                result: {
                  attempt_id:
                    ATTEMPT_ID,

                  quiz_id:
                    QUIZ_ID,

                  correct_count:
                    1,

                  question_count:
                    2,

                  score_percentage:
                    50,

                  strong_topics:
                    [],

                  weak_topics: [
                    {
                      topic:
                        "Cells",

                      correct_count:
                        1,

                      question_count:
                        2,

                      accuracy_percentage:
                        50,
                    },
                  ],

                  completed_at:
                    "2026-08-10T10:05:00Z",
                },
              }),
              {
                status:
                  200,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        const result =
          await getQuizAttemptReview(
            ATTEMPT_ID,
          );

        expect(
          result.answers,
        ).toHaveLength(
          2,
        );

        expect(
          result.answers[1]
            .correct_answer,
        ).toBe(
          "True",
        );

        expect(
          result.result
            .score_percentage,
        ).toBe(
          50,
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          `http://localhost:8000/api/quiz-attempts/${ATTEMPT_ID}/review`,
          expect.objectContaining({
            method:
              "GET",
          }),
        );
      },
    );

    it(
      "deletes one owned saved Quiz",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              null,
              {
                status:
                  204,
              },
            ),
          );

        await expect(
          deleteSavedQuiz(
            QUIZ_ID,
          ),
        ).resolves.toBeUndefined();

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          `http://localhost:8000/api/quizzes/${QUIZ_ID}`,
          expect.objectContaining({
            method:
              "DELETE",

            headers: {
              Authorization:
                "Bearer test-access-token",
            },
          }),
        );
      },
    );

    it(
      "does not access history without authentication",
      async () => {
        mocks.getSession
          .mockResolvedValue({
            data: {
              session:
                null,
            },

            error:
              null,
          });

        await expect(
          listSavedQuizzes(),
        ).rejects.toMatchObject({
          status:
            401,

          code:
            "AUTHENTICATION_REQUIRED",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );
  },
);