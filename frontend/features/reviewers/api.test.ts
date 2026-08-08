// File: /frontend/features/reviewers/api.test.ts
// Purpose: Tests authenticated reviewer-generation requests,
// response validation, source metadata, and safe API errors.

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
  generateReviewer,
  ReviewerApiError,
} from "./api";

const REVIEWER_RESPONSE = {
  id: "reviewer-id",
  subject_id: "subject-id",
  study_file_id: "file-id",
  scope_type: "file",
  title: "Biology Reviewer",
  reviewer_length: "medium",

  content: {
    overview:
      "A reviewer covering the selected biology material.",

    topics: [
      {
        title:
          "Photosynthesis",

        summary:
          "Plants convert light energy into stored chemical energy.",

        key_points: [
          "Photosynthesis occurs mainly in chloroplasts.",
          "Light energy supports the production of glucose.",
        ],

        definitions: [
          {
            term:
              "Chloroplast",

            definition:
              "An organelle where photosynthesis occurs.",
          },
        ],
      },
    ],
  },

  sources: [
    {
      study_file_id:
        "file-id",

      source_name:
        "Biology Notes.pdf",

      chunk_index: 2,

      locator_type:
        "page",

      locator_label:
        "Page 3",
    },
  ],

  generation_model:
    "gemini-test-model",

  generation_count: 1,

  generated_at:
    "2026-08-08T08:00:00Z",

  created_at:
    "2026-08-08T08:00:00Z",

  updated_at:
    "2026-08-08T08:00:00Z",
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

describe(
  "generateReviewer",
  () => {
    beforeEach(() => {
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
      "rejects generation without an authenticated session",
      async () => {
        mocks.getSession
          .mockResolvedValue({
            data: {
              session: null,
            },

            error: null,
          });

        await expect(
          generateReviewer({
            scope_type:
              "subject",

            subject_id:
              "subject-id",

            reviewer_length:
              "short",
          }),
        ).rejects.toMatchObject({
          name:
            "ReviewerApiError",

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
      "sends the bearer token and reviewer generation options",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              REVIEWER_RESPONSE,
              201,
            ),
          );

        const controller =
          new AbortController();

        const result =
          await generateReviewer(
            {
              scope_type:
                "file",

              subject_id:
                "subject-id",

              study_file_id:
                "file-id",

              reviewer_length:
                "medium",
            },
            {
              signal:
                controller.signal,
            },
          );

        expect(result).toEqual(
          REVIEWER_RESPONSE,
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

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/reviewers/generate",
        );

        expect(
          requestOptions.method,
        ).toBe("POST");

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
          scope_type:
            "file",

          subject_id:
            "subject-id",

          study_file_id:
            "file-id",

          reviewer_length:
            "medium",
        });
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
            createJsonResponse(
              REVIEWER_RESPONSE,
              201,
            ),
          );

        await generateReviewer({
          scope_type:
            "file",

          subject_id:
            "subject-id",

          study_file_id:
            "file-id",

          reviewer_length:
            "medium",
        });

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
          "http://127.0.0.1:8000/api/reviewers/generate",
        );
      },
    );

    it(
      "maps a controlled backend reviewer error",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                error_code:
                  "REVIEWER_SOURCE_UNAVAILABLE",

                message:
                  "The selected study material is not ready for reviewer generation.",
              },
              409,
            ),
          );

        const requestPromise =
          generateReviewer({
            scope_type:
              "file",

            subject_id:
              "subject-id",

            study_file_id:
              "file-id",

            reviewer_length:
              "medium",
          });

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: 409,

          code:
            "REVIEWER_SOURCE_UNAVAILABLE",

          message:
            "The selected study material is not ready for reviewer generation.",
        });
      },
    );

    it(
      "rejects malformed successful reviewer responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                id:
                  "reviewer-id",

                scope_type:
                  "file",

                title:
                  "Incomplete reviewer",
              },
              201,
            ),
          );

        try {
          await generateReviewer({
            scope_type:
              "file",

            subject_id:
              "subject-id",

            study_file_id:
              "file-id",

            reviewer_length:
              "medium",
          });

          throw new Error(
            "The malformed reviewer response was accepted.",
          );
        } catch (error) {
          expect(
            error,
          ).toBeInstanceOf(
            ReviewerApiError,
          );

          expect(
            error,
          ).toMatchObject({
            status: 502,

            code:
              "INVALID_REVIEWER_RESPONSE",
          });
        }
      },
    );

    it(
      "rejects inconsistent reviewer scope responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                ...REVIEWER_RESPONSE,

                scope_type:
                  "subject",

                study_file_id:
                  "file-id",
              },
              201,
            ),
          );

        await expect(
          generateReviewer({
            scope_type:
              "subject",

            subject_id:
              "subject-id",

            reviewer_length:
              "medium",
          }),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_REVIEWER_RESPONSE",
        });
      },
    );

    it(
      "reports network failures without exposing the token",
      async () => {
        mocks.fetch
          .mockRejectedValue(
            new TypeError(
              "Network unavailable",
            ),
          );

        const requestPromise =
          generateReviewer({
            scope_type:
              "subject",

            subject_id:
              "subject-id",

            reviewer_length:
              "short",
          });

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: null,

          code:
            "REVIEWER_API_UNREACHABLE",

          message:
            "The reviewer could not connect to the backend.",
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
  },
);