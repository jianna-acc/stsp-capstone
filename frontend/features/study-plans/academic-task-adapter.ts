// File: /frontend/features/study-plans/academic-task-adapter.ts
// Purpose: Converts prioritized Academic Task data into Track D's
// generic scheduling contract without directly depending on Track C.

import type {
  SchedulableTask,
} from "./types";


export type AcademicTaskSchedulingStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "cancelled";


export interface AcademicTaskSchedulingSource {
  task: {
    id: string;
    subject_id: string;
    title: string;
    deadline: string;
    estimated_minutes: number;
    status:
      AcademicTaskSchedulingStatus;
  };

  priority: {
    total_score: number;
  };
}


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
        normalizedScore /
          20,
      ),
    ),
  );
}


function isSchedulableStatus(
  status:
    AcademicTaskSchedulingStatus,
): boolean {
  return (
    status === "pending" ||
    status === "in_progress"
  );
}


export function academicTaskToSchedulableTask(
  item:
    AcademicTaskSchedulingSource,
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
        item.priority
          .total_score,
      ),
  };
}


export function academicTasksToSchedulableTasks(
  items:
    AcademicTaskSchedulingSource[],
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