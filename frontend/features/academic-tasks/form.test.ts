// File: /frontend/features/academic-tasks/form.test.ts
// Purpose: Tests conversion of persisted Academic Tasks into
// editable frontend form values.

import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  AcademicTaskResponse,
} from "./types";
import {
  academicTaskToFormValues,
  toDateTimeLocalValue,
} from "./form";

const TASK:
  AcademicTaskResponse = {
  id:
    "11111111-1111-4111-8111-111111111111",

  subject_id:
    "22222222-2222-4222-8222-222222222222",

  title:
    "Research paper",

  description:
    "Complete the final draft.",

  deadline:
    "2026-08-20T12:00:00Z",

  estimated_minutes:
    180,

  difficulty:
    "hard",

  task_type:
    "assignment",

  output_type:
    "writing",

  status:
    "in_progress",

  created_at:
    "2026-08-09T10:00:00Z",

  updated_at:
    "2026-08-09T10:00:00Z",
};

describe(
  "academic task form helpers",
  () => {
    it(
      "converts a persisted task into editable form values",
      () => {
        const result =
          academicTaskToFormValues(
            TASK,
          );

        expect(
          result,
        ).toMatchObject({
          subjectId:
            TASK.subject_id,

          title:
            "Research paper",

          description:
            "Complete the final draft.",

          estimatedMinutes:
            180,

          difficulty:
            "hard",

          taskType:
            "assignment",

          outputType:
            "writing",
        });

        expect(
          result.deadline,
        ).toMatch(
          /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/,
        );
      },
    );

    it(
      "converts null descriptions to an empty form value",
      () => {
        const result =
          academicTaskToFormValues({
            ...TASK,
            description: null,
          });

        expect(
          result.description,
        ).toBe("");
      },
    );

    it(
      "returns an empty datetime value for invalid persisted dates",
      () => {
        expect(
          toDateTimeLocalValue(
            "invalid-date",
          ),
        ).toBe("");
      },
    );

    it(
      "creates a valid datetime-local value",
      () => {
        const result =
          toDateTimeLocalValue(
            "2026-08-20T12:00:00Z",
          );

        expect(
          result,
        ).toMatch(
          /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/,
        );

        expect(
          Number.isNaN(
            new Date(
              result,
            ).getTime(),
          ),
        ).toBe(false);
      },
    );
  },
);