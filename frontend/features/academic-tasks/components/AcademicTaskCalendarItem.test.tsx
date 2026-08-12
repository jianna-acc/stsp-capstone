// File: /frontend/features/academic-tasks/components/AcademicTaskCalendarItem.test.tsx
// Purpose: Tests the clickable Academic Task mini-card used
// in the weekly Academic Tasks calendar.

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
  AcademicTaskCalendarItem,
} from "./AcademicTaskCalendarItem";

const TASK:
  AcademicTaskResponse = {
    id:
      "task-1",

    subject_id:
      "subject-1",

    title:
      "Research paper",

    description:
      "Complete final draft",

    deadline:
      "2026-08-12T18:00:00",

    estimated_minutes:
      120,

    difficulty:
      "hard",

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
  };

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
  "AcademicTaskCalendarItem",
  () => {
    it(
      "shows task information and priority",
      () => {
        render(
          <MantineProvider>
            <AcademicTaskCalendarItem
              task={
                TASK
              }
              priority={
                PRIORITY
              }
              subject={
                SUBJECT
              }
              selected={
                false
              }
              onSelect={() => {}}
            />
          </MantineProvider>,
        );

        expect(
          screen.getByText(
            "Research paper",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "GESTSOC",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Priority 78\.5\/100/i,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "reports the selected task when clicked",
      () => {
        const onSelect =
          vi.fn();

        render(
          <MantineProvider>
            <AcademicTaskCalendarItem
              task={
                TASK
              }
              priority={
                PRIORITY
              }
              subject={
                SUBJECT
              }
              selected={
                false
              }
              onSelect={
                onSelect
              }
            />
          </MantineProvider>,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /View academic task: Research paper/i,
            },
          ),
        );

        expect(
          onSelect,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          onSelect,
        ).toHaveBeenCalledWith(
          TASK,
        );
      },
    );

    it(
      "marks a selected mini-card for assistive technology",
      () => {
        render(
          <MantineProvider>
            <AcademicTaskCalendarItem
              task={
                TASK
              }
              priority={
                PRIORITY
              }
              subject={
                SUBJECT
              }
              selected
              onSelect={() => {}}
            />
          </MantineProvider>,
        );

        expect(
          screen.getByRole(
            "button",
            {
              name:
                /View academic task: Research paper/i,
            },
          ),
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );
      },
    );
  },
);