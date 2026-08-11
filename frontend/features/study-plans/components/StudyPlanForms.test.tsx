// File: /frontend/features/study-plans/components/StudyPlanForms.test.tsx
// Purpose: Tests manual study-plan and study-session creation forms.

import {
  MantineProvider,
} from "@mantine/core";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
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

import {
  createStudyPlan,
  createStudySession,
} from "../api";
import type {
  StudyPlan,
  StudySession,
} from "../types";

import {
  CreateStudyPlanModal,
} from "./CreateStudyPlanModal";
import {
  CreateStudySessionModal,
} from "./CreateStudySessionModal";


vi.mock(
  "../api",
  () => ({
    createStudyPlan:
      vi.fn(),
    createStudySession:
      vi.fn(),
    deleteStudyPlan:
      vi.fn(),
    deleteStudySession:
      vi.fn(),
    listStudyPlans:
      vi.fn(),
    listStudySessions:
      vi.fn(),
  }),
);


const createStudyPlanMock =
  vi.mocked(
    createStudyPlan,
  );

const createStudySessionMock =
  vi.mocked(
    createStudySession,
  );


const SUBJECTS: SubjectSummary[] =
  [
    {
      id:
        "biology",
      name:
        "Biology",
      color:
        "#7950f2",
      created_at:
        "2026-08-01T08:00:00Z",
      updated_at:
        "2026-08-01T08:00:00Z",
    },
  ];


const PLAN: StudyPlan = {
  id:
    "plan-1",
  title:
    "Finals Plan",
  starts_on:
    "2026-08-10",
  ends_on:
    "2026-08-16",
  status:
    "draft",
  generation_mode:
    "manual",
  generated_at:
    null,
  created_at:
    "2026-08-10T00:00:00Z",
  updated_at:
    "2026-08-10T00:00:00Z",
};


const SESSION: StudySession = {
  id:
    "session-1",
  study_plan_id:
    "plan-1",
  subject_id:
    "biology",
  title:
    "Review cells",
  starts_at:
    "2026-08-11T01:00:00.000Z",
  ends_at:
    "2026-08-11T02:00:00.000Z",
  status:
    "planned",
  origin:
    "manual",
  notes:
    "Chapter 2",
  created_at:
    "2026-08-10T00:00:00Z",
  updated_at:
    "2026-08-10T00:00:00Z",
};


function renderWithMantine(
  component: React.ReactNode,
) {
  return render(
    <MantineProvider>
      {component}
    </MantineProvider>,
  );
}


describe(
  "Study plan forms",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();
      },
    );


    it(
      "creates a manual study plan",
      async () => {
        createStudyPlanMock
          .mockResolvedValue(
            PLAN,
          );

        const onCreated =
          vi.fn();

        renderWithMantine(
          <CreateStudyPlanModal
            opened
            onClose={
              vi.fn()
            }
            onCreated={
              onCreated
            }
          />,
        );

        fireEvent.change(
          screen.getByLabelText(
            /Plan title/i,
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
            /Start date/i,
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
            /End date/i,
          ),
          {
            target: {
              value:
                "2026-08-16",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Create plan",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              createStudyPlanMock,
            ).toHaveBeenCalledWith({
              title:
                "Finals Plan",
              starts_on:
                "2026-08-10",
              ends_on:
                "2026-08-16",
            });
          },
        );

        expect(
          onCreated,
        ).toHaveBeenCalledWith(
          PLAN,
        );
      },
    );


    it(
      "rejects a study plan with an invalid date range",
      async () => {
        renderWithMantine(
          <CreateStudyPlanModal
            opened
            onClose={
              vi.fn()
            }
            onCreated={
              vi.fn()
            }
          />,
        );

        fireEvent.change(
          screen.getByLabelText(
            /Plan title/i,
          ),
          {
            target: {
              value:
                "Invalid plan",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /Start date/i,
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
            /End date/i,
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
                "Create plan",
            },
          ),
        );

        expect(
          await screen.findByText(
            "The end date cannot be earlier than the start date.",
          ),
        ).toBeInTheDocument();

        expect(
          createStudyPlanMock,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      "creates a manual study session",
      async () => {
        createStudySessionMock
          .mockResolvedValue(
            SESSION,
          );

        const onCreated =
          vi.fn();

        renderWithMantine(
          <CreateStudySessionModal
            opened
            onClose={
              vi.fn()
            }
            studyPlan={
              PLAN
            }
            subjects={
              SUBJECTS
            }
            onCreated={
              onCreated
            }
          />,
        );

        fireEvent.change(
          screen.getByLabelText(
            /Session title/i,
          ),
          {
            target: {
              value:
                "Review cells",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /Starts/i,
          ),
          {
            target: {
              value:
                "2026-08-11T09:00",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /Ends/i,
          ),
          {
            target: {
              value:
                "2026-08-11T10:00",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /Notes/i,
          ),
          {
            target: {
              value:
                "Chapter 2",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Add session",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              createStudySessionMock,
            ).toHaveBeenCalledWith(
              "plan-1",
              {
                subject_id:
                  "biology",
                title:
                  "Review cells",
                starts_at:
                  new Date(
                    "2026-08-11T09:00",
                  ).toISOString(),
                ends_at:
                  new Date(
                    "2026-08-11T10:00",
                  ).toISOString(),
                notes:
                  "Chapter 2",
              },
            );
          },
        );

        expect(
          onCreated,
        ).toHaveBeenCalledWith(
          SESSION,
        );
      },
    );
  },
);