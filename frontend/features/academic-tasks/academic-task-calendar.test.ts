// File: /frontend/features/academic-tasks/academic-task-calendar.test.ts
// Purpose: Tests Academic Tasks week/month calendar helpers
// and deterministic deadline grouping.

import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  AcademicTaskResponse,
} from "./types";

import {
  addDays,
  addMonths,
  getMonthGridDays,
  getWeekDays,
  groupAcademicTasksByDeadlineDay,
  isSameMonth,
  localDateKey,
  startOfMonday,
  startOfMonth,
} from "./academic-task-calendar";

function makeTask(
  overrides:
    Partial<AcademicTaskResponse> =
    {},
): AcademicTaskResponse {
  return {
    id:
      "task-1",

    subject_id:
      "subject-1",

    title:
      "Research paper",

    description:
      null,

    deadline:
      "2026-08-12T10:00:00",

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
      "2026-08-01T00:00:00Z",

    updated_at:
      "2026-08-01T00:00:00Z",

    ...overrides,
  };
}

describe(
  "Academic Task calendar helpers",
  () => {
    it(
      "returns Monday as the beginning of the week",
      () => {
        const value =
          new Date(
            2026,
            7,
            12,
            14,
            30,
          );

        const monday =
          startOfMonday(
            value,
          );

        expect(
          monday.getDay(),
        ).toBe(
          1,
        );

        expect(
          monday.getDate(),
        ).toBe(
          10,
        );

        expect(
          monday.getHours(),
        ).toBe(
          0,
        );
      },
    );

    it(
      "returns the first day of the month",
      () => {
        const value =
          new Date(
            2026,
            7,
            12,
            14,
            30,
          );

        const result =
          startOfMonth(
            value,
          );

        expect(
          result.getDate(),
        ).toBe(
          1,
        );

        expect(
          result.getMonth(),
        ).toBe(
          7,
        );

        expect(
          result.getHours(),
        ).toBe(
          0,
        );
      },
    );

    it(
      "adds days without mutating the original date",
      () => {
        const original =
          new Date(
            2026,
            7,
            10,
          );

        const result =
          addDays(
            original,
            3,
          );

        expect(
          result.getDate(),
        ).toBe(
          13,
        );

        expect(
          original.getDate(),
        ).toBe(
          10,
        );
      },
    );

    it(
      "adds months without skipping shorter months",
      () => {
        const original =
          new Date(
            2026,
            0,
            31,
          );

        const result =
          addMonths(
            original,
            1,
          );

        expect(
          result.getMonth(),
        ).toBe(
          1,
        );

        expect(
          result.getDate(),
        ).toBe(
          28,
        );
      },
    );

    it(
      "returns seven days beginning on Monday",
      () => {
        const anchor =
          new Date(
            2026,
            7,
            12,
          );

        const days =
          getWeekDays(
            anchor,
          );

        expect(
          days,
        ).toHaveLength(
          7,
        );

        expect(
          days[0]?.getDate(),
        ).toBe(
          10,
        );

        expect(
          days[6]?.getDate(),
        ).toBe(
          16,
        );
      },
    );

    it(
      "returns a stable six-week month grid",
      () => {
        const days =
          getMonthGridDays(
            new Date(
              2026,
              7,
              12,
            ),
          );

        expect(
          days,
        ).toHaveLength(
          42,
        );

        expect(
          days[0]?.getDay(),
        ).toBe(
          1,
        );

        expect(
          days[41]?.getDay(),
        ).toBe(
          0,
        );
      },
    );

    it(
      "detects dates within the same month",
      () => {
        expect(
          isSameMonth(
            new Date(
              2026,
              7,
              1,
            ),
            new Date(
              2026,
              7,
              31,
            ),
          ),
        ).toBe(
          true,
        );

        expect(
          isSameMonth(
            new Date(
              2026,
              7,
              31,
            ),
            new Date(
              2026,
              8,
              1,
            ),
          ),
        ).toBe(
          false,
        );
      },
    );

    it(
      "creates local date keys",
      () => {
        expect(
          localDateKey(
            new Date(
              2026,
              7,
              12,
              23,
              30,
            ),
          ),
        ).toBe(
          "2026-08-12",
        );
      },
    );

    it(
      "groups tasks by deadline date and orders each day by time",
      () => {
        const later =
          makeTask({
            id:
              "later",

            deadline:
              "2026-08-12T18:00:00",
          });

        const earlier =
          makeTask({
            id:
              "earlier",

            deadline:
              "2026-08-12T09:00:00",
          });

        const tomorrow =
          makeTask({
            id:
              "tomorrow",

            deadline:
              "2026-08-13T08:00:00",
          });

        const grouped =
          groupAcademicTasksByDeadlineDay(
            [
              later,
              tomorrow,
              earlier,
            ],
          );

        expect(
          grouped
            .get(
              "2026-08-12",
            )
            ?.map(
              (
                task,
              ) =>
                task.id,
            ),
        ).toEqual(
          [
            "earlier",
            "later",
          ],
        );

        expect(
          grouped
            .get(
              "2026-08-13",
            )
            ?.map(
              (
                task,
              ) =>
                task.id,
            ),
        ).toEqual(
          [
            "tomorrow",
          ],
        );
      },
    );
  },
);