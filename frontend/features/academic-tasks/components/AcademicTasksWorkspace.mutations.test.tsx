// File: /frontend/features/academic-tasks/components/AcademicTasksWorkspace.mutations.test.tsx
// Purpose: Tests Academic Task edit, status update, deletion,
// and automatic deterministic priority refresh behavior.

import {
  createTheme,
  MantineProvider,
  Modal,
} from "@mantine/core";
import {
  ModalsProvider,
} from "@mantine/modals";
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
  deleteAcademicTask,
  listPrioritizedAcademicTasks,
  updateAcademicTask,
  updateAcademicTaskStatus,
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

      updateAcademicTask:
        vi.fn(),

      updateAcademicTaskStatus:
        vi.fn(),

      deleteAcademicTask:
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

const mockedUpdateAcademicTask =
  vi.mocked(
    updateAcademicTask,
  );

const mockedUpdateAcademicTaskStatus =
  vi.mocked(
    updateAcademicTaskStatus,
  );

const mockedDeleteAcademicTask =
  vi.mocked(
    deleteAcademicTask,
  );

const testTheme =
  createTheme({
    components: {
      Modal: Modal.extend({
        defaultProps: {
          transitionProps: {
            duration: 0,
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

function renderWorkspace() {
  return render(
    <MantineProvider
      theme={testTheme}
      env="test"
    >
      <ModalsProvider>
        <AcademicTasksWorkspace
          subjects={[
            SUBJECT,
          ]}
        />
      </ModalsProvider>
    </MantineProvider>,
  );
}

async function waitForTask() {
  expect(
    await screen.findByText(
      "STS reflection paper",
    ),
  ).toBeInTheDocument();
}

function getEditForm():
  HTMLFormElement {
  const titleInput =
    screen.getByLabelText(
      /Task title/i,
    );

  const form =
    titleInput.closest(
      "form",
    );

  if (!form) {
    throw new Error(
      "Edit academic task form was not found.",
    );
  }

  return form;
}

async function chooseStatus(
  status: string,
) {
  const statusInput =
    screen.getByLabelText(
      "Status for STS reflection paper",
    );

  fireEvent.change(
    statusInput,
    {
      target: {
        value:
          status,
      },
    },
  );
}

async function confirmDelete() {
  fireEvent.click(
    screen.getByRole(
      "button",
      {
        name:
          "Delete task",
      },
    ),
  );

  const dialog =
    await screen.findByRole(
      "dialog",
    );

  expect(
    within(
      dialog,
    ).getByText(
      "Delete academic task?",
    ),
  ).toBeInTheDocument();

  fireEvent.click(
    within(
      dialog,
    ).getByRole(
      "button",
      {
        name:
          "Delete task",
      },
    ),
  );
}

describe(
  "AcademicTasksWorkspace mutations",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockedListPrioritizedAcademicTasks
        .mockResolvedValue([
          PRIORITIZED_TASK,
        ]);
    });

    it(
      "opens an existing task for editing with its saved values",
      async () => {
        renderWorkspace();

        await waitForTask();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Edit task",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Edit academic task",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByLabelText(
            /Task title/i,
          ),
        ).toHaveValue(
          "STS reflection paper",
        );

        expect(
          screen.getByLabelText(
            "Description",
          ),
        ).toHaveValue(
          "Write the final course reflection.",
        );

        expect(
          screen.getByRole(
            "textbox",
            {
              name:
                /^Estimated completion time/i,
            },
          ),
        ).toHaveValue(
          "120",
        );

        expect(
          mockedCreateAcademicTask,
        ).not.toHaveBeenCalled();

        expect(
          mockedListPrioritizedAcademicTasks,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );

    it(
      "updates an existing academic task and refreshes its priority",
      async () => {
        const updatedTask:
          AcademicTaskResponse = {
          ...TASK,

          title:
            "Updated STS reflection paper",

          updated_at:
            "2026-08-09T12:00:00Z",
        };

        const updatedPriority:
          AcademicTaskPriorityBreakdown = {
          ...PRIORITY,

          total_score:
            84.5,
        };

        mockedUpdateAcademicTask
          .mockResolvedValue(
            updatedTask,
          );

        mockedListPrioritizedAcademicTasks
          .mockResolvedValueOnce([
            PRIORITIZED_TASK,
          ])
          .mockResolvedValueOnce([
            {
              task:
                updatedTask,

              priority:
                updatedPriority,
            },
          ]);

        renderWorkspace();

        await waitForTask();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Edit task",
            },
          ),
        );

        await screen.findByText(
          "Edit academic task",
        );

        const titleInput =
          await screen.findByLabelText(
            /Task title/i,
          );

        fireEvent.change(
          titleInput,
          {
            target: {
              value:
                "Updated STS reflection paper",
            },
          },
        );

        fireEvent.submit(
          getEditForm(),
        );

        await waitFor(
          () => {
            expect(
              mockedUpdateAcademicTask,
            ).toHaveBeenCalledTimes(
              1,
            );
          },
        );

        expect(
          mockedUpdateAcademicTask,
        ).toHaveBeenCalledWith(
          TASK.id,
          expect.objectContaining({
            subject_id:
              SUBJECT.id,

            title:
              "Updated STS reflection paper",

            estimated_minutes:
              120,

            difficulty:
              "medium",

            task_type:
              "assignment",

            output_type:
              "writing",
          }),
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
            "Updated STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Priority 84.5/100",
          ),
        ).toBeInTheDocument();

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task updated",

          message:
            "Updated STS reflection paper was updated.",

          color:
            "green",
        });
      },
    );

    it(
      "updates task status and refreshes deterministic priority",
      async () => {
        const updatedTask:
          AcademicTaskResponse = {
          ...TASK,

          status:
            "in_progress",

          updated_at:
            "2026-08-09T12:00:00Z",
        };

        const updatedPriority:
          AcademicTaskPriorityBreakdown = {
          ...PRIORITY,

          total_score:
            81,

          status_score:
            100,
        };

        mockedUpdateAcademicTaskStatus
          .mockResolvedValue(
            updatedTask,
          );

        mockedListPrioritizedAcademicTasks
          .mockResolvedValueOnce([
            PRIORITIZED_TASK,
          ])
          .mockResolvedValueOnce([
            {
              task:
                updatedTask,

              priority:
                updatedPriority,
            },
          ]);

        renderWorkspace();

        await waitForTask();

        await chooseStatus(
          "in_progress",
        );

        await waitFor(
          () => {
            expect(
              mockedUpdateAcademicTaskStatus,
            ).toHaveBeenCalledWith(
              TASK.id,
              {
                status:
                  "in_progress",
              },
            );
          },
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
          screen.getByLabelText(
            "Status for STS reflection paper",
          ),
        ).toHaveValue(
          "in_progress",
        );

        expect(
          screen.getByText(
            "Priority 81.0/100",
          ),
        ).toBeInTheDocument();

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task status updated",

          message:
            "STS reflection paper is now in progress.",

          color:
            "green",
        });
      },
    );

    it(
      "keeps the existing status when a status update fails",
      async () => {
        mockedUpdateAcademicTaskStatus
          .mockRejectedValue(
            new AcademicTaskApiError(
              "Task status could not be saved.",
              503,
              "ACADEMIC_TASK_PERSISTENCE_ERROR",
            ),
          );

        renderWorkspace();

        await waitForTask();

        await chooseStatus(
          "completed",
        );

        await waitFor(
          () => {
            expect(
              mockedUpdateAcademicTaskStatus,
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
          screen.getByLabelText(
            "Status for STS reflection paper",
          ),
        ).toHaveValue(
          "pending",
        );

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Status not updated",

          message:
            "Task status could not be saved.",

          color:
            "red",
        });
      },
    );

    it(
      "deletes a task and refreshes the remaining priority list",
      async () => {
        mockedDeleteAcademicTask
          .mockResolvedValue(
            undefined,
          );

        mockedListPrioritizedAcademicTasks
          .mockResolvedValueOnce([
            PRIORITIZED_TASK,
          ])
          .mockResolvedValueOnce(
            [],
          );

        renderWorkspace();

        await waitForTask();

        await confirmDelete();

        await waitFor(
          () => {
            expect(
              mockedDeleteAcademicTask,
            ).toHaveBeenCalledWith(
              TASK.id,
            );
          },
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
            "No academic tasks yet",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "0 tasks",
          ),
        ).toBeInTheDocument();

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task deleted",

          message:
            "STS reflection paper was removed from your academic tasks.",

          color:
            "green",
        });
      },
    );

    it(
      "keeps the task when deletion fails",
      async () => {
        mockedDeleteAcademicTask
          .mockRejectedValue(
            new AcademicTaskApiError(
              "Task deletion is temporarily unavailable.",
              503,
              "ACADEMIC_TASK_PERSISTENCE_ERROR",
            ),
          );

        renderWorkspace();

        await waitForTask();

        await confirmDelete();

        await waitFor(
          () => {
            expect(
              mockedDeleteAcademicTask,
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
          screen.getByText(
            "STS reflection paper",
          ),
        ).toBeInTheDocument();

        expect(
          mocks.notificationsShow,
        ).toHaveBeenCalledWith({
          title:
            "Task not deleted",

          message:
            "Task deletion is temporarily unavailable.",

          color:
            "red",
        });
      },
    );
  },
);