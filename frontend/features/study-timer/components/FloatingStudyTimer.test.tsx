// File: /frontend/features/study-timer/components/FloatingStudyTimer.test.tsx
// Purpose: Tests persistent Study Activity timer rendering,
// state-specific controls, and user lifecycle interactions.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";


const timerMocks =
  vi.hoisted(
    () => ({
      activity:
        null as
          | Record<
              string,
              unknown
            >
          | null,

      initializing:
        false,

      pendingAction:
        null as
          | string
          | null,

      error:
        null as
          | string
          | null,

      refreshActive:
        vi.fn(),

      pause:
        vi.fn(),

      resume:
        vi.fn(),

      startBreak:
        vi.fn(),

      endBreak:
        vi.fn(),

      endSession:
        vi.fn(),

      clearError:
        vi.fn(),
    }),
  );


vi.mock(
  "./StudyTimerProvider",
  () => ({
    useStudyTimer:
      () =>
        timerMocks,
  }),
);


import {
  FloatingStudyTimer,
} from "./FloatingStudyTimer";


function createActivity(
  overrides:
    Record<
      string,
      unknown
    > = {},
) {
  const now =
    new Date(
      Date.now(),
    ).toISOString();

  return {
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
      now,

    ended_at:
      null,

    segment_started_at:
      now,

    focus_seconds:
      1500,

    break_seconds:
      300,

    created_at:
      now,

    updated_at:
      now,

    ...overrides,
  };
}


function renderTimer() {
  return render(
    <MantineProvider>
      <FloatingStudyTimer />
    </MantineProvider>,
  );
}


describe(
  "FloatingStudyTimer",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();

        timerMocks.activity =
          null;

        timerMocks.initializing =
          false;

        timerMocks.pendingAction =
          null;

        timerMocks.error =
          null;

        timerMocks.refreshActive
          .mockResolvedValue(
            undefined,
          );

        timerMocks.pause
          .mockResolvedValue(
            undefined,
          );

        timerMocks.resume
          .mockResolvedValue(
            undefined,
          );

        timerMocks.startBreak
          .mockResolvedValue(
            undefined,
          );

        timerMocks.endBreak
          .mockResolvedValue(
            undefined,
          );

        timerMocks.endSession
          .mockResolvedValue(
            undefined,
          );
      },
    );


    it(
      "renders nothing when no timer or timer error exists",
      () => {
        renderTimer();

        expect(
          screen.queryByLabelText(
            "Active study timer",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Study timer unavailable",
          ),
        ).not.toBeInTheDocument();
      },
    );


    it(
      "renders the active focus timer and its controls",
      () => {
        timerMocks.activity =
          createActivity();

        renderTimer();

        expect(
          screen.getByLabelText(
            "Active study timer",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Biology review",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "FOCUS",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "00:25:00",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Pause",
            },
          ),
        ).toBeEnabled();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Break",
            },
          ),
        ).toBeEnabled();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "End session",
            },
          ),
        ).toBeEnabled();
      },
    );


    it(
      "renders paused state and resumes the timer",
      async () => {
        const user =
          userEvent.setup();

        timerMocks.activity =
          createActivity({
            status:
              "paused",

            mode:
              "focus",

            segment_started_at:
              null,

            focus_seconds:
              1500,
          });

        renderTimer();

        expect(
          screen.getByText(
            "PAUSED",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "00:25:00",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Pause",
            },
          ),
        ).not.toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Resume",
            },
          ),
        );

        expect(
          timerMocks.resume,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );


    it(
      "renders break state and ends the break",
      async () => {
        const user =
          userEvent.setup();

        timerMocks.activity =
          createActivity({
            mode:
              "break",

            focus_seconds:
              1500,
          });

        renderTimer();

        expect(
          screen.getByText(
            "BREAK",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Focus accumulated:/i,
          ),
        ).toHaveTextContent(
          "00:25:00",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "End break",
            },
          ),
        );

        expect(
          timerMocks.endBreak,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );


    it(
      "invokes focus lifecycle controls",
      async () => {
        const user =
          userEvent.setup();

        timerMocks.activity =
          createActivity();

        renderTimer();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Pause",
            },
          ),
        );

        expect(
          timerMocks.pause,
        ).toHaveBeenCalledTimes(
          1,
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Break",
            },
          ),
        );

        expect(
          timerMocks.startBreak,
        ).toHaveBeenCalledTimes(
          1,
        );

        await user.click(
        screen.getByRole(
            "button",
            {
            name:
                "End session",
            },
        ),
        );

        expect(
        timerMocks.endSession,
        ).not.toHaveBeenCalled();

        const dialog =
        await screen.findByRole(
            "dialog",
        );

        expect(
        within(
            dialog,
        ).getByText(
            /included in Analytics/i,
        ),
        ).toBeInTheDocument();

        await user.click(
        within(
            dialog,
        ).getByRole(
            "button",
            {
            name:
                "End session",
            },
        ),
        );

        await waitFor(
        () => {
            expect(
            timerMocks.endSession,
            ).toHaveBeenCalledTimes(
            1,
            );
        },
        );
      },
    );


    it(
      "shows recoverable loading errors with retry and dismiss actions",
      async () => {
        const user =
          userEvent.setup();

        timerMocks.error =
          "Your active study timer could not be loaded.";

        renderTimer();

        expect(
          screen.getByText(
            "Study timer unavailable",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Your active study timer could not be loaded.",
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
          timerMocks.refreshActive,
        ).toHaveBeenCalledTimes(
          1,
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Dismiss",
            },
          ),
        );

        expect(
          timerMocks.clearError,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
  },
);