// File: /frontend/features/academic-tasks/components/AcademicTasksWorkspace.tsx
// Purpose: Displays Academic Tasks in a responsive deadline calendar with a
// prioritized to-do sidebar, task details drawer, CRUD actions,
// status management, and automatic priority recalculation.

"use client";

import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  NumberInput,
  SegmentedControl,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  useDisclosure,
} from "@mantine/hooks";
import {
  modals,
} from "@mantine/modals";
import {
  notifications,
} from "@mantine/notifications";
import {
  IconAlertCircle,
  IconChecklist,
  IconEdit,
  IconFolderOpen,
  IconPlus,
  IconRefresh,
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
  AcademicTaskCalendar,
} from "./AcademicTaskCalendar";
import {
  AcademicTaskDetailsDrawer,
} from "./AcademicTaskDetailsDrawer";
import {
  AcademicTaskTodoSidebar,
} from "./AcademicTaskTodoSidebar";

import classes from "./AcademicTasksWorkspace.module.css";

interface AcademicTasksWorkspaceProps {
  subjects: SubjectSummary[];
}

type PriorityByTaskId =
  Record<
    string,
    AcademicTaskPriorityBreakdownData
  >;

type MobileWorkspaceView =
  | "calendar"
  | "todo";

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

function formatStatusLabel(
  status: AcademicTaskStatus,
): string {
  switch (status) {
    case "pending":
      return "pending";

    case "in_progress":
      return "in progress";

    case "completed":
      return "completed";

    case "cancelled":
      return "cancelled";
  }
}

export function AcademicTasksWorkspace({
  subjects,
}: AcademicTasksWorkspaceProps) {
  const [
    taskModalOpened,
    {
      open:
        openTaskModal,

      close:
        closeTaskModal,
    },
  ] =
    useDisclosure(
      false,
    );

  const [
    tasks,
    setTasks,
  ] =
    useState<
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
  ] =
    useState(
      subjects.length > 0,
    );

  const [
    loadError,
    setLoadError,
  ] =
    useState<
      string | null
    >(
      null,
    );

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
    useState<
      AcademicTaskResponse | null
    >(
      null,
    );

  const [
    selectedTaskId,
    setSelectedTaskId,
  ] =
    useState<
      string | null
    >(
      null,
    );

  const [
    mobileView,
    setMobileView,
  ] =
    useState<MobileWorkspaceView>(
      "calendar",
    );

  const [
    isSaving,
    setIsSaving,
  ] =
    useState(
      false,
    );

  const [
    updatingStatusId,
    setUpdatingStatusId,
  ] =
    useState<
      string | null
    >(
      null,
    );

  const [
    deletingTaskId,
    setDeletingTaskId,
  ] =
    useState<
      string | null
    >(
      null,
    );

  const selectedTask =
    useMemo(
      () =>
        tasks.find(
          (
            task,
          ) =>
            task.id ===
            selectedTaskId,
        ) ??
        null,
      [
        tasks,
        selectedTaskId,
      ],
    );

  const selectedTaskSubject =
    useMemo(
      () => {
        if (
          !selectedTask
        ) {
          return undefined;
        }

        return subjects.find(
          (
            subject,
          ) =>
            subject.id ===
            selectedTask.subject_id,
        );
      },
      [
        selectedTask,
        subjects,
      ],
    );

  const subjectOptions =
    useMemo(
      () =>
        subjects.map(
          (
            subject,
          ) => ({
            value:
              subject.id,

            label:
              subject.name,
          }),
        ),
      [
        subjects,
      ],
    );

  const requestPrioritizedTasks =
    useCallback(
      async () => {
        return await listPrioritizedAcademicTasks({
          limit:
            100,
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
            (
              item,
            ) =>
              item.task,
          ),
        );

        setPriorityByTaskId(
          Object.fromEntries(
            items.map(
              (
                item,
              ) => [
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
      (
        currentPriorities,
      ) => {
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

      setLoadError(
        null,
      );
    } catch {
      if (
        changedTaskId
      ) {
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
    setIsLoading(
      true,
    );

    setLoadError(
      null,
    );

    try {
      const loadedItems =
        await requestPrioritizedTasks();

      applyPrioritizedTasks(
        loadedItems,
      );
    } catch (
      error
    ) {
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
      setIsLoading(
        false,
      );
    }
  }

  useEffect(
    () => {
      if (
        subjects.length ===
        0
      ) {
        return;
      }

      let isActive =
        true;

      void requestPrioritizedTasks()
        .then(
          (
            loadedItems,
          ) => {
            if (
              !isActive
            ) {
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
            error:
              unknown,
          ) => {
            if (
              !isActive
            ) {
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
            if (
              isActive
            ) {
              setIsLoading(
                false,
              );
            }
          },
        );

      return () => {
        isActive =
          false;
      };
    },
    [
      applyPrioritizedTasks,
      requestPrioritizedTasks,
      subjects.length,
    ],
  );

  function handleOpenCreateModal() {
    setEditingTask(
      null,
    );

    setForm(
      createEmptyForm(
        subjects,
      ),
    );

    setFieldErrors(
      {},
    );

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

    setFieldErrors(
      {},
    );

    openTaskModal();
  }

  function handleCloseTaskModal() {
    if (
      isSaving
    ) {
      return;
    }

    closeTaskModal();

    setEditingTask(
      null,
    );

    setForm(
      createEmptyForm(
        subjects,
      ),
    );

    setFieldErrors(
      {},
    );
  }

  async function handleSubmitTask(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const validation =
      validateAcademicTaskForm(
        form,
      );

    if (
      !validation.success
    ) {
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

    setIsSaving(
      true,
    );

    setFieldErrors(
      {},
    );

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
        (
          currentTasks,
        ) => {
          if (
            editingTask
          ) {
            return currentTasks.map(
              (
                task,
              ) =>
                task.id ===
                savedTask.id
                  ? savedTask
                  : task,
            );
          }

          return [
            savedTask,

            ...currentTasks.filter(
              (
                task,
              ) =>
                task.id !==
                savedTask.id,
            ),
          ];
        },
      );

      await refreshPrioritiesAfterMutation(
        savedTask.id,
      );

      setLoadError(
        null,
      );

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

      setEditingTask(
        null,
      );

      setForm(
        createEmptyForm(
          subjects,
        ),
      );
    } catch (
      error
    ) {
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
      setIsSaving(
        false,
      );
    }
  }

  async function handleStatusChange(
    task: AcademicTaskResponse,
    status: AcademicTaskStatus,
  ) {
    if (
      status ===
      task.status
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
            status,
          },
        );

      setTasks(
        (
          currentTasks,
        ) =>
          currentTasks.map(
            (
              currentTask,
            ) =>
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
          `${updatedTask.title} is now ${formatStatusLabel(
            updatedTask.status,
          )}.`,

        color:
          "green",
      });
    } catch (
      error
    ) {
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
        (
          currentTasks,
        ) =>
          currentTasks.filter(
            (
              currentTask,
            ) =>
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

      if (
        selectedTaskId ===
        task.id
      ) {
        setSelectedTaskId(
          null,
        );
      }

      await refreshPrioritiesAfterMutation();

      notifications.show({
        title:
          "Task deleted",

        message:
          `${task.title} was removed from your academic tasks.`,

        color:
          "green",
      });
    } catch (
      error
    ) {
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
        <Text
          size="sm"
        >
          Delete{" "}
          <strong>
            {
              task.title
            }
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

  function handleTaskSelect(
    task: AcademicTaskResponse,
  ) {
    setSelectedTaskId(
      task.id,
    );
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
            fw={
              700
            }
          >
            ACADEMIC TASKS
          </Text>

          <Title
            order={
              1
            }
          >
            Your tasks
          </Title>

          <Text
            c="dimmed"
            maw={
              680
            }
            mt="xs"
          >
            View your academic deadlines
            across the calendar while
            Intelleap keeps their
            deterministic priority scores
            synchronized with your
            workload, confidence,
            available study time, status,
            and previous performance.
          </Text>
        </div>

        <Group
          className={
            classes.headerActions
          }
        >
          <Badge
            size="lg"
            variant="light"
            color="violet"
          >
            {
              tasks.length
            }{" "}
            {tasks.length ===
            1
              ? "task"
              : "tasks"}
          </Badge>

          {subjects.length >
          0 ? (
            <Button
              leftSection={
                <IconPlus
                  size={
                    18
                  }
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

      {subjects.length ===
      0 ? (
        <Card
          withBorder
          radius="lg"
          padding="xl"
          className={
            classes.emptyState
          }
        >
          <ThemeIcon
            size={
              58
            }
            radius="xl"
            variant="light"
          >
            <IconFolderOpen
              size={
                30
              }
            />
          </ThemeIcon>

          <Stack
            gap={
              6
            }
            align="center"
          >
            <Title
              order={
                3
              }
            >
              Create a subject first
            </Title>

            <Text
              c="dimmed"
              ta="center"
              maw={
                460
              }
            >
              Academic tasks belong to
              subjects. Create at least
              one subject before adding
              tasks.
            </Text>
          </Stack>

          <Button
            component={
              Link
            }
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
            gap={
              4
            }
            align="center"
          >
            <Text
              fw={
                700
              }
            >
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
              size={
                20
              }
            />
          }
        >
          <Stack
            gap="sm"
          >
            <Text
              size="sm"
            >
              {
                loadError
              }
            </Text>

            <Button
              variant="light"
              color="red"
              size="xs"
              w="fit-content"
              leftSection={
                <IconRefresh
                  size={
                    16
                  }
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
      ) : tasks.length ===
        0 ? (
        <Card
          withBorder
          radius="lg"
          padding="xl"
          className={
            classes.emptyState
          }
        >
          <ThemeIcon
            size={
              58
            }
            radius="xl"
            variant="light"
          >
            <IconChecklist
              size={
                30
              }
            />
          </ThemeIcon>

          <Stack
            gap={
              6
            }
            align="center"
          >
            <Title
              order={
                3
              }
            >
              No academic tasks yet
            </Title>

            <Text
              c="dimmed"
              ta="center"
              maw={
                460
              }
            >
              Add your assignments,
              projects, exams, readings,
              and other academic work.
            </Text>
          </Stack>

          <Button
            leftSection={
              <IconPlus
                size={
                  18
                }
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
        <div>
          <div
            className={
              classes.mobileWorkspaceToggle
            }
          >
            <SegmentedControl
              fullWidth
              value={
                mobileView
              }
              data={[
                {
                  value:
                    "calendar",

                  label:
                    "Calendar",
                },

                {
                  value:
                    "todo",

                  label:
                    "To-Do",
                },
              ]}
              onChange={(
                value,
              ) => {
                if (
                  value ===
                    "calendar" ||
                  value ===
                    "todo"
                ) {
                  setMobileView(
                    value,
                  );
                }
              }}
            />
          </div>

          <div
            className={
              classes.calendarWorkspace
            }
            data-mobile-view={
              mobileView
            }
          >
            <div
              className={
                classes.calendarWorkspaceCalendar
              }
            >
              <AcademicTaskCalendar
                tasks={
                  tasks
                }
                priorityByTaskId={
                  priorityByTaskId
                }
                subjects={
                  subjects
                }
                selectedTaskId={
                  selectedTaskId
                }
                onTaskSelect={
                  handleTaskSelect
                }
              />
            </div>

            <div
              className={
                classes.calendarWorkspaceTodo
              }
            >
              <AcademicTaskTodoSidebar
                tasks={
                  tasks
                }
                priorityByTaskId={
                  priorityByTaskId
                }
                subjects={
                  subjects
                }
                selectedTaskId={
                  selectedTaskId
                }
                onTaskSelect={
                  handleTaskSelect
                }
              />
            </div>
          </div>
        </div>
      )}

      <AcademicTaskDetailsDrawer
        task={
          selectedTask
        }
        priority={
          selectedTask
            ? priorityByTaskId[
                selectedTask.id
              ]
            : undefined
        }
        subject={
          selectedTaskSubject
        }
        opened={
          selectedTask !==
          null
        }
        statusUpdating={
          selectedTask
            ? updatingStatusId ===
              selectedTask.id
            : false
        }
        deleting={
          selectedTask
            ? deletingTaskId ===
              selectedTask.id
            : false
        }
        onClose={() => {
          setSelectedTaskId(
            null,
          );
        }}
        onEdit={
          handleOpenEditModal
        }
        onStatusChange={(
          task,
          status,
        ) => {
          void handleStatusChange(
            task,
            status,
          );
        }}
        onDelete={
          confirmDeleteTask
        }
      />

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
              onChange={(
                value,
              ) => {
                setForm(
                  (
                    currentForm,
                  ) => ({
                    ...currentForm,

                    subjectId:
                      value ??
                      "",
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
              onChange={(
                event,
              ) => {
                const title =
                  event
                    .currentTarget
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
              onChange={(
                event,
              ) => {
                const description =
                  event
                    .currentTarget
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
              onChange={(
                event,
              ) => {
                const deadline =
                  event
                    .currentTarget
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
              onChange={(
                value,
              ) => {
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
                onChange={(
                  value,
                ) => {
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
                onChange={(
                  value,
                ) => {
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
              description="Choose the main skill needed to complete this task. This helps Intelleap calculate task priority."
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
              onChange={(
                value,
              ) => {
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