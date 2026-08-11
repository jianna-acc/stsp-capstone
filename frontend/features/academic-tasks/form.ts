// File: /frontend/features/academic-tasks/form.ts
// Purpose: Converts persisted Academic Tasks into editable
// frontend form values for create and update workflows.

import type {
  AcademicTaskResponse,
} from "./types";
import type {
  AcademicTaskFormValues,
} from "./validation";

function padDatePart(
  value: number,
): string {
  return String(
    value,
  ).padStart(
    2,
    "0",
  );
}

export function toDateTimeLocalValue(
  value: string,
): string {
  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "";
  }

  const year =
    date.getFullYear();

  const month =
    padDatePart(
      date.getMonth() + 1,
    );

  const day =
    padDatePart(
      date.getDate(),
    );

  const hours =
    padDatePart(
      date.getHours(),
    );

  const minutes =
    padDatePart(
      date.getMinutes(),
    );

  return (
    `${year}-${month}-${day}` +
    `T${hours}:${minutes}`
  );
}

export function academicTaskToFormValues(
  task: AcademicTaskResponse,
): AcademicTaskFormValues {
  return {
    subjectId:
      task.subject_id,

    title:
      task.title,

    description:
      task.description ?? "",

    deadline:
      toDateTimeLocalValue(
        task.deadline,
      ),

    estimatedMinutes:
      task.estimated_minutes,

    difficulty:
      task.difficulty,

    taskType:
      task.task_type,

    outputType:
      task.output_type,
  };
}