// File: /frontend/features/dashboard/components/DashboardWorkspace.test.tsx
// Purpose: Tests Dashboard command-center data loading,
// independent feature states, Analytics semantics, and navigation.

import {
  MantineProvider,
} from "@mantine/core";

import {
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  AcademicTaskPriorityResponse,
} from "@/features/academic-tasks/types";

import type {
  AnalyticsOverviewResponse,
} from "@/features/analytics/types";

import type {
  StudyPlan,
  StudySession,
} from "@/features/study-plans/types";

import type {
  SubjectSummary,
} from "@/features/subjects/types";


const mocks =
  vi.hoisted(
    () => ({
      listPrioritizedAcademicTasks:
        vi.fn(),

      listStudyPlans:
        vi.fn(),

      listStudySessions:
        vi.fn(),

      getAnalyticsOverview:
        vi.fn(),
    }),
  );


vi.mock(
  "@/features/academic-tasks/api",
  () => ({
    listPrioritizedAcademicTasks:
      mocks.listPrioritizedAcademicTasks,
  }),
);


vi.mock(
  "@/features/study-plans/api",
  () => ({
    listStudyPlans:
      mocks.listStudyPlans,

    listStudySessions:
      mocks.listStudySessions,
  }),
);


vi.mock(
  "@/features/analytics/api",
  () => ({
    getAnalyticsOverview:
      mocks.getAnalyticsOverview,
  }),
);


import {
  DashboardWorkspace,
} from "./DashboardWorkspace";


const SUBJECT:
  SubjectSummary = {
  id:
    "22222222-2222-4222-8222-222222222222",

  name:
    "GESTSOC",

  color:
    "violet",

  created_at:
    "2026-08-01T08:00:00Z",

  updated_at:
    "2026-08-01T08:00:00Z",
};


const PRIORITIZED_TASK:
  AcademicTaskPriorityResponse = {
  task: {
    id:
      "11111111-1111-4111-8111-111111111111",

    subject_id:
      SUBJECT.id,

    title:
      "STS reflection paper",

    description:
      "Write the final course reflection.",

    deadline:
      "2099-08-20T12:00:00Z",

    estimated_minutes:
      120,

    difficulty:
      "medium",

    task_type:
      "assignment",

    output_type:
      "writing",

    status:
      "pending",

    created_at:
      "2026-08-09T10:00:00Z",

    updated_at:
      "2026-08-09T10:00:00Z",
  },

  priority: {
    total_score:
      78.5,

    deadline_score:
      100,

    difficulty_score:
      60,

    estimated_time_score:
      60,

    output_confidence_score:
      75,

    previous_performance_score:
      50,

    available_study_time_score:
      80,

    status_score:
      50,
  },
};


const STUDY_PLAN:
  StudyPlan = {
  id:
    "33333333-3333-4333-8333-333333333333",

  title:
    "Semester Study Plan",

  starts_on:
    "2099-08-01",

  ends_on:
    "2099-08-31",

  status:
    "active",

  generation_mode:
    "manual",

  generated_at:
    null,

  created_at:
    "2026-08-01T08:00:00Z",

  updated_at:
    "2026-08-01T08:00:00Z",
};


const STUDY_SESSION:
  StudySession = {
  id:
    "44444444-4444-4444-8444-444444444444",

  study_plan_id:
    STUDY_PLAN.id,

  subject_id:
    SUBJECT.id,

  title:
    "Science and Technology Review",

  starts_at:
    "2099-08-12T09:00:00Z",

  ends_at:
    "2099-08-12T10:00:00Z",

  status:
    "planned",

  origin:
    "manual",

  notes:
    null,

  created_at:
    "2026-08-01T08:00:00Z",

  updated_at:
    "2026-08-01T08:00:00Z",
};


const ANALYTICS_OVERVIEW:
  AnalyticsOverviewResponse = {
  period:
    "last_7_days",

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
      4,

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
      "Study-duration tracking is not available yet.",
  },

  strong_topics: [
    {
      topic:
        "Globalization",

      score_percent:
        90,

      sample_size:
        10,
    },
  ],

  weak_topics: [
    {
      topic:
        "Climate Justice",

      score_percent:
        55,

      sample_size:
        8,
    },
  ],
};


function renderDashboard() {
  return render(
    <MantineProvider
      env="test"
    >
      <DashboardWorkspace
        displayName="Erica"
        subjects={[
          SUBJECT,
        ]}
      />
    </MantineProvider>,
  );
}


describe(
  "DashboardWorkspace",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();

        mocks
          .listPrioritizedAcademicTasks
          .mockResolvedValue([
            PRIORITIZED_TASK,
          ]);

        mocks
          .listStudyPlans
          .mockResolvedValue([
            STUDY_PLAN,
          ]);

        mocks
          .listStudySessions
          .mockResolvedValue([
            STUDY_SESSION,
          ]);

        mocks
          .getAnalyticsOverview
          .mockResolvedValue(
            ANALYTICS_OVERVIEW,
          );
      },
    );


    it(
      "loads the student command-center data from existing feature APIs",
      async () => {
        renderDashboard();

        expect(
          screen.getByText(
            "Welcome back, Erica",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Science and Technology Review",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "82.5%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "75.0%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Globalization",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "GESTSOC",
          ).length,
        ).toBeGreaterThan(
          0,
        );

        await waitFor(
          () => {
            expect(
              mocks
                .listPrioritizedAcademicTasks,
            ).toHaveBeenCalledWith({
              limit:
                5,

              signal:
                expect.any(
                  AbortSignal,
                ),
            });

            expect(
              mocks.listStudyPlans,
            ).toHaveBeenCalledWith(
              50,
              {
                signal:
                  expect.any(
                    AbortSignal,
                  ),
              },
            );

            expect(
              mocks.listStudySessions,
            ).toHaveBeenCalledWith(
              STUDY_PLAN.id,
              200,
              {
                signal:
                  expect.any(
                    AbortSignal,
                  ),
              },
            );

            expect(
              mocks
                .getAnalyticsOverview,
            ).toHaveBeenCalledWith(
              "last_7_days",
              {
                signal:
                  expect.any(
                    AbortSignal,
                  ),
              },
            );
          },
        );
      },
    );


    it(
      "shows useful empty states when there are no priority tasks or upcoming study sessions",
      async () => {
        mocks
          .listPrioritizedAcademicTasks
          .mockResolvedValue(
            [],
          );

        mocks
          .listStudyPlans
          .mockResolvedValue(
            [],
          );

        renderDashboard();

        expect(
          await screen.findByText(
            "No Academic Tasks currently need your attention.",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "You do not have an upcoming planned study session.",
          ),
        ).toBeInTheDocument();

        expect(
          mocks
            .listStudySessions,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      "shows no-evidence Analytics states without fabricating zero performance or study time",
      async () => {
        mocks
          .getAnalyticsOverview
          .mockResolvedValue({
            ...ANALYTICS_OVERVIEW,

            quiz_accuracy_percent: {
              availability:
                "available",

              value:
                null,

              sample_size:
                0,

              message:
                "No completed Quiz attempts are available.",
            },

            flashcard_performance_percent: {
              availability:
                "available",

              value:
                null,

              sample_size:
                0,

              message:
                "No Flashcard review events are available.",
            },

            strong_topics:
              [],

            weak_topics:
              [],
          });

        renderDashboard();

        await waitFor(
          () => {
            expect(
              screen.getAllByText(
                "No data yet",
              ),
            ).toHaveLength(
              2,
            );
          },
        );

        expect(
          screen.getByText(
            "Complete quizzes or flashcard reviews to build recent topic evidence.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Study-duration tracking is not available yet.",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            /Study Time/i,
          ),
        ).not.toBeInTheDocument();
      },
    );


    it(
      "keeps tasks and study-plan content available when Analytics fails",
      async () => {
        mocks
          .getAnalyticsOverview
          .mockRejectedValue(
            new Error(
              "Analytics data is temporarily unavailable.",
            ),
          );

        renderDashboard();

        expect(
          await screen.findByText(
            "STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Science and Technology Review",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Unable to load performance",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Unable to load study materials",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Analytics data is temporarily unavailable.",
          ),
        ).toHaveLength(
          2,
        );
      },
    );


    it(
      "retries the shared Analytics request after a failure",
      async () => {
        const user =
          userEvent.setup();

        mocks
          .getAnalyticsOverview
          .mockRejectedValueOnce(
            new Error(
              "Temporary Analytics failure.",
            ),
          )
          .mockResolvedValueOnce(
            ANALYTICS_OVERVIEW,
          );

        renderDashboard();

        expect(
          await screen.findByText(
            "Unable to load performance",
          ),
        ).toBeInTheDocument();

        const retryButtons =
          screen.getAllByRole(
            "button",
            {
              name:
                "Retry",
            },
          );

        await user.click(
          retryButtons[0],
        );

        expect(
          await screen.findByText(
            "82.5%",
          ),
        ).toBeInTheDocument();

        expect(
          mocks
            .getAnalyticsOverview,
        ).toHaveBeenCalledTimes(
          2,
        );
      },
    );


    it(
      "links the main Dashboard actions to the existing feature routes",
      async () => {
        renderDashboard();

        await screen.findByText(
          "STS reflection paper",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "View all tasks",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/academic-tasks",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open study plan",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/study-plan",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "View analytics",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/analytics",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Manage subjects",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/subjects",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open Academic Tasks",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/academic-tasks",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open Study Assistant",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/study-assistant",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open Flashcards",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/flashcards",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open Quizzes",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/quizzes",
        );
      },
    );
  },
);