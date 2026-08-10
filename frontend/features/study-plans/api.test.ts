// File: /frontend/features/study-plans/api.test.ts
// Purpose: Tests authenticated Track D frontend API requests,
// URL handling, response validation, and safe errors.

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
  createStudyPlan,
  deleteStudyPlan,
  generateStudyPlan,
  listStudyPlans,
  StudyPlanApiError,
} from "./api";


const PLAN_RESPONSE = {
  id: "plan-id",
  title: "Finals Plan",
  starts_on: "2026-08-10",
  ends_on: "2026-08-17",
  status: "active",
  generation_mode: "manual",
  generated_at: null,
  created_at:
    "2026-08-10T08:00:00+00:00",
  updated_at:
    "2026-08-10T08:00:00+00:00",
};


const SESSION_RESPONSE = {
  id: "session-id",
  study_plan_id: "plan-id",
  subject_id: "subject-id",
  title: "Review Chapter 4",
  starts_at:
    "2026-08-10T18:00:00+08:00",
  ends_at:
    "2026-08-10T19:00:00+08:00",
  status: "planned",
  origin: "generated",
  notes: null,
  created_at:
    "2026-08-10T08:00:00+00:00",
  updated_at:
    "2026-08-10T08:00:00+00:00",
};


describe(
  "study-plans API",
  () => {
    beforeEach(
      () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          "http://localhost:8000";

        mocks.getSession.mockResolvedValue(
          {
            data: {
              session: {
                access_token:
                  "test-access-token",
              },
            },
            error: null,
          },
        );

        mocks.createClient.mockReturnValue(
          {
            auth: {
              getSession:
                mocks.getSession,
            },
          },
        );

        mocks.fetch.mockReset();

        vi.stubGlobal(
          "fetch",
          mocks.fetch,
        );
      },
    );


    afterEach(
      () => {
        vi.unstubAllGlobals();
        vi.restoreAllMocks();

        delete process.env
          .NEXT_PUBLIC_API_BASE_URL;
      },
    );


    it(
      "creates a study plan with the bearer token",
      async () => {
        mocks.fetch.mockResolvedValue(
          new Response(
            JSON.stringify(
              PLAN_RESPONSE,
            ),
            {
              status: 201,
              headers: {
                "Content-Type":
                  "application/json",
              },
            },
          ),
        );

        const result =
          await createStudyPlan(
            {
              title: "Finals Plan",
              starts_on:
                "2026-08-10",
              ends_on:
                "2026-08-17",
            },
          );

        expect(
          result.id,
        ).toBe(
          "plan-id",
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledTimes(
          1,
        );

        const [
          url,
          init,
        ] = mocks.fetch.mock.calls[0];

        expect(
          url,
        ).toBe(
          "http://localhost:8000/api/study-plans",
        );

        expect(
          init.method,
        ).toBe(
          "POST",
        );

        const headers =
          new Headers(
            init.headers,
          );

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
      },
    );


    it(
      "supports an API base URL that already ends in api",
      async () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          "http://localhost:8000/api";

        mocks.fetch.mockResolvedValue(
          new Response(
            JSON.stringify(
              {
                items: [
                  PLAN_RESPONSE,
                ],
              },
            ),
            {
              status: 200,
              headers: {
                "Content-Type":
                  "application/json",
              },
            },
          ),
        );

        await listStudyPlans();

        expect(
          mocks.fetch.mock.calls[0][0],
        ).toBe(
          "http://localhost:8000/api/study-plans?limit=50",
        );
      },
    );


    it(
      "generates and returns a persisted plan",
      async () => {
        mocks.fetch.mockResolvedValue(
          new Response(
            JSON.stringify(
              {
                plan: {
                  ...PLAN_RESPONSE,
                  generation_mode:
                    "generated",
                  generated_at:
                    "2026-08-10T08:00:00+00:00",
                },
                sessions: [
                  SESSION_RESPONSE,
                ],
                unscheduled_tasks: [],
              },
            ),
            {
              status: 201,
              headers: {
                "Content-Type":
                  "application/json",
              },
            },
          ),
        );

        const result =
          await generateStudyPlan(
            {
              title:
                "Generated Finals Plan",
              starts_on:
                "2026-08-10",
              ends_on:
                "2026-08-17",
              tasks: [
                {
                  task_id:
                    "task-id",
                  subject_id:
                    "subject-id",
                  title:
                    "Review Chapter 4",
                  deadline:
                    "2026-08-11T12:00:00+00:00",
                  estimated_minutes:
                    60,
                  priority_weight:
                    3,
                },
              ],
            },
          );

        expect(
          result.sessions,
        ).toHaveLength(
          1,
        );

        expect(
          mocks.fetch.mock.calls[0][0],
        ).toBe(
          "http://localhost:8000/api/study-plan-generation",
        );
      },
    );


    it(
      "accepts a successful no-content delete",
      async () => {
        mocks.fetch.mockResolvedValue(
          new Response(
            null,
            {
              status: 204,
            },
          ),
        );

        await expect(
          deleteStudyPlan(
            "plan-id",
          ),
        ).resolves.toBeUndefined();

        expect(
          mocks.fetch.mock.calls[0][0],
        ).toBe(
          "http://localhost:8000/api/study-plans/plan-id",
        );
      },
    );


    it(
      "rejects requests without an authenticated session",
      async () => {
        mocks.getSession.mockResolvedValue(
          {
            data: {
              session: null,
            },
            error: null,
          },
        );

        await expect(
          listStudyPlans(),
        ).rejects.toMatchObject(
          {
            name:
              "StudyPlanApiError",
            status: 401,
            code:
              "AUTH_SESSION_REQUIRED",
          },
        );

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      "rejects malformed study-plan responses",
      async () => {
        mocks.fetch.mockResolvedValue(
          new Response(
            JSON.stringify(
              {
                id: "plan-id",
              },
            ),
            {
              status: 201,
              headers: {
                "Content-Type":
                  "application/json",
              },
            },
          ),
        );

        await expect(
          createStudyPlan(
            {
              title:
                "Finals Plan",
              starts_on:
                "2026-08-10",
              ends_on:
                "2026-08-17",
            },
          ),
        ).rejects.toBeInstanceOf(
          StudyPlanApiError,
        );
      },
    );


    it(
      "surfaces safe backend errors",
      async () => {
        mocks.fetch.mockResolvedValue(
          new Response(
            JSON.stringify(
              {
                error_code:
                  "STUDY_PLAN_VALIDATION_FAILED",
                message:
                  "The study-plan operation is invalid.",
              },
            ),
            {
              status: 400,
              headers: {
                "Content-Type":
                  "application/json",
              },
            },
          ),
        );

        await expect(
          listStudyPlans(),
        ).rejects.toMatchObject(
          {
            status: 400,
            code:
              "STUDY_PLAN_VALIDATION_FAILED",
            message:
              "The study-plan operation is invalid.",
          },
        );
      },
    );
  },
);