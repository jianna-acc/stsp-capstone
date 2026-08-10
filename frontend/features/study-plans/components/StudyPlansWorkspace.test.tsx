// File: /frontend/features/study-plans/components/StudyPlansWorkspace.test.tsx
// Purpose: Tests Track D study-plan loading, session calendar
// rendering, and saved-plan switching.

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
  SubjectSummary,
} from "@/features/subjects/types";


const apiMocks =
  vi.hoisted(
    () => ({
      listStudyPlans:
        vi.fn(),

      listStudySessions:
        vi.fn(),
    }),
  );


vi.mock(
  "../api",
  () => ({
    listStudyPlans:
      apiMocks.listStudyPlans,

    listStudySessions:
      apiMocks.listStudySessions,
  }),
);


import {
  StudyPlansWorkspace,
} from "./StudyPlansWorkspace";


const SUBJECTS = [
  {
    id: "biology-subject",
    name: "Biology",
    color: "green",
    created_at:
      "2026-08-01T08:00:00Z",
    updated_at:
      "2026-08-01T08:00:00Z",
  },
  {
    id: "history-subject",
    name: "History",
    color: "orange",
    created_at:
      "2026-08-01T08:00:00Z",
    updated_at:
      "2026-08-01T08:00:00Z",
  },
] as SubjectSummary[];


const PLANS = [
  {
    id: "finals-plan",
    title: "Finals Plan",
    starts_on: "2026-08-10",
    ends_on: "2026-08-16",
    status: "active",
    generation_mode: "manual",
    generated_at: null,
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
  {
    id: "research-plan",
    title: "Research Plan",
    starts_on: "2026-08-17",
    ends_on: "2026-08-23",
    status: "active",
    generation_mode: "generated",
    generated_at:
      "2026-08-10T08:00:00Z",
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
] as const;


const FINALS_SESSIONS = [
  {
    id: "biology-session",
    study_plan_id:
      "finals-plan",
    subject_id:
      "biology-subject",
    title:
      "Review Chapter 4",
    starts_at:
      "2026-08-10T18:00:00+08:00",
    ends_at:
      "2026-08-10T19:00:00+08:00",
    status: "planned",
    origin: "manual",
    notes: null,
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
] as const;


const RESEARCH_SESSIONS = [
  {
    id: "history-session",
    study_plan_id:
      "research-plan",
    subject_id:
      "history-subject",
    title:
      "Draft research outline",
    starts_at:
      "2026-08-17T19:00:00+08:00",
    ends_at:
      "2026-08-17T20:00:00+08:00",
    status: "planned",
    origin: "generated",
    notes: null,
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
] as const;


function renderWorkspace() {
  return render(
    <MantineProvider>
      <StudyPlansWorkspace
        initialSubjects={
          SUBJECTS
        }
      />
    </MantineProvider>,
  );
}


describe(
  "StudyPlansWorkspace",
  () => {
    beforeEach(
      () => {
        apiMocks
          .listStudyPlans
          .mockReset()
          .mockResolvedValue(
            PLANS,
          );

        apiMocks
          .listStudySessions
          .mockReset()
          .mockImplementation(
            (
              planId:
                string,
            ) => {
              if (
                planId ===
                "research-plan"
              ) {
                return Promise.resolve(
                  RESEARCH_SESSIONS,
                );
              }

              return Promise.resolve(
                FINALS_SESSIONS,
              );
            },
          );
      },
    );


    it(
      "loads saved plans and displays the selected plan sessions",
      async () => {
        renderWorkspace();

        expect(
          screen.getByLabelText(
            "Loading study plans",
          ),
        ).toBeInTheDocument();

        expect(
            await screen.findByRole(
                "heading",
                {
                name: "Finals Plan",
                level: 2,
                },
            ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Research Plan",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Review Chapter 4",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Biology",
          ),
        ).toBeInTheDocument();

        expect(
          apiMocks
            .listStudyPlans,
        ).toHaveBeenCalledWith(
          50,
          {
            signal:
              expect.any(
                AbortSignal,
              ),
          },
        );
      },
    );


    it(
      "switches plans and loads the selected schedule",
      async () => {
        const user =
          userEvent.setup();

        renderWorkspace();

        const researchPlan =
          await screen.findByRole(
            "button",
            {
              name:
                /Research Plan/i,
            },
          );

        await user.click(
          researchPlan,
        );

        expect(
          await screen.findByText(
            "Draft research outline",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "History",
          ),
        ).toBeInTheDocument();

        await waitFor(
          () => {
            expect(
              apiMocks
                .listStudySessions,
            ).toHaveBeenCalledWith(
              "research-plan",
              200,
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
      "shows the empty state when no plans exist",
      async () => {
        apiMocks
          .listStudyPlans
          .mockResolvedValue(
            [],
          );

        renderWorkspace();

        expect(
          await screen.findByText(
            "No study plans yet",
          ),
        ).toBeInTheDocument();

        expect(
          apiMocks
            .listStudySessions,
        ).not.toHaveBeenCalled();
      },
    );
  },
);