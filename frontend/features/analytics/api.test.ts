// File: /frontend/features/analytics/api.test.ts
// Purpose: Tests authenticated Analytics overview requests,
// period handling, response validation, and safe API errors.

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  AnalyticsPeriod,
} from "./types";


const mocks = vi.hoisted(
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
  getAnalyticsOverview,
} from "./api";


const ANALYTICS_OVERVIEW_RESPONSE = {
  period:
    "all_time",

  data_state:
    "partial",

  subject_count: {
    availability:
      "available",

    value:
      4,

    scope:
      "current_inventory",

    message:
      null,
  },

  study_material_count: {
    availability:
      "available",

    value:
      10,

    scope:
      "current_inventory",

    message:
      null,
  },

  ready_study_material_count: {
    availability:
      "available",

    value:
      8,

    scope:
      "current_inventory",

    message:
      null,
  },

  quiz_accuracy_percent: {
    availability:
      "available",

    value:
      82.5,

    sample_size:
      40,

    message:
      null,
  },

  flashcard_performance_percent: {
    availability:
      "available",

    value:
      75,

    sample_size:
      20,

    message:
      null,
  },

  study_minutes: {
    availability:
      "unavailable",

    value:
      null,

    sample_size:
      0,

    message:
      "No canonical general study-activity duration source is available yet.",
  },

  strong_topics: [
    {
      topic:
        "Algebra",

      score_percent:
        90,

      sample_size:
        10,
    },

    {
      topic:
        "Networking",

      score_percent:
        80,

      sample_size:
        5,
    },
  ],

  weak_topics: [
    {
      topic:
        "Cell Biology",

      score_percent:
        55,

      sample_size:
        8,
    },
  ],
} as const;


function createJsonResponse(
  payload:
    unknown,
  status =
    200,
): Response {
  return {
    ok:
      status >= 200 &&
      status < 300,

    status,

    json:
      vi
        .fn()
        .mockResolvedValue(
          payload,
        ),
  } as unknown as Response;
}


describe(
  "Analytics API",
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
      "rejects Analytics loading without an authenticated session",
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
          getAnalyticsOverview(
            "all_time",
          ),
        ).rejects.toMatchObject({
          name:
            "AnalyticsApiError",

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
      "loads the authenticated all-time Analytics overview",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ANALYTICS_OVERVIEW_RESPONSE,
            ),
          );

        const controller =
          new AbortController();

        const result =
          await getAnalyticsOverview(
            "all_time",
            {
              signal:
                controller.signal,
            },
          );

        expect(
          result,
        ).toEqual(
          ANALYTICS_OVERVIEW_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] =
          mocks.fetch
            .mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/analytics/overview?period=all_time",
        );

        expect(
          requestOptions.method,
        ).toBe(
          "GET",
        );

        expect(
          requestOptions.cache,
        ).toBe(
          "no-store",
        );

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
      "uses all time when no Analytics period is supplied",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ANALYTICS_OVERVIEW_RESPONSE,
            ),
          );

        await getAnalyticsOverview();

        const [
          requestUrl,
        ] =
          mocks.fetch
            .mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/analytics/overview?period=all_time",
        );
      },
    );


    it(
      "loads the last 7 days Analytics period",
      async () => {
        const response = {
          ...ANALYTICS_OVERVIEW_RESPONSE,

          period:
            "last_7_days",
        } as const;

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              response,
            ),
          );

        const result =
          await getAnalyticsOverview(
            "last_7_days",
          );

        expect(
          result.period,
        ).toBe(
          "last_7_days",
        );

        const [
          requestUrl,
        ] =
          mocks.fetch
            .mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/analytics/overview?period=last_7_days",
        );
      },
    );


    it(
      "loads the last 30 days Analytics period",
      async () => {
        const response = {
          ...ANALYTICS_OVERVIEW_RESPONSE,

          period:
            "last_30_days",
        } as const;

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              response,
            ),
          );

        const result =
          await getAnalyticsOverview(
            "last_30_days",
          );

        expect(
          result.period,
        ).toBe(
          "last_30_days",
        );

        const [
          requestUrl,
        ] =
          mocks.fetch
            .mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/analytics/overview?period=last_30_days",
        );
      },
    );


    it(
      "supports an API base URL already ending in api",
      async () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          "http://127.0.0.1:8000/api";

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              ANALYTICS_OVERVIEW_RESPONSE,
            ),
          );

        await getAnalyticsOverview(
          "all_time",
        );

        const [
          requestUrl,
        ] =
          mocks.fetch
            .mock
            .calls[0] as [
              string,
              RequestInit,
            ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/analytics/overview?period=all_time",
        );
      },
    );


    it(
      "accepts available metrics with no evidence yet",
      async () => {
        const response = {
          ...ANALYTICS_OVERVIEW_RESPONSE,

          quiz_accuracy_percent: {
            availability:
              "available",

            value:
              null,

            sample_size:
              0,

            message:
              "No completed Quiz attempts are available for the selected period.",
          },

          flashcard_performance_percent: {
            availability:
              "available",

            value:
              null,

            sample_size:
              0,

            message:
              "No Flashcard review events are available for the selected period.",
          },

          strong_topics:
            [],

          weak_topics:
            [],
        } as const;

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              response,
            ),
          );

        const result =
          await getAnalyticsOverview(
            "all_time",
          );

        expect(
          result.quiz_accuracy_percent
            .availability,
        ).toBe(
          "available",
        );

        expect(
          result.quiz_accuracy_percent
            .value,
        ).toBeNull();

        expect(
          result.flashcard_performance_percent
            .value,
        ).toBeNull();

        expect(
          result.strong_topics,
        ).toEqual(
          [],
        );

        expect(
          result.weak_topics,
        ).toEqual(
          [],
        );
      },
    );


    it(
      "rejects an invalid Analytics period before making a request",
      async () => {
        await expect(
          getAnalyticsOverview(
            "last_year" as AnalyticsPeriod,
          ),
        ).rejects.toMatchObject({
          status:
            400,

          code:
            "ANALYTICS_PERIOD_INVALID",

          message:
            "The selected Analytics period is invalid.",
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
      "rejects malformed successful Analytics responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              period:
                "all_time",

              data_state:
                "partial",

              subject_count: {
                availability:
                  "available",

                value:
                  4,
              },
            }),
          );

        await expect(
          getAnalyticsOverview(
            "all_time",
          ),
        ).rejects.toMatchObject({
          status:
            502,

          code:
            "INVALID_ANALYTICS_RESPONSE",
        });
      },
    );


    it(
      "rejects invalid Analytics topic percentages",
      async () => {
        const response = {
          ...ANALYTICS_OVERVIEW_RESPONSE,

          strong_topics: [
            {
              topic:
                "Invalid Topic",

              score_percent:
                120,

              sample_size:
                3,
            },
          ],
        };

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              response,
            ),
          );

        await expect(
          getAnalyticsOverview(
            "all_time",
          ),
        ).rejects.toMatchObject({
          status:
            502,

          code:
            "INVALID_ANALYTICS_RESPONSE",
        });
      },
    );


    it(
      "rejects Analytics topics with zero sample size",
      async () => {
        const response = {
          ...ANALYTICS_OVERVIEW_RESPONSE,

          weak_topics: [
            {
              topic:
                "Biology",

              score_percent:
                50,

              sample_size:
                0,
            },
          ],
        };

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              response,
            ),
          );

        await expect(
          getAnalyticsOverview(
            "all_time",
          ),
        ).rejects.toMatchObject({
          status:
            502,

          code:
            "INVALID_ANALYTICS_RESPONSE",
        });
      },
    );


    it(
      "maps a controlled Analytics storage error",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                detail:
                  "Analytics data is temporarily unavailable.",
              },
              503,
            ),
          );

        await expect(
          getAnalyticsOverview(
            "all_time",
          ),
        ).rejects.toMatchObject({
          status:
            503,

          message:
            "Analytics data is temporarily unavailable.",
        });
      },
    );


    it(
      "maps a validation error for an unsupported backend period",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                detail:
                  "Invalid reporting period.",
              },
              422,
            ),
          );

        await expect(
          getAnalyticsOverview(
            "all_time",
          ),
        ).rejects.toMatchObject({
          status:
            422,

          message:
            "Invalid reporting period.",
        });
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
          getAnalyticsOverview(
            "all_time",
          );

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status:
            null,

          code:
            "ANALYTICS_API_UNREACHABLE",

          message:
            "Analytics could not connect to the backend.",
        });

        await requestPromise.catch(
          (
            error:
              unknown,
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