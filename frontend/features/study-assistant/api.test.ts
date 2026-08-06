// File: /frontend/features/study-assistant/api.test.ts
// Purpose: Tests authenticated Study Assistant requests,
// response validation, filters, and safe API errors.

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
  askStudyAssistant,
  StudyAssistantApiError,
} from "./api";

const ANSWER_RESPONSE = {
  outcome: "answered",
  answer:
    "Photosynthesis converts light energy into chemical energy. [Source 1]",
  sources: [
    {
      source_number: 1,
      source_name:
        "Biology Notes.pdf",
      chunk_index: 2,
      similarity_score: 0.91,
    },
  ],
  retrieved_count: 3,
  source_count: 1,
  context_available: true,
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
      .mockResolvedValue(payload),
  } as unknown as Response;
}

describe(
  "askStudyAssistant",
  () => {
    beforeEach(() => {
      process.env
        .NEXT_PUBLIC_API_BASE_URL =
        "http://127.0.0.1:8000";

      mocks.createClient.mockReturnValue({
        auth: {
          getSession:
            mocks.getSession,
        },
      });

      mocks.getSession.mockResolvedValue({
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
        mocks.getSession.mockResolvedValue({
          data: {
            session: null,
          },
          error: null,
        });

        await expect(
          askStudyAssistant({
            question:
              "Explain photosynthesis.",
          }),
        ).rejects.toMatchObject({
          name:
            "StudyAssistantApiError",
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
      "sends the bearer token and optional filters",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse(
            ANSWER_RESPONSE,
          ),
        );

        const controller =
          new AbortController();

        const result =
          await askStudyAssistant(
            {
              question:
                "Explain photosynthesis.",
              subject_id:
                "subject-id",
              study_file_id:
                "file-id",
            },
            {
              signal:
                controller.signal,
            },
          );

        expect(result).toEqual(
          ANSWER_RESPONSE,
        );

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

        expect(requestUrl).toBe(
          "http://127.0.0.1:8000/api/rag/answer",
        );

        expect(
          requestOptions.method,
        ).toBe("POST");

        expect(
          requestOptions.cache,
        ).toBe("no-store");

        expect(
          requestOptions.signal,
        ).toBe(controller.signal);

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
          question:
            "Explain photosynthesis.",
          subject_id: "subject-id",
          study_file_id: "file-id",
        });
      },
    );

    it(
      "maps a controlled backend error",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse(
            {
              detail: {
                code:
                  "RAG_ORCHESTRATION_RETRIEVAL_FAILED",
                message:
                  "The study-material retrieval service is temporarily unavailable.",
              },
            },
            503,
          ),
        );

        const requestPromise =
          askStudyAssistant({
            question:
              "Explain the lesson.",
          });

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: 503,
          code:
            "RAG_ORCHESTRATION_RETRIEVAL_FAILED",
          message:
            "The study-material retrieval service is temporarily unavailable.",
        });
      },
    );

        it(
      "rejects malformed successful responses",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse({
            outcome: "answered",
            answer:
              "Incomplete response",
          }),
        );

        try {
          await askStudyAssistant({
            question:
              "Explain the lesson.",
          });

          throw new Error(
            "The malformed response was accepted.",
          );
        } catch (error) {
          expect(error).toBeInstanceOf(
            StudyAssistantApiError,
          );

          expect(error).toMatchObject({
            status: 502,
            code:
              "INVALID_RAG_RESPONSE",
          });
        }
      },
    );

    it(
      "reports network failures without exposing the token",
      async () => {
        mocks.fetch.mockRejectedValue(
          new TypeError(
            "Network unavailable",
          ),
        );

        const requestPromise =
          askStudyAssistant({
            question:
              "Explain the lesson.",
          });

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: null,
          code:
            "RAG_API_UNREACHABLE",
          message:
            "The Study Assistant could not connect to the backend.",
        });

        await requestPromise.catch(
          (error: unknown) => {
            expect(
              String(error),
            ).not.toContain(
              "test-access-token",
            );
          },
        );
      },
    );
  },
);