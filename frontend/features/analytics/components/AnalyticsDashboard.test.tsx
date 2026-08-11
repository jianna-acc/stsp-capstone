// File: /frontend/features/analytics/components/AnalyticsDashboard.test.tsx
// Purpose: Tests Analytics dashboard loading, rendering,
// reporting periods, no-evidence states, and retry behavior.

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


const mocks = vi.hoisted(
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
    }: {
      data: Array<{
        metric:
          string;

        score:
          number;
      }>;
    }) => (
      <div
        data-testid="performance-chart"
      >
        {data.map(
          (
            row,
          ) => (
            <span
              key={
                row.metric
              }
            >
              {
                row.metric
              }
              :
              {
                row.score
              }
            </span>
          ),
        )}
      </div>
    ),
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
          "Algebra",

        score_percent:
          90,

        sample_size:
          10,
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
      "loads and displays overall Analytics evidence",
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
            "Algebra",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Cell Biology",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Study-duration tracking is not available yet.",
          ),
        ).toBeInTheDocument();

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
      "shows no-evidence states without fabricating performance",
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
          screen.queryByTestId(
            "performance-chart",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            "Complete a Quiz or rate Flashcards to begin building your performance chart.",
          ),
        ).toBeInTheDocument();
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