// File: /frontend/features/study-plans/components/GenerateStudyPlanModal.test.tsx
// Purpose: Tests study-plan generation form validation,
// API submission, and unscheduled-work feedback.

import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  MantineProvider,
} from "@mantine/core";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  SchedulableTask,
  StudyPlanGenerationResponse,
} from "../types";
import {
  GenerateStudyPlanModal,
} from "./GenerateStudyPlanModal";


const apiMocks =
  vi.hoisted(
    () => ({
      generateStudyPlan:
        vi.fn(),
    }),
  );


vi.mock(
  "../api",
  () =>
    apiMocks,
);


const TASKS:
  SchedulableTask[] =
  [
    {
      task_id:
        "11111111-1111-4111-8111-111111111111",
      subject_id:
        "22222222-2222-4222-8222-222222222222",
      title:
        "Study for Biology exam",
      deadline:
        "2026-08-20T18:00:00+08:00",
      estimated_minutes:
        180,
      priority_weight:
        5,
    },
  ];


const GENERATED_RESULT:
  StudyPlanGenerationResponse =
  {
    plan: {
      id:
        "33333333-3333-4333-8333-333333333333",
      title:
        "Finals Plan",
      starts_on:
        "2026-08-10",
      ends_on:
        "2026-08-20",
      status:
        "active",
      generation_mode:
        "generated",
      generated_at:
        "2026-08-10T14:00:00Z",
      created_at:
        "2026-08-10T14:00:00Z",
      updated_at:
        "2026-08-10T14:00:00Z",
    },

    sessions: [
      {
        id:
          "44444444-4444-4444-8444-444444444444",
        study_plan_id:
          "33333333-3333-4333-8333-333333333333",
        subject_id:
          "22222222-2222-4222-8222-222222222222",
        title:
          "Study for Biology exam",
        starts_at:
          "2026-08-11T10:00:00Z",
        ends_at:
          "2026-08-11T11:00:00Z",
        status:
          "planned",
        origin:
          "generated",
        notes:
          null,
        created_at:
          "2026-08-10T14:00:00Z",
        updated_at:
          "2026-08-10T14:00:00Z",
      },
    ],

    unscheduled_tasks:
      [],
  };


function renderModal({
  tasks = TASKS,
  onGenerated =
    vi.fn(),
  onClose =
    vi.fn(),
}: {
  tasks?:
    SchedulableTask[];
  onGenerated?: (
    result:
      StudyPlanGenerationResponse,
  ) => void;
  onClose?: () => void;
} = {}) {
  render(
    <MantineProvider>
      <GenerateStudyPlanModal
        opened
        tasks={
          tasks
        }
        onGenerated={
          onGenerated
        }
        onClose={
          onClose
        }
      />
    </MantineProvider>,
  );

  return {
    onGenerated,
    onClose,
  };
}


function fillValidForm(): void {
  fireEvent.change(
    screen.getByLabelText(
      /plan title/i,
    ),
    {
      target: {
        value:
          "Finals Plan",
      },
    },
  );

  fireEvent.change(
    screen.getByLabelText(
      /start date/i,
    ),
    {
      target: {
        value:
          "2026-08-10",
      },
    },
  );

  fireEvent.change(
    screen.getByLabelText(
      /end date/i,
    ),
    {
      target: {
        value:
          "2026-08-20",
      },
    },
  );
}


describe(
  "GenerateStudyPlanModal",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });


    it(
      "disables generation when no tasks are available",
      () => {
        renderModal({
          tasks:
            [],
        });

        expect(
          screen.getByText(
            /no schedulable tasks are available/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                /generate plan/i,
            },
          ),
        ).toBeDisabled();
      },
    );


    it(
      "rejects an invalid plan date range",
      async () => {
        renderModal();

        fireEvent.change(
          screen.getByLabelText(
            /plan title/i,
          ),
          {
            target: {
              value:
                "Invalid Plan",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /start date/i,
          ),
          {
            target: {
              value:
                "2026-08-20",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /end date/i,
          ),
          {
            target: {
              value:
                "2026-08-10",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /generate plan/i,
            },
          ),
        );

        expect(
          await screen.findByText(
            /end date cannot be before start date/i,
          ),
        ).toBeInTheDocument();

        expect(
          apiMocks
            .generateStudyPlan,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      "generates a study plan from schedulable tasks",
      async () => {
        apiMocks
          .generateStudyPlan
          .mockResolvedValue(
            GENERATED_RESULT,
          );

        const {
          onGenerated,
        } =
          renderModal();

        fillValidForm();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /generate plan/i,
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              apiMocks
                .generateStudyPlan,
            ).toHaveBeenCalledWith({
              title:
                "Finals Plan",
              starts_on:
                "2026-08-10",
              ends_on:
                "2026-08-20",
              tasks:
                TASKS,
            });
          },
        );

        expect(
          onGenerated,
        ).toHaveBeenCalledWith(
          GENERATED_RESULT,
        );

        expect(
          await screen.findByText(
            /1 study session was generated/i,
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "shows remaining work that could not be scheduled",
      async () => {
        apiMocks
          .generateStudyPlan
          .mockResolvedValue({
            ...GENERATED_RESULT,
            unscheduled_tasks:
              [
                {
                  task_id:
                    TASKS[0]!
                      .task_id,
                  remaining_minutes:
                    75,
                },
              ],
          });

        renderModal();

        fillValidForm();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /generate plan/i,
            },
          ),
        );

        expect(
          await screen.findByText(
            /1 task still has 75 minutes of unscheduled work/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);