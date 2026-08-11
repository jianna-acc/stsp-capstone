// File: /frontend/features/academic-tasks/api.test.ts
// Purpose: Tests authenticated Academic Task CRUD,
// prioritized listing, response validation, and safe API errors.

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks = vi.hoisted(
  () => ({
    createClient: vi.fn(),
    getSession: vi.fn(),
    fetch: vi.fn(),
  }),
);

vi.mock(
  "@/lib/supabase/client",
  () => ({
    createClient:
      mocks.createClient,
  }),
);

import {
  AcademicTaskApiError,
  createAcademicTask,
  deleteAcademicTask,
  getAcademicTask,
  listAcademicTasks,
  listPrioritizedAcademicTasks,
  updateAcademicTask,
  updateAcademicTaskStatus,
} from "./api";

const TASK_ID =
  "11111111-1111-4111-8111-111111111111";

const SUBJECT_ID =
  "22222222-2222-4222-8222-222222222222";

const ACADEMIC_TASK_RESPONSE = {
  id: TASK_ID,
  subject_id: SUBJECT_ID,
  title: "Research assignment",
  description:
    "Complete the first draft.",
  deadline:
    "2026-08-20T12:00:00Z",
  estimated_minutes: 120,
  difficulty: "medium",
  task_type: "assignment",
  output_type: "writing",
  status: "pending",
  created_at:
    "2026-08-09T10:00:00Z",
  updated_at:
    "2026-08-09T10:00:00Z",
} as const;

const PRIORITY_RESPONSE = {
  task:
    ACADEMIC_TASK_RESPONSE,

  priority: {
    total_score: 72.5,
    deadline_score: 85,
    difficulty_score: 60,
    estimated_time_score: 60,
    output_confidence_score: 75,
    previous_performance_score: 50,
    available_study_time_score: 80,
    status_score: 50,
  },
} as const;

function createJsonResponse(
  payload: unknown,
  status = 200,
): Response {
  return {
    ok:
      status >= 200 &&
      status < 300,

    status,

    json: vi
      .fn()
      .mockResolvedValue(
        payload,
      ),
  } as unknown as Response;
}

function createEmptyResponse(
  status = 204,
): Response {
  return {
    ok:
      status >= 200 &&
      status < 300,

    status,
  } as unknown as Response;
}

describe(
  "Academic Task API",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      process.env
        .NEXT_PUBLIC_API_BASE_URL =
        "http://127.0.0.1:8000";

      mocks.createClient
        .mockReturnValue({
          auth: {
            getSession:
              mocks.getSession,
          },
        });

      mocks.getSession
        .mockResolvedValue({
          data: {
            session: {
              access_token:
                "test-access-token",
            },
          },

          error: null,
        });

      vi.stubGlobal(
        "fetch",
        mocks.fetch,
      );
    });

    afterEach(() => {
      delete process.env
        .NEXT_PUBLIC_API_BASE_URL;

      vi.unstubAllGlobals();
    });

    it(
      "rejects requests without an authenticated session",
      async () => {
        mocks.getSession
          .mockResolvedValue({
            data: {
              session: null,
            },

            error: null,
          });

        await expect(
          listAcademicTasks(),
        ).rejects.toMatchObject({
          name:
            "AcademicTaskApiError",

          status: 401,

          code:
            "AUTHENTICATION_REQUIRED",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "lists academic tasks with bearer authentication",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              items: [
                ACADEMIC_TASK_RESPONSE,
              ],
            }),
          );

        const controller =
          new AbortController();

        const result =
          await listAcademicTasks({
            limit: 25,
            signal:
              controller.signal,
          });

        expect(result).toEqual([
          ACADEMIC_TASK_RESPONSE,
        ]);

        expect(
          mocks.fetch,
        ).toHaveBeenCalledTimes(1);

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/academic-tasks?limit=25",
        );

        expect(
          requestOptions.method,
        ).toBe("GET");

        expect(
          requestOptions.cache,
        ).toBe("no-store");

        expect(
          requestOptions.signal,
        ).toBe(
          controller.signal,
        );

        expect(
          requestOptions.headers,
        ).toEqual({
          Authorization:
            "Bearer test-access-token",
        });
      },
    );

    it(
      "lists prioritized tasks with explainable scores",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              items: [
                PRIORITY_RESPONSE,
              ],
            }),
          );

        const result =
          await listPrioritizedAcademicTasks({
            limit: 10,
          });

        expect(result).toEqual([
          PRIORITY_RESPONSE,
        ]);

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/academic-tasks/prioritized?limit=10",
        );

        expect(
          requestOptions.method,
        ).toBe("GET");

        expect(
          requestOptions.headers,
        ).toEqual({
          Authorization:
            "Bearer test-access-token",
        });
      },
    );

    it(
      "creates an academic task",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ACADEMIC_TASK_RESPONSE,
              201,
            ),
          );

        const result =
          await createAcademicTask({
            subject_id:
              SUBJECT_ID,

            title:
              "Research assignment",

            description:
              "Complete the first draft.",

            deadline:
              "2026-08-20T12:00:00Z",

            estimated_minutes:
              120,

            difficulty:
              "medium",

            task_type:
              "assignment",

            output_type:
              "writing",
          });

        expect(result).toEqual(
          ACADEMIC_TASK_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/academic-tasks",
        );

        expect(
          requestOptions.method,
        ).toBe("POST");

        expect(
          requestOptions.headers,
        ).toEqual({
          "Content-Type":
            "application/json",

          Authorization:
            "Bearer test-access-token",
        });

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          subject_id:
            SUBJECT_ID,

          title:
            "Research assignment",

          description:
            "Complete the first draft.",

          deadline:
            "2026-08-20T12:00:00Z",

          estimated_minutes:
            120,

          difficulty:
            "medium",

          task_type:
            "assignment",

          output_type:
            "writing",
        });
      },
    );

    it(
      "gets one academic task",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ACADEMIC_TASK_RESPONSE,
            ),
          );

        const result =
          await getAcademicTask(
            TASK_ID,
          );

        expect(result).toEqual(
          ACADEMIC_TASK_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          `http://127.0.0.1:8000/api/academic-tasks/${TASK_ID}`,
        );

        expect(
          requestOptions.method,
        ).toBe("GET");
      },
    );

    it(
      "updates an academic task",
      async () => {
        const updatedTask = {
          ...ACADEMIC_TASK_RESPONSE,

          title:
            "Updated research assignment",

          difficulty:
            "hard" as const,

          output_type:
            "research" as const,
        };

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              updatedTask,
            ),
          );

        const result =
          await updateAcademicTask(
            TASK_ID,
            {
              title:
                "Updated research assignment",

              difficulty:
                "hard",

              output_type:
                "research",
            },
          );

        expect(result).toEqual(
          updatedTask,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          `http://127.0.0.1:8000/api/academic-tasks/${TASK_ID}`,
        );

        expect(
          requestOptions.method,
        ).toBe("PATCH");

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          title:
            "Updated research assignment",

          difficulty:
            "hard",

          output_type:
            "research",
        });
      },
    );

    it(
      "updates only the academic task status",
      async () => {
        const updatedTask = {
          ...ACADEMIC_TASK_RESPONSE,

          status:
            "in_progress" as const,
        };

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              updatedTask,
            ),
          );

        const result =
          await updateAcademicTaskStatus(
            TASK_ID,
            {
              status:
                "in_progress",
            },
          );

        expect(result).toEqual(
          updatedTask,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          `http://127.0.0.1:8000/api/academic-tasks/${TASK_ID}/status`,
        );

        expect(
          requestOptions.method,
        ).toBe("PATCH");

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          status:
            "in_progress",
        });
      },
    );

    it(
      "deletes an academic task using the authenticated endpoint",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createEmptyResponse(
              204,
            ),
          );

        await expect(
          deleteAcademicTask(
            TASK_ID,
          ),
        ).resolves.toBeUndefined();

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          `http://127.0.0.1:8000/api/academic-tasks/${TASK_ID}`,
        );

        expect(
          requestOptions.method,
        ).toBe("DELETE");

        expect(
          requestOptions.headers,
        ).toEqual({
          Authorization:
            "Bearer test-access-token",
        });

        expect(
          requestOptions.body,
        ).toBeUndefined();
      },
    );

    it(
      "supports an API base URL that already ends in api",
      async () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          "http://127.0.0.1:8000/api";

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              items: [
                ACADEMIC_TASK_RESPONSE,
              ],
            }),
          );

        await listAcademicTasks();

        const [
          requestUrl,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/academic-tasks",
        );
      },
    );

    it(
      "rejects invalid list limits before authentication or fetch",
      async () => {
        await expect(
          listAcademicTasks({
            limit: 101,
          }),
        ).rejects.toMatchObject({
          name:
            "AcademicTaskApiError",

          status: 400,

          code:
            "ACADEMIC_TASK_LIMIT_INVALID",
        });

        expect(
          mocks.getSession,
        ).not.toHaveBeenCalled();

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "maps controlled backend academic task errors",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                error_code:
                  "ACADEMIC_TASK_NOT_FOUND",

                message:
                  "The requested academic task was not found.",
              },
              404,
            ),
          );

        await expect(
          getAcademicTask(
            TASK_ID,
          ),
        ).rejects.toMatchObject({
          name:
            "AcademicTaskApiError",

          status: 404,

          code:
            "ACADEMIC_TASK_NOT_FOUND",

          message:
            "The requested academic task was not found.",
        });
      },
    );

    it(
      "rejects malformed successful task list responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              items: [
                {
                  id:
                    TASK_ID,

                  title:
                    "Incomplete task",
                },
              ],
            }),
          );

        await expect(
          listAcademicTasks(),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_ACADEMIC_TASK_LIST_RESPONSE",
        });
      },
    );

    it(
      "rejects invalid priority scores",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              items: [
                {
                  ...PRIORITY_RESPONSE,

                  priority: {
                    ...PRIORITY_RESPONSE
                      .priority,

                    total_score:
                      101,
                  },
                },
              ],
            }),
          );

        await expect(
          listPrioritizedAcademicTasks(),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_ACADEMIC_TASK_PRIORITY_RESPONSE",
        });
      },
    );

    it(
      "rejects empty task identifiers before making a request",
      async () => {
        await expect(
          getAcademicTask(
            "   ",
          ),
        ).rejects.toMatchObject({
          status: 400,

          code:
            "ACADEMIC_TASK_ID_REQUIRED",
        });

        expect(
          mocks.getSession,
        ).not.toHaveBeenCalled();

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "reports network failures without exposing the access token",
      async () => {
        mocks.fetch
          .mockRejectedValue(
            new TypeError(
              "Network unavailable",
            ),
          );

        const requestPromise =
          listAcademicTasks();

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: null,

          code:
            "ACADEMIC_TASK_API_UNREACHABLE",

          message:
            "The academic task service could not connect to the backend.",
        });

        await requestPromise.catch(
          (
            error: unknown,
          ) => {
            expect(
              String(error),
            ).not.toContain(
              "test-access-token",
            );
          },
        );
      },
    );

    it(
      "throws the feature error type for invalid successful responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              invalid: true,
            }),
          );

        try {
          await getAcademicTask(
            TASK_ID,
          );

          throw new Error(
            "Invalid Academic Task response was accepted.",
          );
        } catch (error) {
          expect(
            error,
          ).toBeInstanceOf(
            AcademicTaskApiError,
          );

          expect(
            error,
          ).toMatchObject({
            status: 502,

            code:
              "INVALID_ACADEMIC_TASK_RESPONSE",
          });
        }
      },
    );
  },
);