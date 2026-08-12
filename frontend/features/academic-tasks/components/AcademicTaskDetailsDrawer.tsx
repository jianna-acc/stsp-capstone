// File: /frontend/features/academic-tasks/components/AcademicTaskDetailsDrawer.tsx
// Purpose: Shows full Academic Task details and actions for a task
// selected from the calendar or prioritized to-do sidebar.

"use client";

import {
  Badge,
  Button,
  Divider,
  Drawer,
  Group,
  NativeSelect,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconCalendarEvent,
  IconChecklist,
  IconClock,
  IconEdit,
  IconTrash,
} from "@tabler/icons-react";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  formatAcademicTaskPriorityScore,
  getAcademicTaskPriorityPresentation,
} from "../priority-presentation";
import type {
  AcademicTaskPriorityBreakdown as AcademicTaskPriorityBreakdownData,
  AcademicTaskResponse,
  AcademicTaskStatus,
} from "../types";

import {
  AcademicTaskPriorityBreakdown,
} from "./AcademicTaskPriorityBreakdown";

interface AcademicTaskDetailsDrawerProps {
  task:
    AcademicTaskResponse |
    null;

  priority:
    AcademicTaskPriorityBreakdownData |
    undefined;

  subject:
    SubjectSummary |
    undefined;

  opened: boolean;

  statusUpdating: boolean;

  deleting: boolean;

  onClose: () => void;

  onEdit: (
    task: AcademicTaskResponse,
  ) => void;

  onStatusChange: (
    task: AcademicTaskResponse,
    status: AcademicTaskStatus,
  ) => void;

  onDelete: (
    task: AcademicTaskResponse,
  ) => void;
}

const STATUS_OPTIONS = [
  {
    value:
      "pending",
    label:
      "Pending",
  },
  {
    value:
      "in_progress",
    label:
      "In progress",
  },
  {
    value:
      "completed",
    label:
      "Completed",
  },
  {
    value:
      "cancelled",
    label:
      "Cancelled",
  },
] as const;

function isAcademicTaskStatus(
  value: string,
): value is AcademicTaskStatus {
  return (
    value === "pending" ||
    value === "in_progress" ||
    value === "completed" ||
    value === "cancelled"
  );
}

function formatDeadline(
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
      weekday:
        "short",

      month:
        "short",

      day:
        "numeric",

      year:
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

function formatEstimatedTime(
  estimatedMinutes: number,
): string {
  if (
    estimatedMinutes <
    60
  ) {
    return `${estimatedMinutes} min`;
  }

  const hours =
    Math.floor(
      estimatedMinutes /
        60,
    );

  const minutes =
    estimatedMinutes %
    60;

  if (
    minutes ===
    0
  ) {
    return `${hours} hr`;
  }

  return `${hours} hr ${minutes} min`;
}

function formatLabel(
  value: string,
): string {
  return value
    .split(
      "_",
    )
    .map(
      (
        part,
      ) =>
        part.charAt(
          0,
        ).toUpperCase() +
        part.slice(
          1,
        ),
    )
    .join(
      " ",
    );
}

function getStatusColor(
  status: AcademicTaskResponse["status"],
): string {
  switch (
    status
  ) {
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

function getDifficultyColor(
  difficulty: AcademicTaskResponse["difficulty"],
): string {
  switch (
    difficulty
  ) {
    case "easy":
      return "green";

    case "medium":
      return "yellow";

    case "hard":
      return "red";
  }
}

export function AcademicTaskDetailsDrawer({
  task,
  priority,
  subject,
  opened,
  statusUpdating,
  deleting,
  onClose,
  onEdit,
  onStatusChange,
  onDelete,
}: AcademicTaskDetailsDrawerProps) {
  const priorityPresentation =
    priority
      ? getAcademicTaskPriorityPresentation(
          priority.total_score,
        )
      : null;

  return (
    <Drawer
      opened={
        opened
      }
      onClose={
        onClose
      }
      position="right"
      size="md"
      title="Academic task details"
      padding="lg"
    >
      {task ? (
        <Stack
          gap="lg"
        >
          <Group
            align="flex-start"
            justify="space-between"
            wrap="nowrap"
          >
            <Group
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                color={
                  subject?.color ??
                  "violet"
                }
                variant="light"
                size={
                  44
                }
                radius="md"
              >
                <IconChecklist
                  size={
                    23
                  }
                />
              </ThemeIcon>

              <div>
                <Text
                  size="xs"
                  fw={
                    700
                  }
                  c="dimmed"
                  tt="uppercase"
                >
                  {subject?.name ??
                    "Academic task"}
                </Text>

                <Title
                  order={
                    3
                  }
                  mt={
                    2
                  }
                >
                  {
                    task.title
                  }
                </Title>
              </div>
            </Group>

            <Badge
              variant="light"
              color={
                getStatusColor(
                  task.status,
                )
              }
            >
              {formatLabel(
                task.status,
              )}
            </Badge>
          </Group>

          {priority &&
          priorityPresentation ? (
            <Paper
              withBorder
              radius="md"
              p="md"
            >
              <Stack
                gap="sm"
              >
                <Group
                  justify="space-between"
                  gap="sm"
                >
                  <Badge
                    variant="light"
                    color={
                      priorityPresentation.color
                    }
                  >
                    {
                      priorityPresentation.label
                    }
                  </Badge>

                  <Text
                    fw={
                      700
                    }
                    size="sm"
                  >
                    Priority{" "}
                    {formatAcademicTaskPriorityScore(
                      priority.total_score,
                    )}
                  </Text>
                </Group>

                <Progress
                  value={
                    priority.total_score
                  }
                  color={
                    priorityPresentation.color
                  }
                  radius="xl"
                  size="sm"
                  aria-label={
                    `Priority score for ${task.title}`
                  }
                />

                <AcademicTaskPriorityBreakdown
                  taskTitle={
                    task.title
                  }
                  priority={
                    priority
                  }
                />
              </Stack>
            </Paper>
          ) : (
            <Text
              size="sm"
              c="dimmed"
            >
              Priority is being
              recalculated.
            </Text>
          )}

          <Divider />

          <Stack
            gap="sm"
          >
            <Group
              gap={
                8
              }
              wrap="nowrap"
            >
              <IconCalendarEvent
                size={
                  18
                }
              />

              <div>
                <Text
                  size="xs"
                  c="dimmed"
                >
                  Deadline
                </Text>

                <Text
                  size="sm"
                  fw={
                    600
                  }
                >
                  {formatDeadline(
                    task.deadline,
                  )}
                </Text>
              </div>
            </Group>

            <Group
              gap={
                8
              }
              wrap="nowrap"
            >
              <IconClock
                size={
                  18
                }
              />

              <div>
                <Text
                  size="xs"
                  c="dimmed"
                >
                  Estimated time
                </Text>

                <Text
                  size="sm"
                  fw={
                    600
                  }
                >
                  {formatEstimatedTime(
                    task.estimated_minutes,
                  )}
                </Text>
              </div>
            </Group>
          </Stack>

          <SimpleGrid
            cols={{
              base:
                1,

              xs:
                2,
            }}
          >
            <Paper
              withBorder
              radius="md"
              p="sm"
            >
              <Text
                size="xs"
                c="dimmed"
              >
                Difficulty
              </Text>

              <Badge
                mt={
                  5
                }
                variant="light"
                color={
                  getDifficultyColor(
                    task.difficulty,
                  )
                }
              >
                {formatLabel(
                  task.difficulty,
                )}
              </Badge>
            </Paper>

            <Paper
              withBorder
              radius="md"
              p="sm"
            >
              <Text
                size="xs"
                c="dimmed"
              >
                Task type
              </Text>

              <Text
                fw={
                  600
                }
                size="sm"
                mt={
                  5
                }
              >
                {formatLabel(
                  task.task_type,
                )}
              </Text>
            </Paper>

            <Paper
              withBorder
              radius="md"
              p="sm"
            >
              <Text
                size="xs"
                c="dimmed"
              >
                Output type
              </Text>

              <Text
                fw={
                  600
                }
                size="sm"
                mt={
                  5
                }
              >
                {formatLabel(
                  task.output_type,
                )}
              </Text>
            </Paper>

            <Paper
              withBorder
              radius="md"
              p="sm"
            >
              <Text
                size="xs"
                c="dimmed"
              >
                Subject
              </Text>

              <Text
                fw={
                  600
                }
                size="sm"
                mt={
                  5
                }
              >
                {subject?.name ??
                  "Unknown subject"}
              </Text>
            </Paper>
          </SimpleGrid>

          <div>
            <Text
              fw={
                700
              }
              size="sm"
            >
              Description
            </Text>

            <Text
              size="sm"
              c={
                task.description
                  ? undefined
                  : "dimmed"
              }
              mt="xs"
              style={{
                whiteSpace:
                  "pre-wrap",
              }}
            >
              {task.description ??
                "No description provided."}
            </Text>
          </div>

          <Divider />

          <NativeSelect
            label="Status"
            aria-label={
              `Status for ${task.title}`
            }
            data={[
              ...STATUS_OPTIONS,
            ]}
            value={
              task.status
            }
            disabled={
              statusUpdating ||
              deleting
            }
            onChange={(
              event,
            ) => {
              const value =
                event
                  .currentTarget
                  .value;

              if (
                !isAcademicTaskStatus(
                  value,
                ) ||
                value ===
                  task.status
              ) {
                return;
              }

              onStatusChange(
                task,
                value,
              );
            }}
          />

          <Group
            grow
          >
            <Button
              variant="light"
              leftSection={
                <IconEdit
                  size={
                    17
                  }
                />
              }
              disabled={
                statusUpdating ||
                deleting
              }
              onClick={() => {
                onEdit(
                  task,
                );
              }}
            >
              Edit task
            </Button>

            <Button
              variant="light"
              color="red"
              loading={
                deleting
              }
              disabled={
                statusUpdating
              }
              leftSection={
                <IconTrash
                  size={
                    17
                  }
                />
              }
              onClick={() => {
                onDelete(
                  task,
                );
              }}
            >
              Delete task
            </Button>
          </Group>
        </Stack>
      ) : null}
    </Drawer>
  );
}