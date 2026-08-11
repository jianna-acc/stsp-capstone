// File: /frontend/features/quizzes/attempts-api.test.ts
// Purpose: Tests authenticated Quiz attempt start, answer,
// and result requests to the FastAPI backend.

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
  getQuizAttemptResult,
  startQuizAttempt,
  submitQuizAnswer,
} from "./attempts-api";

const QUIZ_ID =
  "11111111-1111-4111-8111-111111111111";

const ATTEMPT_ID =
  "22222222-2222-4222-8222-222222222222";

const QUESTION_ID =
  "33333333-3333-4333-8333-333333333333";

const ATTEMPT = {
  id:
    ATTEMPT_ID,

  quiz_id:
    QUIZ_ID,

  status:
    "in_progress",

  current_position:
    1,

  correct_count:
    0,

  question_count:
    2,

  score_percentage:
    0,

  started_at:
    "2026-08-10T00:00:00Z",

  completed_at:
    null,

  created_at:
    "2026-08-10T00:00:00Z",

  updated_at:
    "2026-08-10T00:00:00Z",
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
  "Quiz attempt API",
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
      "starts an authenticated Quiz attempt",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify(
                ATTEMPT,
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
          await startQuizAttempt(
            QUIZ_ID,
          );

        expect(
          result.id,
        ).toBe(
          ATTEMPT_ID,
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          `http://localhost:8000/api/quizzes/${QUIZ_ID}/attempts`,
          expect.objectContaining({
            method:
              "POST",

            headers: {
              Authorization:
                "Bearer test-access-token",
            },
          }),
        );
      },
    );

    it(
      "submits the expected question answer",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
                attempt: {
                  ...ATTEMPT,

                  current_position:
                    2,

                  correct_count:
                    1,

                  score_percentage:
                    50,
                },

                feedback: {
                  attempt_id:
                    ATTEMPT_ID,

                  quiz_question_id:
                    QUESTION_ID,

                  position:
                    1,

                  is_correct:
                    true,

                  correct_answer:
                    "Nucleus",

                  explanation:
                    "The nucleus contains genetic material.",

                  next_position:
                    2,

                  attempt_completed:
                    false,
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
          await submitQuizAnswer(
            ATTEMPT_ID,
            1,
            "Nucleus",
          );

        expect(
          result.feedback
            .is_correct,
        ).toBe(
          true,
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
          `http://localhost:8000/api/quiz-attempts/${ATTEMPT_ID}/questions/1/answer`,
        );

        expect(
          JSON.parse(
            requestOptions
              .body as string,
          ),
        ).toEqual({
          answer:
            "Nucleus",
        });
      },
    );

    it(
      "loads the completed Quiz result",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            new Response(
              JSON.stringify({
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

                strong_topics: [
                  {
                    topic:
                      "Cells",

                    correct_count:
                      1,

                    question_count:
                      1,

                    accuracy_percentage:
                      100,
                  },
                ],

                weak_topics: [
                  {
                    topic:
                      "Respiration",

                    correct_count:
                      0,

                    question_count:
                      1,

                    accuracy_percentage:
                      0,
                  },
                ],

                completed_at:
                  "2026-08-10T00:05:00Z",
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
          await getQuizAttemptResult(
            ATTEMPT_ID,
          );

        expect(
          result.score_percentage,
        ).toBe(
          50,
        );

        expect(
          result.strong_topics[
            0
          ].topic,
        ).toBe(
          "Cells",
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          `http://localhost:8000/api/quiz-attempts/${ATTEMPT_ID}/result`,
          expect.objectContaining({
            method:
              "GET",
          }),
        );
      },
    );

    it(
      "requires an authenticated session",
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
          startQuizAttempt(
            QUIZ_ID,
          ),
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