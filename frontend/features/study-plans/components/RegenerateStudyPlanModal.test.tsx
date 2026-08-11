// File: /frontend/features/study-plans/components/RegenerateStudyPlanModal.test.tsx
// Purpose: Tests generated study-plan regeneration confirmation,
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
  StudyPlan,
  StudyPlanGenerationResponse,
} from "../types";
import {
  RegenerateStudyPlanModal,
} from "./RegenerateStudyPlanModal";


const apiMocks =
  vi.hoisted(
    () => ({
      regenerateStudyPlan:
        vi.fn(),
    }),
  );


vi.mock(
  "../api",
  () =>
    apiMocks,
);


const PLAN: StudyPlan = {
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
};


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


const REGENERATED_RESULT:
  StudyPlanGenerationResponse =
{
  plan: {
    ...PLAN,
    generated_at:
      "2026-08-11T01:00:00Z",
    updated_at:
      "2026-08-11T01:00:00Z",
  },

  sessions: [
    {
      id:
        "44444444-4444-4444-8444-444444444444",
      study_plan_id:
        PLAN.id,
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
        "2026-08-11T01:00:00Z",
      updated_at:
        "2026-08-11T01:00:00Z",
    },
  ],

  unscheduled_tasks: [],
};


function renderModal({
  tasks = TASKS,
  studyPlan = PLAN,
  onRegenerated =
    vi.fn(),
  onClose =
    vi.fn(),
}: {
  tasks?:
    SchedulableTask[];
  studyPlan?:
    StudyPlan | null;
  onRegenerated?: (
    result:
      StudyPlanGenerationResponse,
  ) => void;
  onClose?: () => void;
} = {}) {
  render(
    <MantineProvider>
      <RegenerateStudyPlanModal
        opened
        tasks={
          tasks
        }
        studyPlan={
          studyPlan
        }
        onRegenerated={
          onRegenerated
        }
        onClose={
          onClose
        }
      />
    </MantineProvider>,
  );

  return {
    onRegenerated,
    onClose,
  };
}


describe(
  "RegenerateStudyPlanModal",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();
      },
    );


    it(
      "disables regeneration when no tasks are available",
      () => {
        renderModal({
          tasks: [],
        });

        expect(
          screen.getByText(
            /no schedulable academic tasks are available/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                /regenerate plan/i,
            },
          ),
        ).toBeDisabled();
      },
    );


    it(
      "regenerates the selected generated plan",
      async () => {
        apiMocks
          .regenerateStudyPlan
          .mockResolvedValue(
            REGENERATED_RESULT,
          );

        const {
          onRegenerated,
        } =
          renderModal();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /regenerate plan/i,
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              apiMocks
                .regenerateStudyPlan,
            ).toHaveBeenCalledWith(
              PLAN.id,
              {
                tasks:
                  TASKS,
              },
            );
          },
        );

        expect(
          onRegenerated,
        ).toHaveBeenCalledWith(
          REGENERATED_RESULT,
        );

        expect(
          await screen.findByText(
            /study plan regenerated/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /manually added sessions were preserved/i,
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "shows remaining work after regeneration",
      async () => {
        apiMocks
          .regenerateStudyPlan
          .mockResolvedValue({
            ...REGENERATED_RESULT,
            unscheduled_tasks: [
              {
                task_id:
                  TASKS[0]!
                    .task_id,
                remaining_minutes:
                  90,
              },
            ],
          });

        renderModal();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /regenerate plan/i,
            },
          ),
        );

        expect(
          await screen.findByText(
            /1 task still has 90 minutes of unscheduled work/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);