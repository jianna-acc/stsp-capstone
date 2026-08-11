// File: /frontend/features/academic-tasks/components/AcademicTasksWorkspace.tsx
// Purpose: Displays prioritized Academic Tasks and supports
// create, edit, status, delete, and automatic priority recalculation.

"use client";

import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  NativeSelect,
  NumberInput,
  Progress,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import {
  IconAlertCircle,
  IconCalendarEvent,
  IconChecklist,
  IconClock,
  IconEdit,
  IconFolderOpen,
  IconPlus,
  IconRefresh,
  IconTrash,
} from "@tabler/icons-react";
import Link from "next/link";
import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  AcademicTaskApiError,
  createAcademicTask,
  deleteAcademicTask,
  listPrioritizedAcademicTasks,
  updateAcademicTask,
  updateAcademicTaskStatus,
} from "../api";
import {
  academicTaskToFormValues,
} from "../form";
import {
  formatAcademicTaskPriorityScore,
  getAcademicTaskPriorityPresentation,
} from "../priority-presentation";
import type {
  AcademicTaskPriorityBreakdown as AcademicTaskPriorityBreakdownData,
  AcademicTaskPriorityResponse,
  AcademicTaskResponse,
  AcademicTaskStatus,
} from "../types";
import {
  ACADEMIC_TASK_DIFFICULTY_OPTIONS,
  ACADEMIC_TASK_OUTPUT_TYPE_OPTIONS,
  ACADEMIC_TASK_TYPE_OPTIONS,
  EMPTY_ACADEMIC_TASK_FORM,
  type AcademicTaskFieldErrors,
  type AcademicTaskFormValues,
  validateAcademicTaskForm,
} from "../validation";

import {
  AcademicTaskPriorityBreakdown,
} from "./AcademicTaskPriorityBreakdown";

import classes from "./AcademicTasksWorkspace.module.css";

interface AcademicTasksWorkspaceProps {
  subjects: SubjectSummary[];
}

type PriorityByTaskId =
  Record<
    string,
    AcademicTaskPriorityBreakdownData
  >;

const ACADEMIC_TASK_STATUS_OPTIONS = [
  {
    value: "pending",
    label: "Pending",
  },
  {
    value: "in_progress",
    label: "In progress",
  },
  {
    value: "completed",
    label: "Completed",
  },
  {
    value: "cancelled",
    label: "Cancelled",
  },
] as const;

function formatDeadline(
  deadline: string,
): string {
  const date =
    new Date(deadline);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return deadline;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(date);
}

function formatEstimatedTime(
  estimatedMinutes: number,
): string {
  if (
    estimatedMinutes < 60
  ) {
    return `${estimatedMinutes} min`;
  }

  const hours =
    Math.floor(
      estimatedMinutes / 60,
    );

  const minutes =
    estimatedMinutes % 60;

  if (minutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${minutes} min`;
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

function getDifficultyColor(
  difficulty: AcademicTaskResponse["difficulty"],
): string {
  switch (difficulty) {
    case "easy":
      return "green";

    case "medium":
      return "yellow";

    case "hard":
      return "red";
  }
}

function createEmptyForm(
  subjects: SubjectSummary[],
): AcademicTaskFormValues {
  return {
    ...EMPTY_ACADEMIC_TASK_FORM,

    subjectId:
      subjects.length === 1
        ? subjects[0].id
        : "",
  };
}

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

export function AcademicTasksWorkspace({
  subjects,
}: AcademicTasksWorkspaceProps) {
  const [
    taskModalOpened,
    {
      open: openTaskModal,
      close: closeTaskModal,
    },
  ] = useDisclosure(false);

  const [
    tasks,
    setTasks,
  ] = useState<
    AcademicTaskResponse[]
  >([]);

  const [
    priorityByTaskId,
    setPriorityByTaskId,
  ] =
    useState<PriorityByTaskId>(
      {},
    );

  const [
    isLoading,
    setIsLoading,
  ] = useState(
    subjects.length > 0,
  );

  const [
    loadError,
    setLoadError,
  ] = useState<
    string | null
  >(null);

  const [
    form,
    setForm,
  ] =
    useState<AcademicTaskFormValues>(
      () =>
        createEmptyForm(
          subjects,
        ),
    );

  const [
    fieldErrors,
    setFieldErrors,
  ] =
    useState<AcademicTaskFieldErrors>(
      {},
    );

  const [
    editingTask,
    setEditingTask,
  ] =
    useState<AcademicTaskResponse | null>(
      null,
    );

  const [
    isSaving,
    setIsSaving,
  ] = useState(false);

  const [
    updatingStatusId,
    setUpdatingStatusId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    deletingTaskId,
    setDeletingTaskId,
  ] =
    useState<string | null>(
      null,
    );

  const subjectById =
    useMemo(
      () =>
        new Map(
          subjects.map(
            (subject) => [
              subject.id,
              subject,
            ],
          ),
        ),
      [subjects],
    );

  const subjectOptions =
    useMemo(
      () =>
        subjects.map(
          (subject) => ({
            value:
              subject.id,
            label:
              subject.name,
          }),
        ),
      [subjects],
    );

  const requestPrioritizedTasks =
    useCallback(
      async () => {
        return await listPrioritizedAcademicTasks({
          limit: 100,
        });
      },
      [],
    );

  const applyPrioritizedTasks =
    useCallback(
      (
        items:
          AcademicTaskPriorityResponse[],
      ) => {
        setTasks(
          items.map(
            (item) =>
              item.task,
          ),
        );

        setPriorityByTaskId(
          Object.fromEntries(
            items.map(
              (item) => [
                item.task.id,
                item.priority,
              ],
            ),
          ),
        );
      },
      [],
    );

  function clearPriorityForTask(
    taskId: string,
  ) {
    setPriorityByTaskId(
      (currentPriorities) => {
        const nextPriorities = {
          ...currentPriorities,
        };

        delete nextPriorities[
          taskId
        ];

        return nextPriorities;
      },
    );
  }

  async function refreshPrioritiesAfterMutation(
    changedTaskId?: string,
  ) {
    try {
      const refreshedItems =
        await requestPrioritizedTasks();

      applyPrioritizedTasks(
        refreshedItems,
      );

      setLoadError(null);
    } catch {
      if (changedTaskId) {
        clearPriorityForTask(
          changedTaskId,
        );
      }

      notifications.show({
        title:
          "Priority refresh delayed",

        message:
          "The task was saved, but its priority could not be recalculated right now.",

        color:
          "yellow",
      });
    }
  }

  async function retryLoadTasks() {
    setIsLoading(true);
    setLoadError(null);

    try {
      const loadedItems =
        await requestPrioritizedTasks();

      applyPrioritizedTasks(
        loadedItems,
      );
    } catch (error) {
      if (
        error instanceof
        AcademicTaskApiError
      ) {
        setLoadError(
          error.message,
        );
      } else {
        setLoadError(
          "Your academic tasks could not be loaded.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(
    () => {
      if (
        subjects.length === 0
      ) {
        return;
      }

      let isActive = true;

      void requestPrioritizedTasks()
        .then(
          (loadedItems) => {
            if (!isActive) {
              return;
            }

            applyPrioritizedTasks(
              loadedItems,
            );

            setLoadError(
              null,
            );
          },
        )
        .catch(
          (
            error: unknown,
          ) => {
            if (!isActive) {
              return;
            }

            if (
              error instanceof
              AcademicTaskApiError
            ) {
              setLoadError(
                error.message,
              );
            } else {
              setLoadError(
                "Your academic tasks could not be loaded.",
              );
            }
          },
        )
        .finally(
          () => {
            if (isActive) {
              setIsLoading(
                false,
              );
            }
          },
        );

      return () => {
        isActive = false;
      };
    },
    [
      applyPrioritizedTasks,
      requestPrioritizedTasks,
      subjects.length,
    ],
  );

  function handleOpenCreateModal() {
    setEditingTask(null);

    setForm(
      createEmptyForm(
        subjects,
      ),
    );

    setFieldErrors({});
    openTaskModal();
  }

  function handleOpenEditModal(
    task: AcademicTaskResponse,
  ) {
    setEditingTask(
      task,
    );

    setForm(
      academicTaskToFormValues(
        task,
      ),
    );

    setFieldErrors({});
    openTaskModal();
  }

  function handleCloseTaskModal() {
    if (isSaving) {
      return;
    }

    closeTaskModal();

    setEditingTask(null);

    setForm(
      createEmptyForm(
        subjects,
      ),
    );

    setFieldErrors({});
  }

  async function handleSubmitTask(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const validation =
      validateAcademicTaskForm(
        form,
      );

    if (!validation.success) {
      setFieldErrors(
        validation.fieldErrors,
      );

      notifications.show({
        title:
          editingTask
            ? "Task not updated"
            : "Task not created",

        message:
          "Check the highlighted task details.",

        color:
          "red",
      });

      return;
    }

    setIsSaving(true);
    setFieldErrors({});

    try {
      const savedTask =
        editingTask
          ? await updateAcademicTask(
              editingTask.id,
              validation.data,
            )
          : await createAcademicTask(
              validation.data,
            );

      setTasks(
        (currentTasks) => {
          if (editingTask) {
            return currentTasks.map(
              (task) =>
                task.id ===
                savedTask.id
                  ? savedTask
                  : task,
            );
          }

          return [
            savedTask,

            ...currentTasks.filter(
              (task) =>
                task.id !==
                savedTask.id,
            ),
          ];
        },
      );

      await refreshPrioritiesAfterMutation(
        savedTask.id,
      );

      setLoadError(null);

      notifications.show({
        title:
          editingTask
            ? "Task updated"
            : "Task created",

        message:
          editingTask
            ? `${savedTask.title} was updated.`
            : `${savedTask.title} was added to your academic tasks.`,

        color:
          "green",
      });

      closeTaskModal();

      setEditingTask(null);

      setForm(
        createEmptyForm(
          subjects,
        ),
      );
    } catch (error) {
      const message =
        error instanceof
        AcademicTaskApiError
          ? error.message
          : editingTask
            ? "The academic task could not be updated."
            : "The academic task could not be created.";

      notifications.show({
        title:
          editingTask
            ? "Task not updated"
            : "Task not created",

        message,

        color:
          "red",
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleStatusChange(
    task: AcademicTaskResponse,
    value: string | null,
  ) {
    if (
      !value ||
      !isAcademicTaskStatus(
        value,
      ) ||
      value === task.status
    ) {
      return;
    }

    setUpdatingStatusId(
      task.id,
    );

    try {
      const updatedTask =
        await updateAcademicTaskStatus(
          task.id,
          {
            status:
              value,
          },
        );

      setTasks(
        (currentTasks) =>
          currentTasks.map(
            (currentTask) =>
              currentTask.id ===
              updatedTask.id
                ? updatedTask
                : currentTask,
          ),
      );

      await refreshPrioritiesAfterMutation(
        updatedTask.id,
      );

      notifications.show({
        title:
          "Task status updated",

        message:
          `${updatedTask.title} is now ${getStatusLabel(
            updatedTask.status,
          ).toLowerCase()}.`,

        color:
          "green",
      });
    } catch (error) {
      const message =
        error instanceof
        AcademicTaskApiError
          ? error.message
          : "The task status could not be updated.";

      notifications.show({
        title:
          "Status not updated",

        message,

        color:
          "red",
      });
    } finally {
      setUpdatingStatusId(
        null,
      );
    }
  }

  async function executeDeleteTask(
    task: AcademicTaskResponse,
  ) {
    setDeletingTaskId(
      task.id,
    );

    try {
      await deleteAcademicTask(
        task.id,
      );

      setTasks(
        (currentTasks) =>
          currentTasks.filter(
            (currentTask) =>
              currentTask.id !==
              task.id,
          ),
      );

      setPriorityByTaskId(
        (
          currentPriorities,
        ) => {
          const nextPriorities = {
            ...currentPriorities,
          };

          delete nextPriorities[
            task.id
          ];

          return nextPriorities;
        },
      );

      await refreshPrioritiesAfterMutation();

      notifications.show({
        title:
          "Task deleted",

        message:
          `${task.title} was removed from your academic tasks.`,

        color:
          "green",
      });
    } catch (error) {
      const message =
        error instanceof
        AcademicTaskApiError
          ? error.message
          : "The academic task could not be deleted.";

      notifications.show({
        title:
          "Task not deleted",

        message,

        color:
          "red",
      });
    } finally {
      setDeletingTaskId(
        null,
      );
    }
  }

  function confirmDeleteTask(
    task: AcademicTaskResponse,
  ) {
    modals.openConfirmModal({
      title:
        "Delete academic task?",

      centered:
        true,

      children: (
        <Text size="sm">
          Delete{" "}
          <strong>
            {task.title}
          </strong>
          ? This action cannot be
          undone.
        </Text>
      ),

      labels: {
        confirm:
          "Delete task",

        cancel:
          "Keep task",
      },

      confirmProps: {
        color:
          "red",
      },

      onConfirm: () => {
        void executeDeleteTask(
          task,
        );
      },
    });
  }

  return (
    <main
      className={
        classes.page
      }
    >
      <div
        className={
          classes.header
        }
      >
        <div>
          <Text
            className={
              classes.eyebrow
            }
            fw={700}
          >
            ACADEMIC TASKS
          </Text>

          <Title order={1}>
            Your tasks
          </Title>

          <Text
            c="dimmed"
            maw={680}
            mt="xs"
          >
            Tasks are ordered using your
            deterministic priority score,
            which considers deadline,
            difficulty, workload,
            confidence, available study
            time, status, and previous
            performance.
          </Text>
        </div>

        <Group>
          <Badge
            size="lg"
            variant="light"
            color="violet"
          >
            {tasks.length}{" "}
            {tasks.length === 1
              ? "task"
              : "tasks"}
          </Badge>

          {subjects.length > 0 ? (
            <Button
              leftSection={
                <IconPlus
                  size={18}
                />
              }
              onClick={
                handleOpenCreateModal
              }
            >
              Create task
            </Button>
          ) : null}
        </Group>
      </div>

      {subjects.length === 0 ? (
        <Card
          withBorder
          radius="lg"
          padding="xl"
          className={
            classes.emptyState
          }
        >
          <ThemeIcon
            size={58}
            radius="xl"
            variant="light"
          >
            <IconFolderOpen
              size={30}
            />
          </ThemeIcon>

          <Stack
            gap={6}
            align="center"
          >
            <Title order={3}>
              Create a subject first
            </Title>

            <Text
              c="dimmed"
              ta="center"
              maw={460}
            >
              Academic tasks belong to
              subjects. Create at least
              one subject before adding
              tasks.
            </Text>
          </Stack>

          <Button
            component={Link}
            href="/subjects"
          >
            Open subjects
          </Button>
        </Card>
      ) : isLoading ? (
        <Card
          withBorder
          radius="lg"
          padding="xl"
          className={
            classes.emptyState
          }
        >
          <Loader />

          <Stack
            gap={4}
            align="center"
          >
            <Text fw={700}>
              Prioritizing your tasks
            </Text>

            <Text
              c="dimmed"
              size="sm"
            >
              Calculating your current
              academic workload.
            </Text>
          </Stack>
        </Card>
      ) : loadError ? (
        <Alert
          color="red"
          radius="lg"
          title="Tasks could not be loaded"
          icon={
            <IconAlertCircle
              size={20}
            />
          }
        >
          <Stack gap="sm">
            <Text size="sm">
              {loadError}
            </Text>

            <Button
              variant="light"
              color="red"
              size="xs"
              w="fit-content"
              leftSection={
                <IconRefresh
                  size={16}
                />
              }
              onClick={() => {
                void retryLoadTasks();
              }}
            >
              Try again
            </Button>
          </Stack>
        </Alert>
      ) : tasks.length === 0 ? (
        <Card
          withBorder
          radius="lg"
          padding="xl"
          className={
            classes.emptyState
          }
        >
          <ThemeIcon
            size={58}
            radius="xl"
            variant="light"
          >
            <IconChecklist
              size={30}
            />
          </ThemeIcon>

          <Stack
            gap={6}
            align="center"
          >
            <Title order={3}>
              No academic tasks yet
            </Title>

            <Text
              c="dimmed"
              ta="center"
              maw={460}
            >
              Add your assignments,
              projects, exams, readings,
              and other academic work.
            </Text>
          </Stack>

          <Button
            leftSection={
              <IconPlus
                size={18}
              />
            }
            onClick={
              handleOpenCreateModal
            }
          >
            Create first task
          </Button>
        </Card>
      ) : (
        <div
          className={
            classes.taskGrid
          }
        >
          {[0, 1].map(
            (columnIndex) => (
              <div
                key={
                  columnIndex
                }
                className={
                  classes.taskColumn
                }
              >
                {tasks.map(
                  (
                    task,
                    taskIndex,
                  ) => {
                    if (
                      taskIndex % 2 !==
                      columnIndex
                    ) {
                      return null;
                    }

                    const subject =
                      subjectById.get(
                        task.subject_id,
                      );

                    const priority =
                      priorityByTaskId[
                        task.id
                      ];

                    const priorityPresentation =
                      priority
                        ? getAcademicTaskPriorityPresentation(
                            priority.total_score,
                          )
                        : null;

                    const statusUpdating =
                      updatingStatusId ===
                        task.id;

                    const deleting =
                      deletingTaskId ===
                        task.id;

                    return (
                      <Card
                        key={
                          task.id
                        }
                        withBorder
                        radius="lg"
                        padding="lg"
                        className={
                          classes.taskCard
                        }
                        style={{
                          order:
                            taskIndex,
                        }}
                      >
                        <Stack gap="md">
                          <Group
                            justify="space-between"
                            align="flex-start"
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
                                size={
                                  42
                                }
                                radius="md"
                                variant="light"
                              >
                                <IconChecklist
                                  size={
                                    22
                                  }
                                />
                              </ThemeIcon>

                              <div>
                                <Text
                                  fw={
                                    700
                                  }
                                  size="lg"
                                >
                                  {
                                    task.title
                                  }
                                </Text>

                                <Text
                                  c="dimmed"
                                  size="sm"
                                >
                                  {subject?.name ??
                                    "Unknown subject"}
                                </Text>
                              </div>
                            </Group>

                            <Badge
                              color={
                                getStatusColor(
                                  task.status,
                                )
                              }
                              variant="light"
                            >
                              {getStatusLabel(
                                task.status,
                              )}
                            </Badge>
                          </Group>

                          {priority &&
                          priorityPresentation ? (
                            <Stack gap="xs">
                              <Group
                                justify="space-between"
                                gap="xs"
                              >
                                <Badge
                                  color={
                                    priorityPresentation.color
                                  }
                                  variant="light"
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
                                size="sm"
                                radius="xl"
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
                          ) : (
                            <Text
                              c="dimmed"
                              size="sm"
                            >
                              Priority will
                              be recalculated
                              shortly.
                            </Text>
                          )}

                          {task.description ? (
                            <Text
                              c="dimmed"
                              size="sm"
                              lineClamp={
                                2
                              }
                            >
                              {
                                task.description
                              }
                            </Text>
                          ) : null}

                          <Group gap="xs">
                            <Badge
                              variant="outline"
                              color={
                                getDifficultyColor(
                                  task.difficulty,
                                )
                              }
                              tt="capitalize"
                            >
                              {
                                task.difficulty
                              }
                            </Badge>

                            <Badge
                              variant="outline"
                              color="gray"
                              tt="capitalize"
                            >
                              {
                                task.task_type
                              }
                            </Badge>
                          </Group>

                          <div
                            className={
                              classes.taskMeta
                            }
                          >
                            <Group
                              gap={
                                7
                              }
                              wrap="nowrap"
                            >
                              <IconCalendarEvent
                                size={
                                  17
                                }
                              />

                              <Text
                                size="sm"
                                c="dimmed"
                              >
                                {formatDeadline(
                                  task.deadline,
                                )}
                              </Text>
                            </Group>

                            <Group
                              gap={
                                7
                              }
                              wrap="nowrap"
                            >
                              <IconClock
                                size={
                                  17
                                }
                              />

                              <Text
                                size="sm"
                                c="dimmed"
                              >
                                {formatEstimatedTime(
                                  task.estimated_minutes,
                                )}
                              </Text>
                            </Group>
                          </div>

                          <NativeSelect
                            label="Status"
                            aria-label={
                              `Status for ${task.title}`
                            }
                            data={[
                              ...ACADEMIC_TASK_STATUS_OPTIONS,
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
                              void handleStatusChange(
                                task,
                                event
                                  .currentTarget
                                  .value,
                              );
                            }}
                          />

                          <Group grow>
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
                                handleOpenEditModal(
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
                                confirmDeleteTask(
                                  task,
                                );
                              }}
                            >
                              Delete task
                            </Button>
                          </Group>
                        </Stack>
                      </Card>
                    );
                  },
                )}
              </div>
            ),
          )}
        </div>
      )}

      <Modal
        opened={
          taskModalOpened
        }
        onClose={
          handleCloseTaskModal
        }
        title={
          editingTask
            ? "Edit academic task"
            : "Create academic task"
        }
        centered
        radius="lg"
        size="lg"
        closeOnClickOutside={
          !isSaving
        }
        closeOnEscape={
          !isSaving
        }
      >
        <form
          onSubmit={
            handleSubmitTask
          }
        >
          <Stack>
            <Select
              label="Subject"
              description="Choose the subject this task belongs to."
              placeholder="Select a subject"
              data={
                subjectOptions
              }
              value={
                form.subjectId
              }
              error={
                fieldErrors.subjectId
              }
              searchable
              required
              disabled={
                isSaving
              }
              onChange={(value) => {
                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,

                    subjectId:
                      value ?? "",
                  }),
                );
              }}
            />

            <TextInput
              label="Task title"
              description="For example: Final research paper or Chapter 5 quiz."
              placeholder="Enter task title"
              value={
                form.title
              }
              error={
                fieldErrors.title
              }
              maxLength={
                200
              }
              required
              disabled={
                isSaving
              }
              onChange={(event) => {
                const title =
                  event.currentTarget
                    .value;

                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,
                    title,
                  }),
                );
              }}
            />

            <Textarea
              label="Description"
              description="Optional notes or instructions for this task."
              placeholder="Add task details"
              value={
                form.description
              }
              error={
                fieldErrors.description
              }
              maxLength={
                5000
              }
              autosize
              minRows={
                3
              }
              disabled={
                isSaving
              }
              onChange={(event) => {
                const description =
                  event.currentTarget
                    .value;

                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,
                    description,
                  }),
                );
              }}
            />

            <TextInput
              type="datetime-local"
              label="Deadline"
              description="Choose the date and time when this task is due."
              value={
                form.deadline
              }
              error={
                fieldErrors.deadline
              }
              required
              disabled={
                isSaving
              }
              onChange={(event) => {
                const deadline =
                  event.currentTarget
                    .value;

                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,
                    deadline,
                  }),
                );
              }}
            />

            <NumberInput
              label="Estimated completion time"
              description="Enter the estimated number of minutes required."
              value={
                form.estimatedMinutes
              }
              error={
                fieldErrors.estimatedMinutes
              }
              min={
                1
              }
              max={
                10080
              }
              allowDecimal={
                false
              }
              required
              disabled={
                isSaving
              }
              onChange={(value) => {
                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,

                    estimatedMinutes:
                      value,
                  }),
                );
              }}
            />

            <SimpleGrid
              cols={{
                base:
                  1,

                sm:
                  2,
              }}
            >
              <Select
                label="Difficulty"
                data={[
                  ...ACADEMIC_TASK_DIFFICULTY_OPTIONS,
                ]}
                value={
                  form.difficulty
                }
                error={
                  fieldErrors.difficulty
                }
                allowDeselect={
                  false
                }
                required
                disabled={
                  isSaving
                }
                onChange={(value) => {
                  setForm(
                    (
                      currentForm,
                    ) => ({
                      ...currentForm,

                      difficulty:
                        (
                          value ??
                          ""
                        ) as AcademicTaskFormValues["difficulty"],
                    }),
                  );
                }}
              />

              <Select
                label="Task type"
                data={[
                  ...ACADEMIC_TASK_TYPE_OPTIONS,
                ]}
                value={
                  form.taskType
                }
                error={
                  fieldErrors.taskType
                }
                allowDeselect={
                  false
                }
                required
                disabled={
                  isSaving
                }
                onChange={(value) => {
                  setForm(
                    (
                      currentForm,
                    ) => ({
                      ...currentForm,

                      taskType:
                        (
                          value ??
                          ""
                        ) as AcademicTaskFormValues["taskType"],
                    }),
                  );
                }}
              />
            </SimpleGrid>

            <Select
              label="Academic output type"
              description="Choose the main skill needed to complete this task. This helps STUDY AI calculate task priority."
              data={[
                ...ACADEMIC_TASK_OUTPUT_TYPE_OPTIONS,
              ]}
              value={
                form.outputType
              }
              error={
                fieldErrors.outputType
              }
              allowDeselect={
                false
              }
              required
              disabled={
                isSaving
              }
              onChange={(value) => {
                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,

                    outputType:
                      (
                        value ??
                        ""
                      ) as AcademicTaskFormValues["outputType"],
                  }),
                );
              }}
            />

            <Group
              justify="flex-end"
              mt="sm"
            >
              <Button
                variant="default"
                disabled={
                  isSaving
                }
                onClick={
                  handleCloseTaskModal
                }
              >
                Cancel
              </Button>

              <Button
                type="submit"
                loading={
                  isSaving
                }
                leftSection={
                  editingTask ? (
                    <IconEdit
                      size={
                        17
                      }
                    />
                  ) : (
                    <IconPlus
                      size={
                        17
                      }
                    />
                  )
                }
              >
                {editingTask
                  ? "Save changes"
                  : "Create task"}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </main>
  );
}