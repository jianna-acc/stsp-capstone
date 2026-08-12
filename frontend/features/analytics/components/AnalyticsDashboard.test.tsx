// File: /frontend/features/analytics/components/AnalyticsDashboard.test.tsx
// Purpose: Tests compact Analytics rendering, weekly Study Time,
// expandable topics, reporting periods, empty states, and retry behavior.

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
  AnalyticsOverviewResponse,
  AnalyticsPeriod,
} from "@/features/analytics/types";


const mocks =
  vi.hoisted(
    () => ({
      getAnalyticsOverview:
        vi.fn(),
    }),
  );


vi.mock(
  "@mantine/charts",
  () => ({
    BarChart: ({
      data,
      dataKey,
      series,
    }: {
      data:
        Array<
          Record<
            string,
            unknown
          >
        >;

      dataKey:
        string;

      series:
        Array<{
          name:
            string;
        }>;
    }) => {
      const testId =
        dataKey ===
          "week"
          ? "weekly-study-chart"
          : "performance-chart";

      const seriesName =
        series[0]
          ?.name ??
        "";

      return (
        <div
          data-testid={
            testId
          }
        >
          {data.map(
            (
              row,
            ) => (
              <span
                key={
                  String(
                    row[
                      dataKey
                    ],
                  )
                }
              >
                {
                  String(
                    row[
                      dataKey
                    ],
                  )
                }
                :
                {
                  String(
                    row[
                      seriesName
                    ],
                  )
                }
              </span>
            ),
          )}
        </div>
      );
    },
  }),
);


vi.mock(
  "@/features/analytics/api",
  async (
    importOriginal,
  ) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/features/analytics/api"
        )
      >();

    return {
      ...actual,

      getAnalyticsOverview:
        mocks.getAnalyticsOverview,
    };
  },
);


import {
  AnalyticsApiError,
} from "@/features/analytics/api";

import {
  AnalyticsDashboard,
} from "./AnalyticsDashboard";


const OVERVIEW:
  AnalyticsOverviewResponse = {
    period:
      "all_time",

    data_state:
      "ready",

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
        "available",

      value:
        95,

      sample_size:
        3,

      message:
        null,
    },

    study_time_by_week: [
      {
        week_start:
          "2026-08-03",

        week_end:
          "2026-08-09",

        study_minutes:
          30,

        session_count:
          1,
      },

      {
        week_start:
          "2026-08-10",

        week_end:
          "2026-08-16",

        study_minutes:
          65,

        session_count:
          2,
      },
    ],

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
          85,

        sample_size:
          5,
      },

      {
        topic:
          "Databases",

        score_percent:
          80,

        sample_size:
          4,
      },

      {
        topic:
          "Operating Systems",

        score_percent:
          78,

        sample_size:
          3,
      },

      {
        topic:
          "Security",

        score_percent:
          75,

        sample_size:
          2,
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

      {
        topic:
          "Statistics",

        score_percent:
          50,

        sample_size:
          5,
      },

      {
        topic:
          "Calculus",

        score_percent:
          45,

        sample_size:
          4,
      },

      {
        topic:
          "Physics",

        score_percent:
          40,

        sample_size:
          3,
      },
    ],
  };


function renderDashboard() {
  return render(
    <MantineProvider>
      <AnalyticsDashboard />
    </MantineProvider>,
  );
}


describe(
  "AnalyticsDashboard",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();

        mocks
          .getAnalyticsOverview
          .mockResolvedValue(
            OVERVIEW,
          );
      },
    );


    it(
      "loads compact Analytics and weekly Study Time evidence",
      async () => {
        renderDashboard();

        expect(
          screen.getByText(
            "Loading your Analytics...",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "82.5%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "75%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "95 min",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "3 completed sessions",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "All metrics ready",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByTestId(
            "weekly-study-chart",
          ),
        ).toHaveTextContent(
          "Aug 3 – Aug 9:30",
        );

        expect(
          screen.getByTestId(
            "weekly-study-chart",
          ),
        ).toHaveTextContent(
          "Aug 10 – Aug 16:65",
        );

        expect(
          screen.getByTestId(
            "performance-chart",
          ),
        ).toHaveTextContent(
          "Quiz accuracy:82.5",
        );

        expect(
          screen.getByTestId(
            "performance-chart",
          ),
        ).toHaveTextContent(
          "Flashcard recall:75",
        );

        await waitFor(
          () => {
            expect(
              mocks
                .getAnalyticsOverview,
            ).toHaveBeenCalledWith(
              "all_time",
              expect.objectContaining({
                signal:
                  expect.any(
                    AbortSignal,
                  ),
              }),
            );
          },
        );
      },
    );


    it(
      "shows only a topic preview until the user expands it",
      async () => {
        const user =
          userEvent.setup();

        renderDashboard();

        await screen.findByText(
          "Algebra",
        );

        expect(
          screen.getByText(
            "Databases",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Security",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Physics",
          ),
        ).not.toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Show all (5)",
            },
          ),
        );

        expect(
          screen.getByText(
            "Security",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Show less",
            },
          ),
        ).toHaveAttribute(
          "aria-expanded",
          "true",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Show less",
            },
          ),
        );

        expect(
          screen.queryByText(
            "Security",
          ),
        ).not.toBeInTheDocument();
      },
    );


    it(
      "reloads Analytics when the reporting period changes",
      async () => {
        const user =
          userEvent.setup();

        mocks
          .getAnalyticsOverview
          .mockImplementation(
            (
              period:
                AnalyticsPeriod,
            ) =>
              Promise.resolve({
                ...OVERVIEW,

                period,
              }),
          );

        renderDashboard();

        await screen.findByText(
          "82.5%",
        );

        await user.click(
          screen.getByText(
            "Last 30 Days",
          ),
        );

        await waitFor(
          () => {
            expect(
              mocks
                .getAnalyticsOverview,
            ).toHaveBeenCalledWith(
              "last_30_days",
              expect.objectContaining({
                signal:
                  expect.any(
                    AbortSignal,
                  ),
              }),
            );
          },
        );
      },
    );


    it(
      "shows no-evidence states without fabricating Analytics",
      async () => {
        mocks
          .getAnalyticsOverview
          .mockResolvedValue({
            ...OVERVIEW,

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

            study_minutes: {
              availability:
                "available",

              value:
                null,

              sample_size:
                0,

              message:
                "No completed study sessions are available for the selected period.",
            },

            study_time_by_week:
              [],

            strong_topics:
              [],

            weak_topics:
              [],
          });

        renderDashboard();

        expect(
          await screen.findByText(
            "No completed Quiz attempts are available for the selected period.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "No Flashcard review events are available for the selected period.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "No completed study sessions are available for the selected period.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByTestId(
            "weekly-study-chart",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            "Complete a study session to build your weekly chart.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByTestId(
            "performance-chart",
          ),
        ).not.toBeInTheDocument();
      },
    );


    it(
      "shows a safe error and retries Analytics loading",
      async () => {
        const user =
          userEvent.setup();

        mocks
          .getAnalyticsOverview
          .mockRejectedValueOnce(
            new AnalyticsApiError(
              "Analytics data is temporarily unavailable.",
              503,
            ),
          )
          .mockResolvedValueOnce(
            OVERVIEW,
          );

        renderDashboard();

        expect(
          await screen.findByText(
            "Analytics data is temporarily unavailable.",
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Retry",
            },
          ),
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
  },
);