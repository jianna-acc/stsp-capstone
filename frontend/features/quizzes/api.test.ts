// File: /frontend/features/quizzes/api.test.ts
// Purpose: Tests authenticated Quiz-generation requests,
// response validation, and controlled frontend API errors.

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
  generateQuiz,
  QuizApiError,
} from "./api";

const QUIZ = {
  id:
    "11111111-1111-4111-8111-111111111111",

  subject_id:
    "22222222-2222-4222-8222-222222222222",

  study_file_id:
    null,

  scope_type:
    "subject",

  title:
    "Biology Practice Quiz",

  quiz_type:
    "mixed",

  difficulty:
    "medium",

  question_count:
    2,

  questions: [
    {
      id:
        "33333333-3333-4333-8333-333333333333",

      position:
        1,

      question_type:
        "multiple_choice",

      topic:
        "Cells",

      question:
        "Which structure contains genetic material?",

      choices: [
        "Nucleus",
        "Cell wall",
        "Cytoplasm",
      ],
    },
    {
      id:
        "44444444-4444-4444-8444-444444444444",

      position:
        2,

      question_type:
        "true_false",

      topic:
        "Cells",

      question:
        "The nucleus contains genetic material.",

      choices: [
        "True",
        "False",
      ],
    },
  ],

  generation_model:
    "gemini-test",

  generation_count:
    1,

  generated_at:
    "2026-08-09T15:00:00Z",

  created_at:
    "2026-08-09T15:00:00Z",

  updated_at:
    "2026-08-09T15:00:00Z",
} as const;

describe(
  "Quiz API",
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
      "sends the bearer token and Quiz generation options",
      async () => {
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

        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify(
                QUIZ,
              ),
              {
                status:
                  201,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        const result =
          await generateQuiz({
            scope_type:
              "subject",

            subject_id:
              QUIZ.subject_id,

            quiz_type:
              "mixed",

            difficulty:
              "medium",

            question_count:
              2,
          });

        expect(
          result.id,
        ).toBe(
          QUIZ.id,
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledTimes(
          1,
        );

        const [
          requestUrl,
          requestOptions,
        ] =
          mocks.fetch
            .mock.calls[
              0
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://localhost:8000/api/quizzes/generate",
        );

        expect(
          requestOptions,
        ).toEqual(
          expect.objectContaining({
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                "Bearer test-access-token",
            },

            cache:
              "no-store",
          }),
        );

        expect(
          JSON.parse(
            requestOptions
              .body as string,
          ),
        ).toEqual({
          scope_type:
            "subject",

          subject_id:
            QUIZ.subject_id,

          quiz_type:
            "mixed",

          difficulty:
            "medium",

          question_count:
            2,
        });
      },
    );

    it(
      "rejects Quiz generation without an authenticated session",
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
          generateQuiz({
            scope_type:
              "subject",

            subject_id:
              QUIZ.subject_id,

            quiz_type:
              "mixed",

            difficulty:
              "medium",

            question_count:
              2,
          }),
        ).rejects.toMatchObject({
          name:
            "QuizApiError",

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

    it(
      "rejects malformed successful Quiz responses",
      async () => {
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

        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
                id:
                  "broken",
              }),
              {
                status:
                  201,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        await expect(
          generateQuiz({
            scope_type:
              "subject",

            subject_id:
              QUIZ.subject_id,

            quiz_type:
              "mixed",

            difficulty:
              "medium",

            question_count:
              2,
          }),
        ).rejects.toMatchObject({
          name:
            "QuizApiError",

          status:
            502,

          code:
            "INVALID_QUIZ_RESPONSE",
        });
      },
    );

    it(
      "surfaces controlled backend errors",
      async () => {
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

        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
                error_code:
                  "QUIZ_SOURCE_UNAVAILABLE",

                message:
                  "The selected material is not ready.",
              }),
              {
                status:
                  409,

                headers: {
                  "Content-Type":
                    "application/json",
                },
              },
            ),
          );

        try {
          await generateQuiz({
            scope_type:
              "subject",

            subject_id:
              QUIZ.subject_id,

            quiz_type:
              "mixed",

            difficulty:
              "medium",

            question_count:
              2,
          });

          throw new Error(
            "Expected QuizApiError.",
          );
        } catch (error) {
          expect(
            error,
          ).toBeInstanceOf(
            QuizApiError,
          );

          expect(
            error,
          ).toMatchObject({
            status:
              409,

            code:
              "QUIZ_SOURCE_UNAVAILABLE",

            message:
              "The selected material is not ready.",
          });
        }
      },
    );
  },
);