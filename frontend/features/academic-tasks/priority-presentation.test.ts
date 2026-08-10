// File: /frontend/features/academic-tasks/priority-presentation.test.ts
// Purpose: Tests frontend presentation of deterministic
// Academic Task priority scores.

import {
  describe,
  expect,
  it,
} from "vitest";

import {
  formatAcademicTaskPriorityScore,
  getAcademicTaskPriorityPresentation,
} from "./priority-presentation";

describe(
  "academic task priority presentation",
  () => {
    it(
      "classifies highest priority scores",
      () => {
        expect(
          getAcademicTaskPriorityPresentation(
            75,
          ),
        ).toMatchObject({
          level: "highest",
          label:
            "Highest priority",
          color: "red",
        });
      },
    );

    it(
      "classifies high priority scores",
      () => {
        expect(
          getAcademicTaskPriorityPresentation(
            50,
          ).level,
        ).toBe("high");
      },
    );

    it(
      "classifies medium priority scores",
      () => {
        expect(
          getAcademicTaskPriorityPresentation(
            25,
          ).level,
        ).toBe("medium");
      },
    );

    it(
      "classifies low priority scores",
      () => {
        expect(
          getAcademicTaskPriorityPresentation(
            24.9,
          ).level,
        ).toBe("low");
      },
    );

    it(
      "formats scores consistently",
      () => {
        expect(
          formatAcademicTaskPriorityScore(
            82.345,
          ),
        ).toBe(
          "82.3/100",
        );
      },
    );
  },
);