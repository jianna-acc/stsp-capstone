// File: /frontend/features/academic-tasks/validation.ts
// Purpose: Validates and normalizes Academic Task create-form
// values before they are sent to the protected backend API.

import type {
  AcademicTaskCreateRequest,
  AcademicTaskDifficulty,
  AcademicTaskOutputType,
  AcademicTaskType,
} from "./types";

export interface AcademicTaskFormValues {
  subjectId: string;
  title: string;
  description: string;
  deadline: string;
  estimatedMinutes:
    | number
    | string;
  difficulty:
    | AcademicTaskDifficulty
    | "";
  taskType:
    | AcademicTaskType
    | "";
  outputType:
    | AcademicTaskOutputType
    | "";
}

export interface AcademicTaskFieldErrors {
  subjectId?: string;
  title?: string;
  description?: string;
  deadline?: string;
  estimatedMinutes?: string;
  difficulty?: string;
  taskType?: string;
  outputType?: string;
}

export type AcademicTaskValidationResult =
  | {
      success: true;
      data: AcademicTaskCreateRequest;
    }
  | {
      success: false;
      fieldErrors:
        AcademicTaskFieldErrors;
    };

export const EMPTY_ACADEMIC_TASK_FORM:
  AcademicTaskFormValues = {
  subjectId: "",
  title: "",
  description: "",
  deadline: "",
  estimatedMinutes: 60,
  difficulty: "medium",
  taskType: "assignment",
  outputType: "other",
};

export const ACADEMIC_TASK_DIFFICULTY_OPTIONS = [
  {
    value: "easy",
    label: "Easy",
  },
  {
    value: "medium",
    label: "Medium",
  },
  {
    value: "hard",
    label: "Hard",
  },
] as const;

export const ACADEMIC_TASK_TYPE_OPTIONS = [
  {
    value: "assignment",
    label: "Assignment",
  },
  {
    value: "project",
    label: "Project",
  },
  {
    value: "exam",
    label: "Exam",
  },
  {
    value: "quiz",
    label: "Quiz",
  },
  {
    value: "reading",
    label: "Reading",
  },
  {
    value: "presentation",
    label: "Presentation",
  },
  {
    value: "research",
    label: "Research",
  },
  {
    value: "other",
    label: "Other",
  },
] as const;

export const ACADEMIC_TASK_OUTPUT_TYPE_OPTIONS = [
  {
    value: "writing",
    label: "Writing",
  },
  {
    value: "computation",
    label: "Computation",
  },
  {
    value: "research",
    label: "Research",
  },
  {
    value: "presentation",
    label: "Presentation",
  },
  {
    value: "creative",
    label: "Creative work",
  },
  {
    value: "reading_analysis",
    label: "Reading and analysis",
  },
  {
    value: "memorization",
    label: "Memorization",
  },
  {
    value: "mixed",
    label: "Mixed outputs",
  },
  {
    value: "other",
    label: "Other",
  },
] as const;

function isDifficulty(
  value: string,
): value is AcademicTaskDifficulty {
  return (
    value === "easy" ||
    value === "medium" ||
    value === "hard"
  );
}

function isTaskType(
  value: string,
): value is AcademicTaskType {
  return (
    value === "assignment" ||
    value === "project" ||
    value === "exam" ||
    value === "quiz" ||
    value === "reading" ||
    value === "presentation" ||
    value === "research" ||
    value === "other"
  );
}

function isOutputType(
  value: string,
): value is AcademicTaskOutputType {
  return (
    value === "writing" ||
    value === "computation" ||
    value === "research" ||
    value === "presentation" ||
    value === "creative" ||
    value === "reading_analysis" ||
    value === "memorization" ||
    value === "mixed" ||
    value === "other"
  );
}

function parseEstimatedMinutes(
  value: number | string,
): number | null {
  if (
    typeof value === "number"
  ) {
    return Number.isFinite(value)
      ? value
      : null;
  }

  const normalized =
    value.trim();

  if (!normalized) {
    return null;
  }

  const parsed =
    Number(normalized);

  return Number.isFinite(parsed)
    ? parsed
    : null;
}

export function validateAcademicTaskForm(
  values: AcademicTaskFormValues,
): AcademicTaskValidationResult {
  const fieldErrors:
    AcademicTaskFieldErrors = {};

  const subjectId =
    values.subjectId.trim();

  const title =
    values.title.trim();

  const description =
    values.description.trim();

  const deadline =
    values.deadline.trim();

  const estimatedMinutes =
    parseEstimatedMinutes(
      values.estimatedMinutes,
    );

  if (!subjectId) {
    fieldErrors.subjectId =
      "Select a subject.";
  }

  if (!title) {
    fieldErrors.title =
      "Enter a task title.";
  } else if (
    title.length > 200
  ) {
    fieldErrors.title =
      "Task title must be 200 characters or fewer.";
  }

  if (
    description.length > 5000
  ) {
    fieldErrors.description =
      "Description must be 5000 characters or fewer.";
  }

  if (!deadline) {
    fieldErrors.deadline =
      "Select a deadline.";
  } else {
    const parsedDeadline =
      new Date(deadline);

    if (
      Number.isNaN(
        parsedDeadline.getTime(),
      )
    ) {
      fieldErrors.deadline =
        "Enter a valid deadline.";
    }
  }

  if (
    estimatedMinutes === null
  ) {
    fieldErrors.estimatedMinutes =
      "Enter the estimated completion time.";
  } else if (
    !Number.isInteger(
      estimatedMinutes,
    ) ||
    estimatedMinutes < 1 ||
    estimatedMinutes > 10080
  ) {
    fieldErrors.estimatedMinutes =
      "Estimated time must be between 1 and 10080 minutes.";
  }

  if (
    !isDifficulty(
      values.difficulty,
    )
  ) {
    fieldErrors.difficulty =
      "Select a difficulty.";
  }

  if (
    !isTaskType(
      values.taskType,
    )
  ) {
    fieldErrors.taskType =
      "Select a task type.";
  }

  if (
    !isOutputType(
      values.outputType,
    )
  ) {
    fieldErrors.outputType =
      "Select an academic output type.";
  }

  if (
    Object.keys(
      fieldErrors,
    ).length > 0
  ) {
    return {
      success: false,
      fieldErrors,
    };
  }

  /*
   * The guards above guarantee these values are valid.
   */
  const normalizedDeadline =
    new Date(
      deadline,
    ).toISOString();

  return {
    success: true,

    data: {
      subject_id:
        subjectId,

      title,

      description:
        description || null,

      deadline:
        normalizedDeadline,

      estimated_minutes:
        estimatedMinutes as number,

      difficulty:
        values.difficulty as AcademicTaskDifficulty,

      task_type:
        values.taskType as AcademicTaskType,

      output_type:
        values.outputType as AcademicTaskOutputType,
    },
  };
}