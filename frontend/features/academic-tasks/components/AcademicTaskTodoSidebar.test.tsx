// File: /frontend/features/academic-tasks/components/AcademicTaskTodoSidebar.test.tsx
// Purpose: Tests the prioritized Academic Task to-do sidebar.

import {
  MantineProvider,
} from "@mantine/core";
import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import type {
  AcademicTaskPriorityBreakdown,
  AcademicTaskResponse,
} from "../types";

import {
  AcademicTaskTodoSidebar,
} from "./AcademicTaskTodoSidebar";

const SUBJECT:
  SubjectSummary = {
    id:
      "subject-1",

    name:
      "GESTSOC",

    color:
      "violet",

    created_at:
      "2026-08-01T00:00:00Z",

    updated_at:
      "2026-08-01T00:00:00Z",
  };

function makeTask(
  id: string,
  title: string,
  status:
    AcademicTaskResponse["status"] =
    "pending",
): AcademicTaskResponse {
  return {
    id,

    subject_id:
      "subject-1",

    title,

    description:
      null,

    deadline:
      "2026-08-20T18:00:00",

    estimated_minutes:
      120,

    difficulty:
      "medium",

    task_type:
      "assignment",

    output_type:
      "writing",

    status,

    created_at:
      "2026-08-01T00:00:00Z",

    updated_at:
      "2026-08-01T00:00:00Z",
  };
}

const PRIORITY:
  AcademicTaskPriorityBreakdown = {
    total_score:
      78.5,

    deadline_score:
      85,

    difficulty_score:
      100,

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

describe(
  "AcademicTaskTodoSidebar",
  () => {
    it(
      "preserves backend task order for active tasks",
      () => {
        render(
          <MantineProvider>
            <AcademicTaskTodoSidebar
              tasks={[
                makeTask(
                  "task-1",
                  "First priority",
                ),

                makeTask(
                  "task-2",
                  "Second priority",
                ),
              ]}
              priorityByTaskId={{
                "task-1":
                  PRIORITY,

                "task-2": {
                  ...PRIORITY,

                  total_score:
                    60,
                },
              }}
              subjects={[
                SUBJECT,
              ]}
              selectedTaskId={
                null
              }
              onTaskSelect={() => {}}
            />
          </MantineProvider>,
        );

        const buttons =
          screen.getAllByRole(
            "button",
          );

        expect(
          buttons[0],
        ).toHaveTextContent(
          "First priority",
        );

        expect(
          buttons[1],
        ).toHaveTextContent(
          "Second priority",
        );
      },
    );

    it(
      "hides completed and cancelled tasks from active to-do items",
      () => {
        render(
          <MantineProvider>
            <AcademicTaskTodoSidebar
              tasks={[
                makeTask(
                  "active",
                  "Active task",
                ),

                makeTask(
                  "complete",
                  "Finished task",
                  "completed",
                ),

                makeTask(
                  "cancelled",
                  "Cancelled task",
                  "cancelled",
                ),
              ]}
              priorityByTaskId={{
                active:
                  PRIORITY,
              }}
              subjects={[
                SUBJECT,
              ]}
              selectedTaskId={
                null
              }
              onTaskSelect={() => {}}
            />
          </MantineProvider>,
        );

        expect(
          screen.getByText(
            "Active task",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Finished task",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Cancelled task",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            "1 completed task",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "reports a selected to-do task",
      () => {
        const onTaskSelect =
          vi.fn();

        const task =
          makeTask(
            "task-1",
            "Research paper",
          );

        render(
          <MantineProvider>
            <AcademicTaskTodoSidebar
              tasks={[
                task,
              ]}
              priorityByTaskId={{
                "task-1":
                  PRIORITY,
              }}
              subjects={[
                SUBJECT,
              ]}
              selectedTaskId={
                null
              }
              onTaskSelect={
                onTaskSelect
              }
            />
          </MantineProvider>,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /View to-do task: Research paper/i,
            },
          ),
        );

        expect(
          onTaskSelect,
        ).toHaveBeenCalledWith(
          task,
        );
      },
    );
  },
);