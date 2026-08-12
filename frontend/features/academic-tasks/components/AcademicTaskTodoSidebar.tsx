// File: /frontend/features/academic-tasks/components/AcademicTaskTodoSidebar.tsx
// Purpose: Displays a compact prioritized Academic Task to-do list
// beside the calendar using backend-owned task ordering.

"use client";

import {
  Badge,
  Card,
  Group,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import {
  IconChecklist,
} from "@tabler/icons-react";
import {
  useMemo,
} from "react";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  formatAcademicTaskPriorityScore,
  getAcademicTaskPriorityPresentation,
} from "../priority-presentation";
import type {
  AcademicTaskPriorityBreakdown,
  AcademicTaskResponse,
} from "../types";

import classes from "./AcademicTasksWorkspace.module.css";

interface AcademicTaskTodoSidebarProps {
  tasks: AcademicTaskResponse[];

  priorityByTaskId: Record<
    string,
    AcademicTaskPriorityBreakdown
  >;

  subjects: SubjectSummary[];

  selectedTaskId:
    string |
    null;

  onTaskSelect: (
    task: AcademicTaskResponse,
  ) => void;
}

function formatTodoDeadline(
  deadline: string,
): string {
  const value =
    new Date(
      deadline,
    );

  if (
    Number.isNaN(
      value.getTime(),
    )
  ) {
    return deadline;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      month:
        "short",

      day:
        "numeric",

      hour:
        "numeric",

      minute:
        "2-digit",
    },
  ).format(
    value,
  );
}

export function AcademicTaskTodoSidebar({
  tasks,
  priorityByTaskId,
  subjects,
  selectedTaskId,
  onTaskSelect,
}: AcademicTaskTodoSidebarProps) {
  const subjectById =
    useMemo(
      () =>
        new Map(
          subjects.map(
            (
              subject,
            ) => [
              subject.id,
              subject,
            ],
          ),
        ),
      [
        subjects,
      ],
    );

  /*
   * `tasks` already follows the ordering returned by the
   * prioritized backend endpoint. Do not sort it again here.
   */
  const activeTasks =
    useMemo(
      () =>
        tasks.filter(
          (
            task,
          ) =>
            task.status !==
              "completed" &&
            task.status !==
              "cancelled",
        ),
      [
        tasks,
      ],
    );

  const completedCount =
    useMemo(
      () =>
        tasks.filter(
          (
            task,
          ) =>
            task.status ===
            "completed",
        ).length,
      [
        tasks,
      ],
    );

  return (
    <Card
      withBorder
      radius="lg"
      padding="lg"
      className={
        classes.todoPanel
      }
    >
      <Stack gap="md">
        <div>
          <Group
            justify="space-between"
            gap="xs"
          >
            <Title
              order={3}
            >
              Priority To-Do
            </Title>

            <Badge
              variant="light"
              color="violet"
            >
              {
                activeTasks.length
              }
            </Badge>
          </Group>

          <Text
            size="sm"
            c="dimmed"
            mt={3}
          >
            What to work on next.
          </Text>
        </div>

        {activeTasks.length ===
        0 ? (
          <Stack
            gap="xs"
            align="center"
            className={
              classes.todoEmptyState
            }
          >
            <IconChecklist
              size={28}
            />

            <Text
              fw={700}
              size="sm"
            >
              Nothing pending
            </Text>

            <Text
              size="xs"
              c="dimmed"
              ta="center"
            >
              You have no active
              academic tasks right now.
            </Text>
          </Stack>
        ) : (
          <Stack
            gap="xs"
          >
            {activeTasks.map(
              (
                task,
                index,
              ) => {
                const priority =
                  priorityByTaskId[
                    task.id
                  ];

                const presentation =
                  priority
                    ? getAcademicTaskPriorityPresentation(
                        priority.total_score,
                      )
                    : null;

                const subject =
                  subjectById.get(
                    task.subject_id,
                  );

                const selected =
                  selectedTaskId ===
                  task.id;

                return (
                  <UnstyledButton
                    key={
                      task.id
                    }
                    type="button"
                    className={[
                      classes.todoTaskButton,

                      selected
                        ? classes.todoTaskButtonSelected
                        : "",
                    ]
                      .filter(
                        Boolean,
                      )
                      .join(
                        " ",
                      )}
                    aria-label={
                      `View to-do task: ${task.title}`
                    }
                    aria-pressed={
                      selected
                    }
                    onClick={() => {
                      onTaskSelect(
                        task,
                      );
                    }}
                  >
                    <Group
                      align="flex-start"
                      wrap="nowrap"
                      gap="sm"
                    >
                      <div
                        className={
                          classes.todoRank
                        }
                      >
                        {
                          index +
                          1
                        }
                      </div>

                      <div
                        className={
                          classes.todoTaskContent
                        }
                      >
                        <Group
                          justify="space-between"
                          gap="xs"
                          wrap="nowrap"
                        >
                          <Text
                            fw={700}
                            size="sm"
                            lineClamp={2}
                          >
                            {
                              task.title
                            }
                          </Text>

                          {presentation ? (
                            <Badge
                              size="xs"
                              variant="light"
                              color={
                                presentation.color
                              }
                            >
                              {
                                presentation.label
                              }
                            </Badge>
                          ) : null}
                        </Group>

                        <Text
                          size="xs"
                          c="dimmed"
                          mt={3}
                          lineClamp={1}
                        >
                          {subject?.name ??
                            "Unknown subject"}
                        </Text>

                        <Group
                          justify="space-between"
                          gap="xs"
                          mt="xs"
                          wrap="nowrap"
                        >
                          <Text
                            size="xs"
                            c="dimmed"
                          >
                            Due{" "}
                            {formatTodoDeadline(
                              task.deadline,
                            )}
                          </Text>

                          {priority ? (
                            <Text
                              size="xs"
                              fw={700}
                              c={
                                presentation?.color
                              }
                            >
                              {formatAcademicTaskPriorityScore(
                                priority.total_score,
                              )}
                            </Text>
                          ) : null}
                        </Group>
                      </div>
                    </Group>
                  </UnstyledButton>
                );
              },
            )}
          </Stack>
        )}

        {completedCount >
        0 ? (
          <Text
            size="xs"
            c="dimmed"
            ta="center"
          >
            {completedCount}{" "}
            {completedCount ===
            1
              ? "completed task"
              : "completed tasks"}
          </Text>
        ) : null}
      </Stack>
    </Card>
  );
}