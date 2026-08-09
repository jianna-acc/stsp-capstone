// File: /frontend/features/academic-tasks/validation.test.ts
// Purpose: Tests Academic Task create-form validation and
// normalization before backend submission.

import {
  describe,
  expect,
  it,
} from "vitest";

import {
  EMPTY_ACADEMIC_TASK_FORM,
  validateAcademicTaskForm,
} from "./validation";

const SUBJECT_ID =
  "22222222-2222-4222-8222-222222222222";

function validValues() {
  return {
    ...EMPTY_ACADEMIC_TASK_FORM,

    subjectId:
      SUBJECT_ID,

    title:
      "Final research paper",

    description:
      "Complete the final draft.",

    deadline:
      "2026-08-20T18:00",

    estimatedMinutes:
      180,

    difficulty:
      "hard" as const,

    taskType:
      "assignment" as const,

    outputType:
      "writing" as const,
  };
}

describe(
  "validateAcademicTaskForm",
  () => {
    it(
      "normalizes a valid academic task",
      () => {
        const result =
          validateAcademicTaskForm(
            validValues(),
          );

        expect(
          result.success,
        ).toBe(true);

        if (!result.success) {
          throw new Error(
            "Valid task was rejected.",
          );
        }

        expect(
          result.data,
        ).toMatchObject({
          subject_id:
            SUBJECT_ID,

          title:
            "Final research paper",

          description:
            "Complete the final draft.",

          estimated_minutes:
            180,

          difficulty:
            "hard",

          task_type:
            "assignment",

          output_type:
            "writing",
        });

        expect(
          Number.isNaN(
            new Date(
              result.data.deadline,
            ).getTime(),
          ),
        ).toBe(false);
      },
    );

    it(
      "trims text values and converts blank descriptions to null",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),

            subjectId:
              `  ${SUBJECT_ID}  `,

            title:
              "  Read chapter 5  ",

            description:
              "   ",
          });

        expect(
          result.success,
        ).toBe(true);

        if (!result.success) {
          return;
        }

        expect(
          result.data.subject_id,
        ).toBe(
          SUBJECT_ID,
        );

        expect(
          result.data.title,
        ).toBe(
          "Read chapter 5",
        );

        expect(
          result.data.description,
        ).toBeNull();
      },
    );

    it(
      "requires a subject",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),
            subjectId: "",
          });

        expect(
          result,
        ).toMatchObject({
          success: false,

          fieldErrors: {
            subjectId:
              "Select a subject.",
          },
        });
      },
    );

    it(
      "requires a title",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),
            title: "   ",
          });

        expect(
          result,
        ).toMatchObject({
          success: false,

          fieldErrors: {
            title:
              "Enter a task title.",
          },
        });
      },
    );

    it(
      "rejects titles longer than 200 characters",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),
            title:
              "a".repeat(201),
          });

        expect(
          result.success,
        ).toBe(false);
      },
    );

    it(
      "rejects descriptions longer than 5000 characters",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),

            description:
              "a".repeat(5001),
          });

        expect(
          result.success,
        ).toBe(false);
      },
    );

    it(
      "requires a valid deadline",
      () => {
        const missing =
          validateAcademicTaskForm({
            ...validValues(),
            deadline: "",
          });

        expect(
          missing.success,
        ).toBe(false);

        const invalid =
          validateAcademicTaskForm({
            ...validValues(),
            deadline:
              "not-a-date",
          });

        expect(
          invalid.success,
        ).toBe(false);
      },
    );

    it(
      "accepts numeric strings for estimated minutes",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),

            estimatedMinutes:
              "90",
          });

        expect(
          result.success,
        ).toBe(true);

        if (!result.success) {
          return;
        }

        expect(
          result.data
            .estimated_minutes,
        ).toBe(90);
      },
    );

    it(
      "rejects invalid estimated durations",
      () => {
        for (
          const estimatedMinutes
          of [
            "",
            0,
            -1,
            10081,
            1.5,
            "abc",
          ]
        ) {
          const result =
            validateAcademicTaskForm({
              ...validValues(),
              estimatedMinutes,
            });

          expect(
            result.success,
          ).toBe(false);
        }
      },
    );

    it(
      "rejects missing select values",
      () => {
        const result =
          validateAcademicTaskForm({
            ...validValues(),

            difficulty: "",
            taskType: "",
            outputType: "",
          });

        expect(
          result,
        ).toMatchObject({
          success: false,

          fieldErrors: {
            difficulty:
              "Select a difficulty.",

            taskType:
              "Select a task type.",

            outputType:
              "Select an academic output type.",
          },
        });
      },
    );
  },
);