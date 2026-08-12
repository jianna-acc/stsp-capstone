// File: /frontend/features/dashboard/components/DashboardWorkspace.tsx
// Purpose: Renders the authenticated student command-center
// Dashboard using existing feature APIs and navigation routes.

"use client";

import Link from "next/link";

import type {
  ReactNode,
} from "react";

import {
  Alert,
  Badge,
  Button,
  Container,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";

import {
  IconAlertCircle,
  IconBooks,
  IconCalendarTime,
  IconChartBar,
  IconChecklist,
  IconMessageCircle,
  IconRefresh,
  IconUserEdit,
} from "@tabler/icons-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  listPrioritizedAcademicTasks,
} from "@/features/academic-tasks/api";

import {
  getAcademicTaskPriorityPresentation,
} from "@/features/academic-tasks/priority-presentation";

import type {
  AcademicTaskPriorityResponse,
} from "@/features/academic-tasks/types";

import {
  getAnalyticsOverview,
} from "@/features/analytics/api";

import type {
  AnalyticsCountMetric,
  AnalyticsMetric,
  AnalyticsOverviewResponse,
} from "@/features/analytics/types";

import {
  selectNextStudySession,
} from "@/features/dashboard/dashboard-data";

import type {
  DashboardStudySessionCandidate,
} from "@/features/dashboard/dashboard-data";

import {
  listStudyPlans,
  listStudySessions,
} from "@/features/study-plans/api";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import styles from "./DashboardWorkspace.module.css";


const PRIORITY_TASK_LIMIT = 5;


interface DashboardWorkspaceProps {
  displayName: string;
  subjects: SubjectSummary[];
}


interface QuickAction {
  title: string;
  href: string;
  icon: ReactNode;
}


const QUICK_ACTIONS: readonly QuickAction[] = [
  {
    title: "Academic Tasks",
    href: "/academic-tasks",
    icon: (
      <IconChecklist
        size={17}
      />
    ),
  },
  {
    title: "Study Plan",
    href: "/study-plan",
    icon: (
      <IconCalendarTime
        size={17}
      />
    ),
  },
  {
    title: "Study Assistant",
    href: "/study-assistant",
    icon: (
      <IconMessageCircle
        size={17}
      />
    ),
  },
  {
    title: "Flashcards",
    href: "/flashcards",
    icon: (
      <IconBooks
        size={17}
      />
    ),
  },
  {
    title: "Quizzes",
    href: "/quizzes",
    icon: (
      <IconChartBar
        size={17}
      />
    ),
  },
  {
    title: "Subjects",
    href: "/subjects",
    icon: (
      <IconBooks
        size={17}
      />
    ),
  },
];


function formatDeadline(
  value: string,
): string {
  const deadline =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      deadline.getTime(),
    )
  ) {
    return "Deadline unavailable";
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
  ).format(
    deadline,
  );
}


function formatStudySessionSchedule(
  startsAt: string,
  endsAt: string,
): string {
  const start =
    new Date(
      startsAt,
    );

  const end =
    new Date(
      endsAt,
    );

  if (
    Number.isNaN(
      start.getTime(),
    ) ||
    Number.isNaN(
      end.getTime(),
    )
  ) {
    return "Schedule unavailable";
  }

  const startDate =
    new Intl.DateTimeFormat(
      undefined,
      {
        weekday: "short",
        month: "short",
        day: "numeric",
      },
    ).format(
      start,
    );

  const startTime =
    new Intl.DateTimeFormat(
      undefined,
      {
        hour: "numeric",
        minute: "2-digit",
      },
    ).format(
      start,
    );

  const endTime =
    new Intl.DateTimeFormat(
      undefined,
      {
        hour: "numeric",
        minute: "2-digit",
      },
    ).format(
      end,
    );

  return [
    startDate,
    " · ",
    startTime,
    " – ",
    endTime,
  ].join("");
}


function formatTaskStatus(
  status:
    AcademicTaskPriorityResponse["task"]["status"],
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


function getErrorMessage(
  error: unknown,
): string {
  if (
    error instanceof Error &&
    error.message.trim()
  ) {
    return error.message;
  }

  return (
    "Priority tasks could not be loaded."
  );
}


async function loadNextStudySessionCandidate(
  signal?: AbortSignal,
): Promise<DashboardStudySessionCandidate | null> {
  const plans =
    await listStudyPlans(
      50,
      {
        signal,
      },
    );

  const relevantPlans =
    plans.filter(
      (
        plan,
      ) =>
        plan.status === "active" ||
        plan.status === "draft",
    );

  if (
    relevantPlans.length === 0
  ) {
    return null;
  }

  const sessionGroups =
    await Promise.all(
      relevantPlans.map(
        async (
          plan,
        ) => {
          const sessions =
            await listStudySessions(
              plan.id,
              200,
              {
                signal,
              },
            );

          return sessions.map(
            (
              session,
            ) => ({
              plan,
              session,
            }),
          );
        },
      ),
    );

  return selectNextStudySession(
    sessionGroups.flat(),
  );
}


function formatAnalyticsPercent(
  metric: AnalyticsMetric,
): string {
  if (
    metric.availability ===
      "unavailable"
  ) {
    return "Unavailable";
  }

  if (
    metric.sample_size === 0 ||
    metric.value === null
  ) {
    return "No data yet";
  }

  return `${metric.value.toFixed(1)}%`;
}


function formatAnalyticsCount(
  metric: AnalyticsCountMetric,
): string {
  if (
    metric.availability ===
      "unavailable" ||
    metric.value === null
  ) {
    return "Unavailable";
  }

  return String(
    metric.value,
  );
}


export function DashboardWorkspace({
  displayName,
  subjects,
}: DashboardWorkspaceProps) {
  const [
    priorityTasks,
    setPriorityTasks,
  ] = useState<
    AcademicTaskPriorityResponse[]
  >([]);

  const [
    isLoadingTasks,
    setIsLoadingTasks,
  ] = useState(
    true,
  );

  const [
    taskError,
    setTaskError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    nextStudySession,
    setNextStudySession,
  ] = useState<
    DashboardStudySessionCandidate | null
  >(
    null,
  );

  const [
    isLoadingStudySession,
    setIsLoadingStudySession,
  ] = useState(
    true,
  );

  const [
    studySessionError,
    setStudySessionError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    analyticsOverview,
    setAnalyticsOverview,
  ] = useState<
    AnalyticsOverviewResponse | null
  >(
    null,
  );

  const [
    isLoadingAnalytics,
    setIsLoadingAnalytics,
  ] = useState(
    true,
  );

  const [
    analyticsError,
    setAnalyticsError,
  ] = useState<
    string | null
  >(
    null,
  );

  const subjectNames =
    useMemo(
      () =>
        new Map(
          subjects.map(
            (
              subject,
            ) => [
              subject.id,
              subject.name,
            ],
          ),
        ),
      [
        subjects,
      ],
    );

  const loadPriorityTasks =
    useCallback(
      async (
        signal?:
          AbortSignal,
      ) => {
        try {
          const items =
            await listPrioritizedAcademicTasks(
              {
                limit:
                  PRIORITY_TASK_LIMIT,
                signal,
              },
            );

          if (
            signal?.aborted
          ) {
            return;
          }

          setPriorityTasks(
            items,
          );
        } catch (
          error
        ) {
          if (
            error instanceof
              DOMException &&
            error.name ===
              "AbortError"
          ) {
            return;
          }

          if (
            signal?.aborted
          ) {
            return;
          }

          setPriorityTasks(
            [],
          );

          setTaskError(
            getErrorMessage(
              error,
            ),
          );
        } finally {
          if (
            !signal?.aborted
          ) {
            setIsLoadingTasks(
              false,
            );
          }
        }
      },
      [],
    );

  useEffect(
    () => {
      const controller =
        new AbortController();

      void listPrioritizedAcademicTasks(
        {
          limit:
            PRIORITY_TASK_LIMIT,
          signal:
            controller.signal,
        },
      )
        .then(
          (
            items,
          ) => {
            if (
              controller.signal
                .aborted
            ) {
              return;
            }

            setPriorityTasks(
              items,
            );

            setIsLoadingTasks(
              false,
            );
          },
        )
        .catch(
          (
            error:
              unknown,
          ) => {
            if (
              controller.signal
                .aborted
            ) {
              return;
            }

            if (
              error instanceof
                DOMException &&
              error.name ===
                "AbortError"
            ) {
              return;
            }

            setPriorityTasks(
              [],
            );

            setTaskError(
              getErrorMessage(
                error,
              ),
            );

            setIsLoadingTasks(
              false,
            );
          },
        );

      return () => {
        controller.abort();
      };
    },
    [],
  );

  useEffect(
    () => {
      const controller =
        new AbortController();

      void loadNextStudySessionCandidate(
        controller.signal,
      )
        .then(
          (
            candidate,
          ) => {
            if (
              controller.signal
                .aborted
            ) {
              return;
            }

            setNextStudySession(
              candidate,
            );

            setIsLoadingStudySession(
              false,
            );
          },
        )
        .catch(
          (
            error:
              unknown,
          ) => {
            if (
              controller.signal
                .aborted
            ) {
              return;
            }

            if (
              error instanceof
                DOMException &&
              error.name ===
                "AbortError"
            ) {
              return;
            }

            setNextStudySession(
              null,
            );

            setStudySessionError(
              getErrorMessage(
                error,
              ),
            );

            setIsLoadingStudySession(
              false,
            );
          },
        );

      return () => {
        controller.abort();
      };
    },
    [],
  );

  useEffect(
    () => {
      const controller =
        new AbortController();

      void getAnalyticsOverview(
        "last_7_days",
        {
          signal:
            controller.signal,
        },
      )
        .then(
          (
            overview,
          ) => {
            if (
              controller.signal
                .aborted
            ) {
              return;
            }

            setAnalyticsOverview(
              overview,
            );

            setIsLoadingAnalytics(
              false,
            );
          },
        )
        .catch(
          (
            error:
              unknown,
          ) => {
            if (
              controller.signal
                .aborted
            ) {
              return;
            }

            if (
              error instanceof
                DOMException &&
              error.name ===
                "AbortError"
            ) {
              return;
            }

            setAnalyticsOverview(
              null,
            );

            setAnalyticsError(
              getErrorMessage(
                error,
              ),
            );

            setIsLoadingAnalytics(
              false,
            );
          },
        );

      return () => {
        controller.abort();
      };
    },
    [],
  );

  const retryStudySession =
    useCallback(
      () => {
        setIsLoadingStudySession(
          true,
        );

        setStudySessionError(
          null,
        );

        void loadNextStudySessionCandidate()
          .then(
            (
              candidate,
            ) => {
              setNextStudySession(
                candidate,
              );

              setIsLoadingStudySession(
                false,
              );
            },
          )
          .catch(
            (
              error:
                unknown,
            ) => {
              setNextStudySession(
                null,
              );

              setStudySessionError(
                getErrorMessage(
                  error,
                ),
              );

              setIsLoadingStudySession(
                false,
              );
            },
          );
      },
      [],
    );

  const retryAnalytics =
    useCallback(
      () => {
        setIsLoadingAnalytics(
          true,
        );

        setAnalyticsError(
          null,
        );

        void getAnalyticsOverview(
          "last_7_days",
        )
          .then(
            (
              overview,
            ) => {
              setAnalyticsOverview(
                overview,
              );

              setIsLoadingAnalytics(
                false,
              );
            },
          )
          .catch(
            (
              error:
                unknown,
            ) => {
              setAnalyticsOverview(
                null,
              );

              setAnalyticsError(
                getErrorMessage(
                  error,
                ),
              );

              setIsLoadingAnalytics(
                false,
              );
            },
          );
      },
      [],
    );

  return (
    <Container
      py={{
        base: 24,
        sm: 32,
      }}
      size="xl"
    >
      <Stack
        gap="lg"
      >
        <Paper
        className={
            styles.hero
        }
        p={{
            base: "md",
            sm: "lg",
        }}
        radius="lg"
        withBorder
        >
        <Group
            align="flex-start"
            justify="space-between"
            wrap="wrap"
        >
            <Stack
            gap={3}
            >
            <Text
                c="violet.7"
                fw={700}
                size="xs"
                tt="uppercase"
            >
                Student dashboard
            </Text>

            <Title
                order={1}
            >
                Welcome back,{" "}
                {displayName}
            </Title>

            <Text
                c="dimmed"
                maw={680}
                size="sm"
            >
                Here&apos;s what
                needs your attention
                and what to study
                next.
            </Text>
            </Stack>

            <Button
            component={
                Link
            }
            href="/profile"
            leftSection={
                <IconUserEdit
                size={16}
                />
            }
            size="compact-sm"
            variant="light"
            >
            Edit profile
            </Button>
        </Group>
        </Paper>

        <div
          className={
            styles.mainGrid
          }
        >
          <Paper
            className={
              styles.sectionCard
            }
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack
              gap="md"
            >
              <Group
                align="flex-start"
                justify="space-between"
              >
                <Stack
                  gap={1}
                >
                  <Title
                    order={2}
                  >
                    Priority Tasks
                  </Title>

                  <Text
                    c="dimmed"
                    size="xs"
                  >
                    Your highest-priority
                    Academic Tasks.
                  </Text>
                </Stack>

                <Button
                  component={
                    Link
                  }
                  href="/academic-tasks"
                  leftSection={
                    <IconChecklist
                      size={15}
                    />
                  }
                  size="compact-sm"
                  variant="light"
                >
                  View all tasks
                </Button>
              </Group>

              {isLoadingTasks ? (
                <Group
                  gap="xs"
                  py="sm"
                >
                  <Loader
                    size="xs"
                  />

                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    Loading priority
                    tasks...
                  </Text>
                </Group>
              ) : null}

              {!isLoadingTasks &&
              taskError ? (
                <Alert
                  color="red"
                  icon={
                    <IconAlertCircle
                      size={17}
                    />
                  }
                  title="Unable to load priority tasks"
                >
                  <Stack
                    gap="xs"
                  >
                    <Text
                      size="sm"
                    >
                      {taskError}
                    </Text>

                    <Group>
                      <Button
                        color="red"
                        leftSection={
                          <IconRefresh
                            size={15}
                          />
                        }
                        onClick={() => {
                          setIsLoadingTasks(
                            true,
                          );

                          setTaskError(
                            null,
                          );

                          void loadPriorityTasks();
                        }}
                        size="compact-sm"
                        variant="light"
                      >
                        Retry
                      </Button>
                    </Group>
                  </Stack>
                </Alert>
              ) : null}

              {!isLoadingTasks &&
              !taskError &&
              priorityTasks.length ===
                0 ? (
                <div
                  className={
                    styles.emptyState
                  }
                >
                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    No Academic Tasks
                    currently need your
                    attention.
                  </Text>

                  <Button
                    component={
                      Link
                    }
                    href="/academic-tasks"
                    mt="xs"
                    size="compact-sm"
                    variant="light"
                  >
                    Open Academic Tasks
                  </Button>
                </div>
              ) : null}

              {!isLoadingTasks &&
              !taskError &&
              priorityTasks.length >
                0 ? (
                <div
                  className={
                    styles.taskList
                  }
                >
                  {priorityTasks.map(
                    (
                      item,
                    ) => {
                      const {
                        task,
                        priority,
                      } =
                        item;

                      const presentation =
                        getAcademicTaskPriorityPresentation(
                          priority.total_score,
                        );

                      const subjectName =
                        subjectNames.get(
                          task.subject_id,
                        ) ??
                        "Unknown subject";

                      return (
                        <div
                          key={
                            task.id
                          }
                          className={
                            styles.taskRow
                          }
                        >
                          <Stack
                            gap={5}
                          >
                            <Group
                              align="flex-start"
                              justify="space-between"
                              wrap="wrap"
                            >
                              <Text
                                fw={700}
                                size="sm"
                              >
                                {
                                  task.title
                                }
                              </Text>

                              <Badge
                                color={
                                  presentation.color
                                }
                                size="sm"
                                variant="light"
                              >
                                {
                                  presentation.label
                                }
                              </Badge>
                            </Group>

                            <Group
                              gap={6}
                              wrap="wrap"
                            >
                              <Badge
                                size="xs"
                                variant="outline"
                              >
                                {
                                  subjectName
                                }
                              </Badge>

                              <Badge
                                color="gray"
                                size="xs"
                                variant="light"
                              >
                                {formatTaskStatus(
                                  task.status,
                                )}
                              </Badge>

                              <Text
                                c="dimmed"
                                size="xs"
                              >
                                Due{" "}
                                {formatDeadline(
                                  task.deadline,
                                )}
                                {" · "}
                                {
                                  task.estimated_minutes
                                }{" "}
                                min
                              </Text>
                            </Group>
                          </Stack>
                        </div>
                      );
                    },
                  )}
                </div>
              ) : null}
            </Stack>
          </Paper>

          <Paper
            className={
              styles.sectionCard
            }
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack
              gap="md"
            >
              <Group
                align="flex-start"
                justify="space-between"
              >
                <Stack
                  gap={1}
                >
                  <Title
                    order={2}
                  >
                    Next Study Session
                  </Title>

                  <Text
                    c="dimmed"
                    size="xs"
                  >
                    Your nearest upcoming
                    planned Study Plan
                    session.
                  </Text>
                </Stack>

                <Button
                  component={
                    Link
                  }
                  href="/study-plan"
                  leftSection={
                    <IconCalendarTime
                      size={15}
                    />
                  }
                  size="compact-sm"
                  variant="light"
                >
                  Open study plan
                </Button>
              </Group>

              {isLoadingStudySession ? (
                <Group
                  gap="xs"
                  py="sm"
                >
                  <Loader
                    size="xs"
                  />

                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    Loading your next
                    study session...
                  </Text>
                </Group>
              ) : null}

              {!isLoadingStudySession &&
              studySessionError ? (
                <Alert
                  color="red"
                  icon={
                    <IconAlertCircle
                      size={17}
                    />
                  }
                  title="Unable to load your study plan"
                >
                  <Stack
                    gap="xs"
                  >
                    <Text
                      size="sm"
                    >
                      {
                        studySessionError
                      }
                    </Text>

                    <Group>
                      <Button
                        color="red"
                        leftSection={
                          <IconRefresh
                            size={15}
                          />
                        }
                        onClick={
                          retryStudySession
                        }
                        size="compact-sm"
                        variant="light"
                      >
                        Retry
                      </Button>
                    </Group>
                  </Stack>
                </Alert>
              ) : null}

              {!isLoadingStudySession &&
              !studySessionError &&
              !nextStudySession ? (
                <div
                  className={
                    styles.emptyState
                  }
                >
                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    You do not have an
                    upcoming planned study
                    session.
                  </Text>

                  <Button
                    component={
                      Link
                    }
                    href="/study-plan"
                    mt="xs"
                    size="compact-sm"
                    variant="light"
                  >
                    Open Study Plan
                  </Button>
                </div>
              ) : null}

              {!isLoadingStudySession &&
              !studySessionError &&
              nextStudySession ? (
                <div
                  className={
                    styles.sessionCard
                  }
                >
                  <Stack
                    gap="xs"
                  >
                    <Group
                      align="flex-start"
                      justify="space-between"
                    >
                      <Stack
                        gap={2}
                      >
                        <Text
                          fw={700}
                        >
                          {
                            nextStudySession
                              .session
                              .title
                          }
                        </Text>

                        <Text
                          c="dimmed"
                          size="sm"
                        >
                          {
                            subjectNames.get(
                              nextStudySession
                                .session
                                .subject_id,
                            ) ??
                            "Unknown subject"
                          }
                        </Text>
                      </Stack>

                      <Badge
                        color="violet"
                        size="sm"
                        variant="light"
                      >
                        Planned
                      </Badge>
                    </Group>

                    <Text
                      fw={600}
                      size="sm"
                    >
                      {formatStudySessionSchedule(
                        nextStudySession
                          .session
                          .starts_at,
                        nextStudySession
                          .session
                          .ends_at,
                      )}
                    </Text>

                    <Text
                      c="dimmed"
                      size="xs"
                    >
                      Study plan:{" "}
                      {
                        nextStudySession
                          .plan
                          .title
                      }
                    </Text>
                  </Stack>
                </div>
              ) : null}
            </Stack>
          </Paper>
        </div>

        <div
          className={
            styles.summaryGrid
          }
        >
          <Paper
            className={`${styles.sectionCard} ${styles.performanceCard}`}
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack
              gap="md"
            >
              <Group
                align="flex-start"
                justify="space-between"
              >
                <Stack
                  gap={1}
                >
                  <Title
                    order={2}
                  >
                    Performance Snapshot
                  </Title>

                  <Text
                    c="dimmed"
                    size="xs"
                  >
                    Recent learning
                    evidence from the
                    last 7 days.
                  </Text>
                </Stack>

                <Button
                  component={
                    Link
                  }
                  href="/analytics"
                  leftSection={
                    <IconChartBar
                      size={15}
                    />
                  }
                  size="compact-sm"
                  variant="light"
                >
                  View analytics
                </Button>
              </Group>

              {isLoadingAnalytics ? (
                <Group
                  gap="xs"
                  py="sm"
                >
                  <Loader
                    size="xs"
                  />

                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    Loading recent
                    performance...
                  </Text>
                </Group>
              ) : null}

              {!isLoadingAnalytics &&
              analyticsError ? (
                <Alert
                  color="red"
                  icon={
                    <IconAlertCircle
                      size={17}
                    />
                  }
                  title="Unable to load performance"
                >
                  <Stack
                    gap="xs"
                  >
                    <Text
                      size="sm"
                    >
                      {
                        analyticsError
                      }
                    </Text>

                    <Group>
                      <Button
                        color="red"
                        leftSection={
                          <IconRefresh
                            size={15}
                          />
                        }
                        onClick={
                          retryAnalytics
                        }
                        size="compact-sm"
                        variant="light"
                      >
                        Retry
                      </Button>
                    </Group>
                  </Stack>
                </Alert>
              ) : null}

              {!isLoadingAnalytics &&
              !analyticsError &&
              analyticsOverview ? (
                <Stack
                  gap="sm"
                >
                  <div
                    className={
                      styles.metricGrid
                    }
                  >
                    <div
                      className={
                        styles.metricTile
                      }
                    >
                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        Quiz Accuracy
                      </Text>

                      <Text
                        className={
                          styles.metricValue
                        }
                        fw={700}
                        size="lg"
                      >
                        {formatAnalyticsPercent(
                          analyticsOverview
                            .quiz_accuracy_percent,
                        )}
                      </Text>

                      {analyticsOverview
                        .quiz_accuracy_percent
                        .sample_size >
                      0 ? (
                        <Text
                          c="dimmed"
                          size="xs"
                        >
                          {
                            analyticsOverview
                              .quiz_accuracy_percent
                              .sample_size
                          }{" "}
                          completed{" "}
                          {analyticsOverview
                            .quiz_accuracy_percent
                            .sample_size ===
                          1
                            ? "question"
                            : "questions"}
                        </Text>
                      ) : null}
                    </div>

                    <div
                      className={
                        styles.metricTile
                      }
                    >
                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        Flashcard Recall
                      </Text>

                      <Text
                        className={
                          styles.metricValue
                        }
                        fw={700}
                        size="lg"
                      >
                        {formatAnalyticsPercent(
                          analyticsOverview
                            .flashcard_performance_percent,
                        )}
                      </Text>

                      {analyticsOverview
                        .flashcard_performance_percent
                        .sample_size >
                      0 ? (
                        <Text
                          c="dimmed"
                          size="xs"
                        >
                          {
                            analyticsOverview
                              .flashcard_performance_percent
                              .sample_size
                          }{" "}
                          review{" "}
                          {analyticsOverview
                            .flashcard_performance_percent
                            .sample_size ===
                          1
                            ? "event"
                            : "events"}
                        </Text>
                      ) : null}
                    </div>
                  </div>

                  {analyticsOverview
                    .strong_topics
                    .length >
                  0 ? (
                    <Group
                      gap="xs"
                    >
                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        Strongest:
                      </Text>

                      <Text
                        fw={700}
                        size="sm"
                      >
                        {
                          analyticsOverview
                            .strong_topics[0]
                            .topic
                        }
                      </Text>

                      <Badge
                        color="green"
                        size="sm"
                        variant="light"
                      >
                        {analyticsOverview
                          .strong_topics[0]
                          .score_percent
                          .toFixed(
                            1,
                          )}
                        %
                      </Badge>
                    </Group>
                  ) : (
                    <Text
                      c="dimmed"
                      size="xs"
                    >
                      Complete quizzes or flashcard reviews to build recent topic evidence.
                    </Text>
                  )}
                </Stack>
              ) : null}
            </Stack>
          </Paper>

          <Paper
            className={`${styles.sectionCard} ${styles.materialsCard}`}
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack
              gap="md"
            >
              <Group
                align="flex-start"
                justify="space-between"
              >
                <Stack
                  gap={1}
                >
                  <Title
                    order={2}
                  >
                    Study Materials
                  </Title>

                  <Text
                    c="dimmed"
                    size="xs"
                  >
                    Your current learning
                    inventory.
                  </Text>
                </Stack>

                <Button
                  component={
                    Link
                  }
                  href="/subjects"
                  leftSection={
                    <IconBooks
                      size={15}
                    />
                  }
                  size="compact-sm"
                  variant="light"
                >
                  Manage subjects
                </Button>
              </Group>

              {isLoadingAnalytics ? (
                <Group
                  gap="xs"
                  py="sm"
                >
                  <Loader
                    size="xs"
                  />

                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    Loading study
                    materials...
                  </Text>
                </Group>
              ) : null}

              {!isLoadingAnalytics &&
              analyticsError ? (
                <Alert
                  color="red"
                  icon={
                    <IconAlertCircle
                      size={17}
                    />
                  }
                  title="Unable to load study materials"
                >
                  <Stack
                    gap="xs"
                  >
                    <Text
                      size="sm"
                    >
                      {
                        analyticsError
                      }
                    </Text>

                    <Group>
                      <Button
                        color="red"
                        leftSection={
                          <IconRefresh
                            size={15}
                          />
                        }
                        onClick={
                          retryAnalytics
                        }
                        size="compact-sm"
                        variant="light"
                      >
                        Retry
                      </Button>
                    </Group>
                  </Stack>
                </Alert>
              ) : null}

              {!isLoadingAnalytics &&
              !analyticsError &&
              analyticsOverview ? (
                <>
                  <div
                    className={
                      styles.materialGrid
                    }
                  >
                    <div
                      className={
                        styles.metricTile
                      }
                    >
                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        Subjects
                      </Text>

                      <Text
                        className={
                          styles.metricValue
                        }
                        fw={700}
                        size="lg"
                      >
                        {formatAnalyticsCount(
                          analyticsOverview
                            .subject_count,
                        )}
                      </Text>
                    </div>

                    <div
                      className={
                        styles.metricTile
                      }
                    >
                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        Materials
                      </Text>

                      <Text
                        className={
                          styles.metricValue
                        }
                        fw={700}
                        size="lg"
                      >
                        {formatAnalyticsCount(
                          analyticsOverview
                            .study_material_count,
                        )}
                      </Text>
                    </div>

                    <div
                      className={
                        styles.metricTile
                      }
                    >
                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        Ready
                      </Text>

                      <Text
                        className={
                          styles.metricValue
                        }
                        fw={700}
                        size="lg"
                      >
                        {formatAnalyticsCount(
                          analyticsOverview
                            .ready_study_material_count,
                        )}
                      </Text>
                    </div>
                  </div>

                  <Text
                    c="dimmed"
                    size="xs"
                  >
                    Ready materials have
                    completed processing and
                    can support your learning
                    features.
                  </Text>
                </>
              ) : null}
            </Stack>
          </Paper>

          <Paper
            className={`${styles.sectionCard} ${styles.quickActionsCard}`}
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack
              gap="md"
            >
              <Stack
                gap={1}
              >
                <Title
                  order={2}
                >
                  Quick Actions
                </Title>

                <Text
                  c="dimmed"
                  size="xs"
                >
                  Jump directly to your
                  study tools.
                </Text>
              </Stack>

              <div
                className={
                  styles.quickActionGrid
                }
              >
                {QUICK_ACTIONS.map(
                  (
                    action,
                  ) => (
                    <Link
                      key={
                        action.href
                      }
                      aria-label={
                        `Open ${action.title}`
                      }
                      className={
                        styles.actionLink
                      }
                      href={
                        action.href
                      }
                    >
                      <div
                        className={
                          styles.actionTile
                        }
                      >
                        <ThemeIcon
                          color="violet"
                          radius="md"
                          size={32}
                          variant="light"
                        >
                          {
                            action.icon
                          }
                        </ThemeIcon>

                        <Stack
                          gap={0}
                        >
                          <Text
                            fw={700}
                            size="sm"
                          >
                            {
                              action.title
                            }
                          </Text>

                          <Text
                            c="dimmed"
                            size="xs"
                          >
                            Open
                          </Text>
                        </Stack>
                      </div>
                    </Link>
                  ),
                )}
              </div>
            </Stack>
          </Paper>
        </div>
      </Stack>
    </Container>
  );
}