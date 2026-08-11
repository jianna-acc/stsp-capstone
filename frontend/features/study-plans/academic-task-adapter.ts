// File: /frontend/features/study-plans/academic-task-adapter.ts
// Purpose: Converts prioritized Academic Tasks into Track D's
// generic schedulable-task contract.

import type {
  AcademicTaskPriorityResponse,
} from "@/features/academic-tasks/types";

import type {
  SchedulableTask,
} from "./types";


export function priorityScoreToWeight(
  totalScore: number,
): number {
  const normalizedScore =
    Math.min(
      100,
      Math.max(
        0,
        totalScore,
      ),
    );

  return Math.min(
    5,
    Math.max(
      1,
      Math.ceil(
        normalizedScore / 20,
      ),
    ),
  );
}


function isSchedulableStatus(
  status:
    AcademicTaskPriorityResponse["task"]["status"],
): boolean {
  return (
    status === "pending" ||
    status === "in_progress"
  );
}


export function academicTaskToSchedulableTask(
  item:
    AcademicTaskPriorityResponse,
): SchedulableTask | null {
  if (
    !isSchedulableStatus(
      item.task.status,
    )
  ) {
    return null;
  }

  return {
    task_id:
      item.task.id,

    subject_id:
      item.task.subject_id,

    title:
      item.task.title,

    deadline:
      item.task.deadline,

    estimated_minutes:
      item.task.estimated_minutes,

    priority_weight:
      priorityScoreToWeight(
        item.priority.total_score,
      ),
  };
}


export function academicTasksToSchedulableTasks(
  items:
    AcademicTaskPriorityResponse[],
): SchedulableTask[] {
  return items.flatMap(
    (item) => {
      const task =
        academicTaskToSchedulableTask(
          item,
        );

      return task
        ? [task]
        : [];
    },
  );
}