// File: /frontend/features/study-timer/components/StudyTimerProvider.test.tsx
// Purpose: Tests durable shared Study Activity timer state,
// persisted recovery, scheduled starts, and lifecycle transitions.

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
  StudyActivity,
} from "../types";


const apiMocks =
  vi.hoisted(
    () => ({
      getActiveStudyActivity:
        vi.fn(),

      startStudyActivity:
        vi.fn(),

      pauseStudyActivity:
        vi.fn(),

      resumeStudyActivity:
        vi.fn(),

      startStudyActivityBreak:
        vi.fn(),

      endStudyActivityBreak:
        vi.fn(),

      endStudyActivity:
        vi.fn(),
    }),
  );


vi.mock(
  "../api",
  () =>
    apiMocks,
);


import {
  StudyTimerProvider,
  useStudyTimer,
} from "./StudyTimerProvider";


const RUNNING_ACTIVITY:
  StudyActivity = {
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
  };


const PAUSED_ACTIVITY:
  StudyActivity = {
    ...RUNNING_ACTIVITY,

    status:
      "paused",

    mode:
      "focus",

    segment_started_at:
      null,

    focus_seconds:
      1500,
  };


const BREAK_ACTIVITY:
  StudyActivity = {
    ...RUNNING_ACTIVITY,

    mode:
      "break",

    segment_started_at:
      "2026-08-12T08:30:00Z",

    focus_seconds:
      1500,

    break_seconds:
      300,
  };


const COMPLETED_ACTIVITY:
  StudyActivity = {
    ...RUNNING_ACTIVITY,

    status:
      "completed",

    mode:
      "focus",

    ended_at:
      "2026-08-12T09:00:00Z",

    segment_started_at:
      null,

    focus_seconds:
      3000,

    break_seconds:
      600,
  };


function TimerHarness() {
  const {
    activity,
    initializing,
    pendingAction,
    startFromStudySession,
    pause,
    resume,
    startBreak,
    endBreak,
    endSession,
  } =
    useStudyTimer();

  return (
    <div>
      <div
        data-testid="initializing"
      >
        {
          String(
            initializing,
          )
        }
      </div>

      <div
        data-testid="status"
      >
        {
          activity?.status ??
          "none"
        }
      </div>

      <div
        data-testid="mode"
      >
        {
          activity?.mode ??
          "none"
        }
      </div>

      <div
        data-testid="activity-id"
      >
        {
          activity?.id ??
          "none"
        }
      </div>

      <div
        data-testid="pending-action"
      >
        {
          pendingAction ??
          "none"
        }
      </div>

      <button
        type="button"
        onClick={() => {
          void startFromStudySession(
            "session-id",
          );
        }}
      >
        Start scheduled
      </button>

      <button
        type="button"
        onClick={() => {
          void pause();
        }}
      >
        Pause
      </button>

      <button
        type="button"
        onClick={() => {
          void resume();
        }}
      >
        Resume
      </button>

      <button
        type="button"
        onClick={() => {
          void startBreak();
        }}
      >
        Start break
      </button>

      <button
        type="button"
        onClick={() => {
          void endBreak();
        }}
      >
        End break
      </button>

      <button
        type="button"
        onClick={() => {
          void endSession();
        }}
      >
        End session
      </button>
    </div>
  );
}


function renderProvider() {
  return render(
    <StudyTimerProvider>
      <TimerHarness />
    </StudyTimerProvider>,
  );
}


describe(
  "StudyTimerProvider",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();

        apiMocks
          .getActiveStudyActivity
          .mockResolvedValue(
            null,
          );

        apiMocks
          .startStudyActivity
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        apiMocks
          .pauseStudyActivity
          .mockResolvedValue(
            PAUSED_ACTIVITY,
          );

        apiMocks
          .resumeStudyActivity
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        apiMocks
          .startStudyActivityBreak
          .mockResolvedValue(
            BREAK_ACTIVITY,
          );

        apiMocks
          .endStudyActivityBreak
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        apiMocks
          .endStudyActivity
          .mockResolvedValue(
            COMPLETED_ACTIVITY,
          );
      },
    );


    it(
      "recovers an existing persisted timer when mounted",
      async () => {
        apiMocks
          .getActiveStudyActivity
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        renderProvider();

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "running",
            );
          },
        );

        expect(
          screen.getByTestId(
            "mode",
          ),
        ).toHaveTextContent(
          "focus",
        );

        expect(
          screen.getByTestId(
            "activity-id",
          ),
        ).toHaveTextContent(
          "activity-id",
        );

        expect(
          apiMocks
            .getActiveStudyActivity,
        ).toHaveBeenCalledWith({
          signal:
            expect.any(
              AbortSignal,
            ),
        });
      },
    );


    it(
      "finishes initialization with no timer when none is active",
      async () => {
        renderProvider();

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "initializing",
              ),
            ).toHaveTextContent(
              "false",
            );
          },
        );

        expect(
          screen.getByTestId(
            "status",
          ),
        ).toHaveTextContent(
          "none",
        );
      },
    );


    it(
      "starts a scheduled Study Plan session",
      async () => {
        const user =
          userEvent.setup();

        renderProvider();

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "initializing",
              ),
            ).toHaveTextContent(
              "false",
            );
          },
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Start scheduled",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "running",
            );
          },
        );

        expect(
          apiMocks
            .startStudyActivity,
        ).toHaveBeenCalledWith({
          study_session_id:
            "session-id",
        });
      },
    );


    it(
      "updates shared state across pause and resume",
      async () => {
        const user =
          userEvent.setup();

        apiMocks
          .getActiveStudyActivity
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        renderProvider();

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "running",
            );
          },
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Pause",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "paused",
            );
          },
        );

        expect(
          apiMocks
            .pauseStudyActivity,
        ).toHaveBeenCalledWith(
          "activity-id",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Resume",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "running",
            );
          },
        );

        expect(
          apiMocks
            .resumeStudyActivity,
        ).toHaveBeenCalledWith(
          "activity-id",
        );
      },
    );


    it(
      "updates shared state across break start and end",
      async () => {
        const user =
          userEvent.setup();

        apiMocks
          .getActiveStudyActivity
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        renderProvider();

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "running",
            );
          },
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Start break",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "mode",
              ),
            ).toHaveTextContent(
              "break",
            );
          },
        );

        expect(
          apiMocks
            .startStudyActivityBreak,
        ).toHaveBeenCalledWith(
          "activity-id",
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

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "mode",
              ),
            ).toHaveTextContent(
              "focus",
            );
          },
        );

        expect(
          apiMocks
            .endStudyActivityBreak,
        ).toHaveBeenCalledWith(
          "activity-id",
        );
      },
    );


    it(
      "clears the active timer after completion",
      async () => {
        const user =
          userEvent.setup();

        apiMocks
          .getActiveStudyActivity
          .mockResolvedValue(
            RUNNING_ACTIVITY,
          );

        renderProvider();

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "running",
            );
          },
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

        await waitFor(
          () => {
            expect(
              screen.getByTestId(
                "status",
              ),
            ).toHaveTextContent(
              "none",
            );
          },
        );

        expect(
          apiMocks
            .endStudyActivity,
        ).toHaveBeenCalledWith(
          "activity-id",
        );
      },
    );
  },
);