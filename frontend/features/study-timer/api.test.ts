// File: /frontend/features/study-timer/api.test.ts
// Purpose: Tests authenticated Study Activity timer requests,
// lifecycle endpoints, response validation, and safe API errors.

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
      createClient:
        vi.fn(),
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
      mocks.createClient,
  }),
);


import {
  endStudyActivity,
  endStudyActivityBreak,
  getActiveStudyActivity,
  pauseStudyActivity,
  resumeStudyActivity,
  startStudyActivity,
  startStudyActivityBreak,
} from "./api";


const ACTIVITY_RESPONSE = {
  id:
    "activity-id",

  subject_id:
    "subject-id",

  study_plan_id:
    "plan-id",

  study_session_id:
    "session-id",

  title:
    "Biology review",

  status:
    "running",

  mode:
    "focus",

  started_at:
    "2026-08-12T08:00:00Z",

  ended_at:
    null,

  segment_started_at:
    "2026-08-12T08:00:00Z",

  focus_seconds:
    1200,

  break_seconds:
    300,

  created_at:
    "2026-08-12T08:00:00Z",

  updated_at:
    "2026-08-12T08:00:00Z",
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

    json:
      vi.fn()
        .mockResolvedValue(
          payload,
        ),
  } as unknown as Response;
}


describe(
  "Study Activity timer API",
  () => {
    beforeEach(
      () => {
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

            error:
              null,
          });

        vi.stubGlobal(
          "fetch",
          mocks.fetch,
        );
      },
    );


    afterEach(
      () => {
        delete process.env
          .NEXT_PUBLIC_API_BASE_URL;

        vi.unstubAllGlobals();
      },
    );


    it(
      "rejects active-timer loading without an authenticated session",
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
          getActiveStudyActivity(),
        ).rejects.toMatchObject({
          name:
            "StudyActivityApiError",

          status:
            401,

          code:
            "AUTH_SESSION_REQUIRED",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      "loads the authenticated active timer",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ACTIVITY_RESPONSE,
            ),
          );

        const controller =
          new AbortController();

        const result =
          await getActiveStudyActivity({
            signal:
              controller.signal,
          });

        expect(
          result,
        ).toEqual(
          ACTIVITY_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] =
          mocks.fetch.mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/study-activity/active",
        );

        expect(
          requestOptions.method,
        ).toBe(
          "GET",
        );

        expect(
          requestOptions.signal,
        ).toBe(
          controller.signal,
        );

        const headers =
          requestOptions
            .headers as Headers;

        expect(
          headers.get(
            "Authorization",
          ),
        ).toBe(
          "Bearer test-access-token",
        );
      },
    );


    it(
      "returns null when no active timer exists",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              null,
            ),
          );

        await expect(
          getActiveStudyActivity(),
        ).resolves.toBeNull();
      },
    );


    it(
      "starts a scheduled Study Plan session",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ACTIVITY_RESPONSE,
              201,
            ),
          );

        const result =
          await startStudyActivity({
            study_session_id:
              "session-id",
          });

        expect(
          result,
        ).toEqual(
          ACTIVITY_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] =
          mocks.fetch.mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/study-activity/start",
        );

        expect(
          requestOptions.method,
        ).toBe(
          "POST",
        );

        const headers =
          requestOptions
            .headers as Headers;

        expect(
          headers.get(
            "Authorization",
          ),
        ).toBe(
          "Bearer test-access-token",
        );

        expect(
          headers.get(
            "Content-Type",
          ),
        ).toBe(
          "application/json",
        );

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          study_session_id:
            "session-id",
        });
      },
    );


    it(
      "uses all trusted lifecycle transition endpoints",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ACTIVITY_RESPONSE,
            ),
          );

        await pauseStudyActivity(
          "activity-id",
        );

        await resumeStudyActivity(
          "activity-id",
        );

        await startStudyActivityBreak(
          "activity-id",
        );

        await endStudyActivityBreak(
          "activity-id",
        );

        await endStudyActivity(
          "activity-id",
        );

        const calledUrls =
          mocks.fetch.mock.calls.map(
            (
              call,
            ) =>
              call[0],
          );

        expect(
          calledUrls,
        ).toEqual([
          "http://127.0.0.1:8000/api/study-activity/activity-id/pause",
          "http://127.0.0.1:8000/api/study-activity/activity-id/resume",
          "http://127.0.0.1:8000/api/study-activity/activity-id/break/start",
          "http://127.0.0.1:8000/api/study-activity/activity-id/break/end",
          "http://127.0.0.1:8000/api/study-activity/activity-id/end",
        ]);

        mocks.fetch.mock.calls.forEach(
          (
            call,
          ) => {
            const options =
              call[1] as RequestInit;

            expect(
              options.method,
            ).toBe(
              "POST",
            );

            const headers =
              options.headers as Headers;

            expect(
              headers.get(
                "Authorization",
              ),
            ).toBe(
              "Bearer test-access-token",
            );
          },
        );
      },
    );


    it(
      "maps a controlled active-timer conflict",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                error_code:
                  "STUDY_ACTIVITY_CONFLICT",

                message:
                  "The study timer is not in a valid state for that action.",
              },
              409,
            ),
          );

        await expect(
          startStudyActivity({
            study_session_id:
              "session-id",
          }),
        ).rejects.toMatchObject({
          name:
            "StudyActivityApiError",

          status:
            409,

          code:
            "STUDY_ACTIVITY_CONFLICT",

          message:
            "The study timer is not in a valid state for that action.",
        });
      },
    );


    it(
      "rejects malformed successful timer responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              id:
                "activity-id",

              status:
                "running",
            }),
          );

        await expect(
          getActiveStudyActivity(),
        ).rejects.toMatchObject({
          name:
            "StudyActivityApiError",

          code:
            "INVALID_STUDY_ACTIVITY_RESPONSE",
        });
      },
    );


    it(
      "reports network failure without exposing the authentication token",
      async () => {
        mocks.fetch
          .mockRejectedValue(
            new TypeError(
              "Network unavailable",
            ),
          );

        const requestPromise =
          getActiveStudyActivity();

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          name:
            "StudyActivityApiError",

          status:
            null,

          code:
            "STUDY_ACTIVITY_NETWORK_ERROR",

          message:
            "The study timer service could not be reached.",
        });

        await requestPromise.catch(
          (
            error: unknown,
          ) => {
            expect(
              String(
                error,
              ),
            ).not.toContain(
              "test-access-token",
            );
          },
        );
      },
    );
  },
);