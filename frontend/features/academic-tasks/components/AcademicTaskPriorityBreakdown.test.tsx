// File: /frontend/features/academic-tasks/components/AcademicTaskPriorityBreakdown.test.tsx
// Purpose: Tests the deterministic Academic Task priority
// factor explanation interface.

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
} from "vitest";

import type {
  AcademicTaskPriorityBreakdown as AcademicTaskPriorityBreakdownData,
} from "../types";

import {
  AcademicTaskPriorityBreakdown,
} from "./AcademicTaskPriorityBreakdown";

const PRIORITY:
  AcademicTaskPriorityBreakdownData = {
  total_score: 78.5,
  deadline_score: 100,
  difficulty_score: 60,
  estimated_time_score: 60,
  output_confidence_score: 75,
  previous_performance_score: 50,
  available_study_time_score: 80,
  status_score: 50,
};

function renderBreakdown() {
  render(
    <MantineProvider>
      <AcademicTaskPriorityBreakdown
        taskTitle="STS reflection paper"
        priority={
          PRIORITY
        }
      />
    </MantineProvider>,
  );
}

describe(
  "AcademicTaskPriorityBreakdown",
  () => {
    it(
      "keeps factor details collapsed initially",
      () => {
        renderBreakdown();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Why this priority?",
            },
          ),
        ).toHaveAttribute(
          "aria-expanded",
          "false",
        );
      },
    );

    it(
      "shows all seven deterministic factor scores",
      () => {
        renderBreakdown();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Why this priority?",
            },
          ),
        );

        expect(
          screen.getByText(
            "Deadline proximity",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Difficulty",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Estimated completion time",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Output confidence",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Previous performance",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Available study time",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Task status",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByLabelText(
            "Deadline proximity priority factor for STS reflection paper",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "explains how factor scores should be interpreted",
      () => {
        renderBreakdown();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Why this priority?",
            },
          ),
        );

        expect(
          screen.getByText(
            /Each factor is scored from 0 to 100/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);