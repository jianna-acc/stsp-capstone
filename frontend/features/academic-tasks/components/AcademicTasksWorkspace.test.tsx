// File: /frontend/features/academic-tasks/components/AcademicTasksWorkspace.test.tsx
// Purpose: Tests prioritized Academic Tasks loading, empty,
// error, populated, drawer, and create-task workspace behavior.

import {
  createTheme,
  Drawer,
  MantineProvider,
  Modal,
} from "@mantine/core";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks = vi.hoisted(
  () => ({
    notificationsShow:
      vi.fn(),
  }),
);

vi.mock(
  "@mantine/notifications",
  () => ({
    notifications: {
      show:
        mocks.notificationsShow,
    },
  }),
);

import {
  AcademicTaskApiError,
  createAcademicTask,
  listPrioritizedAcademicTasks,
} from "../api";
import type {
  AcademicTaskPriorityBreakdown,
  AcademicTaskPriorityResponse,
  AcademicTaskResponse,
} from "../types";

import {
  AcademicTasksWorkspace,
} from "./AcademicTasksWorkspace";

vi.mock(
  "../api",
  async () => {
    const actual =
      await vi.importActual<
        typeof import("../api")
      >("../api");

    return {
      ...actual,

      listPrioritizedAcademicTasks:
        vi.fn(),

      createAcademicTask:
        vi.fn(),
    };
  },
);

const mockedListPrioritizedAcademicTasks =
  vi.mocked(
    listPrioritizedAcademicTasks,
  );

const mockedCreateAcademicTask =
  vi.mocked(
    createAcademicTask,
  );

const testTheme =
  createTheme({
    components: {
      Modal: Modal.extend({
        defaultProps: {
          transitionProps: {
            duration:
              0,
          },
        },
      }),

      Drawer: Drawer.extend({
        defaultProps: {
          transitionProps: {
            duration:
              0,
          },
        },
      }),
    },
  });

const SUBJECT = {
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

const TASK:
  AcademicTaskResponse = {
  id:
    "11111111-1111-4111-8111-111111111111",

  subject_id:
    SUBJECT.id,

  title:
    "STS reflection paper",

  description:
    "Write the final course reflection.",

  deadline:
    "2026-08-20T12:00:00Z",

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
};

const PRIORITY:
  AcademicTaskPriorityBreakdown = {
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
};

const PRIORITIZED_TASK:
  AcademicTaskPriorityResponse = {
  task:
    TASK,

  priority:
    PRIORITY,
};

function renderWorkspace(
  subjects = [
    SUBJECT,
  ],
) {
  return render(
    <MantineProvider
      env="test"
      theme={
        testTheme
      }
    >
      <AcademicTasksWorkspace
        subjects={
          subjects
        }
      />
    </MantineProvider>,
  );
}

function getCreateTaskForm():
  HTMLFormElement {
  const titleInput =
    screen.getByLabelText(
      /Task title/i,
    );

  const form =
    titleInput.closest(
      "form",
    );

  if (
    !form
  ) {
    throw new Error(
      "Create academic task form was not found.",
    );
  }

  return form;
}

async function openCreateTaskModal() {
  fireEvent.click(
    screen.getByRole(
      "button",
      {
        name:
          "Create task",
      },
    ),
  );

  expect(
    await screen.findByText(
      "Create academic task",
    ),
  ).toBeInTheDocument();

  expect(
    await screen.findByLabelText(
      /Task title/i,
    ),
  ).toBeInTheDocument();
}

async function openTaskDrawer():
  Promise<HTMLElement> {
  const taskButton =
    await screen.findByRole(
      "button",
      {
        name:
          "View to-do task: STS reflection paper",
      },
    );

  fireEvent.click(
    taskButton,
  );

  const drawerTitle =
    await screen.findByText(
      "Academic task details",
    );

  const drawer =
    drawerTitle.closest(
      '[role="dialog"]',
    );

  if (
    !drawer
  ) {
    throw new Error(
      "Academic task details drawer was not found.",
    );
  }

  return drawer as HTMLElement;
}

describe(
  "AcademicTasksWorkspace",
  () => {
    beforeEach(
      () => {
        vi.clearAllMocks();
      },
    );

    it(
      "requires a subject before loading academic tasks",
      () => {
        renderWorkspace(
          [],
        );

        expect(
          screen.getByText(
            "Create a subject first",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open subjects",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/subjects",
        );

        expect(
          mockedListPrioritizedAcademicTasks,
        ).not.toHaveBeenCalled();

        expect(
          mockedCreateAcademicTask,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "shows an empty state when the student has no tasks",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValue(
            [],
          );

        renderWorkspace();

        expect(
          screen.getByText(
            "Prioritizing your tasks",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "No academic tasks yet",
          ),
        ).toBeInTheDocument();

        expect(
          mockedListPrioritizedAcademicTasks,
        ).toHaveBeenCalledWith({
          limit:
            100,
        });
      },
    );

    it(
      "renders loaded tasks with their subject metadata and priority",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValue([
            PRIORITIZED_TASK,
          ]);

        renderWorkspace();

        expect(
          await screen.findByText(
            "STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "GESTSOC",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "1 task",
          ),
        ).toBeInTheDocument();

        const drawer =
          await openTaskDrawer();

        expect(
          within(
            drawer,
          ).getByText(
            "Write the final course reflection.",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            drawer,
          ).getByLabelText(
            "Status for STS reflection paper",
          ),
        ).toHaveValue(
          "pending",
        );

        expect(
          within(
            drawer,
          ).getByText(
            "Medium",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            drawer,
          ).getByText(
            "Assignment",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            drawer,
          ).getByText(
            "2 hr",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            drawer,
          ).getByText(
            "Highest priority",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            drawer,
          ).getByText(
            "Priority 78.5/100",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            drawer,
          ).getByRole(
            "progressbar",
            {
              name:
                "Priority score for STS reflection paper",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "uses a safe fallback when a task references an unavailable subject",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValue([
            {
              task: {
                ...TASK,

                subject_id:
                  "33333333-3333-4333-8333-333333333333",
              },

              priority:
                PRIORITY,
            },
          ]);

        renderWorkspace();

        expect(
          await screen.findByText(
            "Unknown subject",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows controlled API errors",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockRejectedValue(
            new AcademicTaskApiError(
              "Academic task storage is temporarily unavailable.",
              503,
              "ACADEMIC_TASK_PERSISTENCE_ERROR",
            ),
          );

        renderWorkspace();

        expect(
          await screen.findByText(
            "Tasks could not be loaded",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Academic task storage is temporarily unavailable.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Try again",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "uses a safe generic message for unexpected loading errors",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockRejectedValue(
            new Error(
              "internal details",
            ),
          );

        renderWorkspace();

        expect(
          await screen.findByText(
            "Your academic tasks could not be loaded.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "internal details",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "retries loading after an error",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockRejectedValueOnce(
            new AcademicTaskApiError(
              "Temporary failure.",
              503,
              "ACADEMIC_TASK_PERSISTENCE_ERROR",
            ),
          )
          .mockResolvedValueOnce([
            PRIORITIZED_TASK,
          ]);

        renderWorkspace();

        const retryButton =
          await screen.findByRole(
            "button",
            {
              name:
                "Try again",
            },
          );

        fireEvent.click(
          retryButton,
        );

        await waitFor(
          () => {
            expect(
              mockedListPrioritizedAcademicTasks,
            ).toHaveBeenCalledTimes(
              2,
            );
          },
        );

        expect(
          await screen.findByText(
            "STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Temporary failure.",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "opens the create-task modal",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValue(
            [],
          );

        renderWorkspace();

        await screen.findByText(
          "No academic tasks yet",
        );

        await openCreateTaskModal();

        expect(
          screen.getByLabelText(
            /Deadline/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "textbox",
            {
              name:
                /^Estimated completion time/i,
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "validates required create-task fields before calling the API",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValue(
            [],
          );

        renderWorkspace();

        await screen.findByText(
          "No academic tasks yet",
        );

        await openCreateTaskModal();

        fireEvent.submit(
          getCreateTaskForm(),
        );

        expect(
          await screen.findByText(
            "Enter a task title.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Select a deadline.",
          ),
        ).toBeInTheDocument();

        expect(
          mockedCreateAcademicTask,
        ).not.toHaveBeenCalled();

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task not created",

          message:
            "Check the highlighted task details.",

          color:
            "red",
        });
      },
    );

    it(
      "creates a valid academic task and refreshes its priority",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValueOnce(
            [],
          )
          .mockResolvedValueOnce([
            PRIORITIZED_TASK,
          ]);

        mockedCreateAcademicTask
          .mockResolvedValue(
            TASK,
          );

        renderWorkspace();

        await screen.findByText(
          "No academic tasks yet",
        );

        await openCreateTaskModal();

        fireEvent.change(
          screen.getByLabelText(
            /Task title/i,
          ),
          {
            target: {
              value:
                "STS reflection paper",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            "Description",
          ),
          {
            target: {
              value:
                "Write the final course reflection.",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /Deadline/i,
          ),
          {
            target: {
              value:
                "2026-08-20T20:00",
            },
          },
        );

        fireEvent.submit(
          getCreateTaskForm(),
        );

        await waitFor(
          () => {
            expect(
              mockedCreateAcademicTask,
            ).toHaveBeenCalledTimes(
              1,
            );
          },
        );

        const createRequest =
          mockedCreateAcademicTask
            .mock.calls[0][0];

        expect(
          createRequest,
        ).toMatchObject({
          subject_id:
            SUBJECT.id,

          title:
            "STS reflection paper",

          description:
            "Write the final course reflection.",

          estimated_minutes:
            60,

          difficulty:
            "medium",

          task_type:
            "assignment",

          output_type:
            "other",
        });

        expect(
          Number.isNaN(
            new Date(
              createRequest.deadline,
            ).getTime(),
          ),
        ).toBe(
          false,
        );

        await waitFor(
          () => {
            expect(
              mockedListPrioritizedAcademicTasks,
            ).toHaveBeenCalledTimes(
              2,
            );
          },
        );

        expect(
          await screen.findByText(
            "STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "1 task",
          ),
        ).toBeInTheDocument();

        const drawer =
          await openTaskDrawer();

        expect(
          within(
            drawer,
          ).getByText(
            "Priority 78.5/100",
          ),
        ).toBeInTheDocument();

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task created",

          message:
            "STS reflection paper was added to your academic tasks.",

          color:
            "green",
        });
      },
    );

    it(
      "shows controlled API errors when task creation fails",
      async () => {
        mockedListPrioritizedAcademicTasks
          .mockResolvedValue(
            [],
          );

        mockedCreateAcademicTask
          .mockRejectedValue(
            new AcademicTaskApiError(
              "The selected subject could not be used.",
              400,
              "ACADEMIC_TASK_VALIDATION_ERROR",
            ),
          );

        renderWorkspace();

        await screen.findByText(
          "No academic tasks yet",
        );

        await openCreateTaskModal();

        fireEvent.change(
          screen.getByLabelText(
            /Task title/i,
          ),
          {
            target: {
              value:
                "New assignment",
            },
          },
        );

        fireEvent.change(
          screen.getByLabelText(
            /Deadline/i,
          ),
          {
            target: {
              value:
                "2026-08-20T20:00",
            },
          },
        );

        fireEvent.submit(
          getCreateTaskForm(),
        );

        await waitFor(
          () => {
            expect(
              mockedCreateAcademicTask,
            ).toHaveBeenCalledTimes(
              1,
            );
          },
        );

        expect(
          mockedListPrioritizedAcademicTasks,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task not created",

          message:
            "The selected subject could not be used.",

          color:
            "red",
        });

        expect(
          screen.queryByText(
            "New assignment",
          ),
        ).not.toBeInTheDocument();
      },
    );
  },
);