// File: /frontend/features/academic-tasks/components/AcademicTaskCalendarItem.tsx
// Purpose: Renders one compact clickable Academic Task inside
// the Academic Tasks calendar.

"use client";

import {
  Badge,
  Card,
  Group,
  Text,
  UnstyledButton,
} from "@mantine/core";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  formatCalendarTime,
} from "../academic-task-calendar";
import {
  formatAcademicTaskPriorityScore,
  getAcademicTaskPriorityPresentation,
} from "../priority-presentation";
import type {
  AcademicTaskPriorityBreakdown,
  AcademicTaskResponse,
} from "../types";

import classes from "./AcademicTasksWorkspace.module.css";

interface AcademicTaskCalendarItemProps {
  task: AcademicTaskResponse;

  priority:
    AcademicTaskPriorityBreakdown |
    undefined;

  subject:
    SubjectSummary |
    undefined;

  selected: boolean;

  onSelect: (
    task: AcademicTaskResponse,
  ) => void;
}

function getStatusColor(
  status: AcademicTaskResponse["status"],
): string {
  switch (status) {
    case "pending":
      return "yellow";

    case "in_progress":
      return "blue";

    case "completed":
      return "green";

    case "cancelled":
      return "gray";
  }
}

function getStatusLabel(
  status: AcademicTaskResponse["status"],
): string {
  switch (status) {
    case "pending":
      return "Pending";

    case "in_progress":
      return "In progress";

    case "completed":
      return "Completed";

    case "cancelled":
      return "Cancelled";
  }
}

export function AcademicTaskCalendarItem({
  task,
  priority,
  subject,
  selected,
  onSelect,
}: AcademicTaskCalendarItemProps) {
  const completed =
    task.status ===
    "completed";

  const priorityPresentation =
    priority
      ? getAcademicTaskPriorityPresentation(
          priority.total_score,
        )
      : null;

  return (
    <UnstyledButton
      type="button"
      className={
        classes.calendarTaskButton
      }
      aria-label={
        `View academic task: ${task.title}`
      }
      aria-pressed={
        selected
      }
      onClick={() => {
        onSelect(
          task,
        );
      }}
    >
      <Card
        withBorder
        radius="md"
        padding="sm"
        className={[
          classes.calendarTask,

          completed
            ? classes.calendarTaskCompleted
            : "",

          selected
            ? classes.calendarTaskSelected
            : "",
        ]
          .filter(
            Boolean,
          )
          .join(
            " ",
          )}
      >
        <Group
          justify="space-between"
          gap="xs"
          wrap="nowrap"
        >
          <Badge
            size="xs"
            variant="light"
            color={
              completed
                ? "green"
                : priorityPresentation?.color ??
                  getStatusColor(
                    task.status,
                  )
            }
          >
            {completed
              ? "Completed"
              : priorityPresentation?.label ??
                getStatusLabel(
                  task.status,
                )}
          </Badge>

          <Text
            size="xs"
            fw={700}
            c={
              completed
                ? "dimmed"
                : undefined
            }
          >
            {formatCalendarTime(
              task.deadline,
            )}
          </Text>
        </Group>

        <Text
          fw={700}
          size="sm"
          mt="xs"
          lineClamp={2}
          td={
            completed
              ? "line-through"
              : undefined
          }
          c={
            completed
              ? "dimmed"
              : undefined
          }
        >
          {
            task.title
          }
        </Text>

        <Text
          size="xs"
          c="dimmed"
          mt={3}
          lineClamp={1}
        >
          {subject?.name ??
            "Unknown subject"}
        </Text>

        {priority &&
        !completed ? (
          <Text
            size="xs"
            fw={700}
            mt="xs"
            c={
              priorityPresentation?.color
            }
          >
            Priority{" "}
            {formatAcademicTaskPriorityScore(
              priority.total_score,
            )}
          </Text>
        ) : null}
      </Card>
    </UnstyledButton>
  );
}