// File: /frontend/features/study-plans/components/StudyPlansWorkspace.tsx
// Purpose: Displays saved Track D study plans and their
// scheduled sessions in a responsive weekly calendar.

"use client";

import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  Paper,
  ScrollArea,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Tooltip,
  UnstyledButton,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCalendarEvent,
  IconCalendarWeek,
  IconChevronLeft,
  IconChevronRight,
  IconClock,
  IconPlayerPlay,
  IconPlus,
  IconRefresh,
  IconSparkles,
  IconTrash,
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
  useStudyTimer,
} from "@/features/study-timer/components/StudyTimerProvider";
import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  academicTasksToSchedulableTasks,
} from "../academic-task-adapter";
import {
  deleteStudyPlan,
  deleteStudySession,
  listStudyPlans,
  listStudySessions,
} from "../api";
import type {
  SchedulableTask,
  StudyPlan,
  StudyPlanGenerationResponse,
  StudySession,
} from "../types";

import {
  CreateStudyPlanModal,
} from "./CreateStudyPlanModal";
import {
  CreateStudySessionModal,
} from "./CreateStudySessionModal";
import {
  GenerateStudyPlanModal,
} from "./GenerateStudyPlanModal";
import {
  RegenerateStudyPlanModal,
} from "./RegenerateStudyPlanModal";

import classes from "./StudyPlansWorkspace.module.css";


interface StudyPlansWorkspaceProps {
  initialSubjects:
    SubjectSummary[];
}


type LoadStatus =
  | "loading"
  | "ready"
  | "error";


function startOfMonday(
  value: Date,
): Date {
  const result =
    new Date(
      value,
    );

  result.setHours(
    0,
    0,
    0,
    0,
  );

  const daysSinceMonday =
    (
      result.getDay() +
      6
    ) % 7;

  result.setDate(
    result.getDate() -
      daysSinceMonday,
  );

  return result;
}


function addDays(
  value: Date,
  amount: number,
): Date {
  const result =
    new Date(
      value,
    );

  result.setDate(
    result.getDate() +
      amount,
  );

  return result;
}


function parseDateOnly(
  value: string,
): Date {
  return new Date(
    `${value}T00:00:00`,
  );
}


function localDateKey(
  value: Date,
): string {
  return [
    value.getFullYear(),
    String(
      value.getMonth() +
        1,
    ).padStart(
      2,
      "0",
    ),
    String(
      value.getDate(),
    ).padStart(
      2,
      "0",
    ),
  ].join("-");
}


function getErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (
    error instanceof
      Error &&
    error.message.trim()
  ) {
    return error.message;
  }

  return fallback;
}


function isAbortError(
  error: unknown,
): boolean {
  return (
    error instanceof
      DOMException &&
    error.name ===
      "AbortError"
  );
}


function formatPlanRange(
  plan: StudyPlan,
): string {
  const formatter =
    new Intl.DateTimeFormat(
      undefined,
      {
        month:
          "short",
        day:
          "numeric",
        year:
          "numeric",
      },
    );

  return [
    formatter.format(
      parseDateOnly(
        plan.starts_on,
      ),
    ),
    "–",
    formatter.format(
      parseDateOnly(
        plan.ends_on,
      ),
    ),
  ].join(" ");
}


function formatTime(
  isoValue: string,
): string {
  return new Intl.DateTimeFormat(
    undefined,
    {
      hour:
        "numeric",
      minute:
        "2-digit",
    },
  ).format(
    new Date(
      isoValue,
    ),
  );
}


export function StudyPlansWorkspace({
  initialSubjects,
}: Readonly<StudyPlansWorkspaceProps>) {
  const {
    activity:
      activeStudyActivity,
    pendingAction:
      studyTimerPendingAction,
    startFromStudySession,
  } =
    useStudyTimer();

  const [
    plans,
    setPlans,
  ] = useState<
    StudyPlan[]
  >([]);

  const [
    plansStatus,
    setPlansStatus,
  ] = useState<LoadStatus>(
    "loading",
  );

  const [
    plansError,
    setPlansError,
  ] = useState<
    string | null
  >(null);

  const [
    selectedPlanId,
    setSelectedPlanId,
  ] = useState<
    string | null
  >(null);

  const [
    sessions,
    setSessions,
  ] = useState<
    StudySession[]
  >([]);

  const [
    sessionsStatus,
    setSessionsStatus,
  ] = useState<LoadStatus>(
    "ready",
  );

  const [
    sessionsError,
    setSessionsError,
  ] = useState<
    string | null
  >(null);

  const [
    weekAnchor,
    setWeekAnchor,
  ] = useState(
    () =>
      startOfMonday(
        new Date(),
      ),
  );

  const [
    createPlanOpened,
    setCreatePlanOpened,
  ] = useState(
    false,
  );

  const [
    createSessionOpened,
    setCreateSessionOpened,
  ] = useState(
    false,
  );

  const [
    deletePlanOpened,
    setDeletePlanOpened,
  ] = useState(
    false,
  );

  const [
    sessionToDelete,
    setSessionToDelete,
  ] = useState<
    StudySession | null
  >(null);

  const [
    actionError,
    setActionError,
  ] = useState<
    string | null
  >(null);

  const [
    deletingPlan,
    setDeletingPlan,
  ] = useState(
    false,
  );

  const [
    deletingSession,
    setDeletingSession,
  ] = useState(
    false,
  );

  const [
    generatePlanOpened,
    setGeneratePlanOpened,
  ] = useState(
    false,
  );

  const [
    regeneratePlanOpened,
    setRegeneratePlanOpened,
  ] = useState(
    false,
  );

  const [
    regenerationTasks,
    setRegenerationTasks,
  ] = useState<
    SchedulableTask[]
  >([]);

  const [
    regenerationTasksLoading,
    setRegenerationTasksLoading,
  ] = useState(
    false,
  );

  const [
    generationTasks,
    setGenerationTasks,
  ] = useState<
    SchedulableTask[]
  >([]);

  const [
    generationTasksLoading,
    setGenerationTasksLoading,
  ] = useState(
    false,
  );

  const [
    generationTasksError,
    setGenerationTasksError,
  ] = useState<
    string | null
  >(null);


  const subjectNames =
    useMemo(
      () =>
        new Map(
          initialSubjects.map(
            (
              subject,
            ) => [
              subject.id,
              subject.name,
            ],
          ),
        ),
      [
        initialSubjects,
      ],
    );


  const selectedPlan =
    useMemo(
      () =>
        plans.find(
          (
            plan,
          ) =>
            plan.id ===
            selectedPlanId,
        ) ??
        null,
      [
        plans,
        selectedPlanId,
      ],
    );


  const selectedPlanHasActiveTimer =
    activeStudyActivity !==
      null &&
    selectedPlan !==
      null &&
    activeStudyActivity
      .study_plan_id ===
      selectedPlan.id;


  const weekDays =
    useMemo(
      () =>
        Array.from(
          {
            length:
              7,
          },
          (
            _,
            index,
          ) =>
            addDays(
              weekAnchor,
              index,
            ),
        ),
      [
        weekAnchor,
      ],
    );


  const sessionsByDay =
    useMemo(
      () => {
        const result =
          new Map<
            string,
            StudySession[]
          >();

        for (
          const session
          of sessions
        ) {
          const key =
            localDateKey(
              new Date(
                session.starts_at,
              ),
            );

          const current =
            result.get(
              key,
            ) ??
            [];

          current.push(
            session,
          );

          result.set(
            key,
            current,
          );
        }

        for (
          const items
          of result.values()
        ) {
          items.sort(
            (
              first,
              second,
            ) =>
              new Date(
                first.starts_at,
              ).getTime() -
              new Date(
                second.starts_at,
              ).getTime(),
          );
        }

        return result;
      },
      [
        sessions,
      ],
    );


  const loadPlans =
    useCallback(
      async (
        signal?:
          AbortSignal,
      ) => {
        setPlansStatus(
          "loading",
        );

        setPlansError(
          null,
        );

        try {
          const loadedPlans =
            await listStudyPlans(
              50,
              {
                signal,
              },
            );

          setPlans(
            loadedPlans,
          );

          setSelectedPlanId(
            (
              currentPlanId,
            ) => {
              if (
                currentPlanId &&
                loadedPlans.some(
                  (
                    plan,
                  ) =>
                    plan.id ===
                    currentPlanId,
                )
              ) {
                return currentPlanId;
              }

              return (
                loadedPlans[0]
                  ?.id ??
                null
              );
            },
          );

          if (
            loadedPlans[0]
          ) {
            setWeekAnchor(
              startOfMonday(
                parseDateOnly(
                  loadedPlans[0]
                    .starts_on,
                ),
              ),
            );
          } else {
            setSessions(
              [],
            );
          }

          setPlansStatus(
            "ready",
          );
        } catch (
          error
        ) {
          if (
            isAbortError(
              error,
            )
          ) {
            return;
          }

          setPlansStatus(
            "error",
          );

          setPlansError(
            getErrorMessage(
              error,
              "Your study plans could not be loaded.",
            ),
          );
        }
      },
      [],
    );


  const loadSessions =
    useCallback(
      async (
        studyPlanId:
          string,
        signal?:
          AbortSignal,
      ) => {
        setSessionsStatus(
          "loading",
        );

        setSessionsError(
          null,
        );

        try {
          const loadedSessions =
            await listStudySessions(
              studyPlanId,
              200,
              {
                signal,
              },
            );

          setSessions(
            loadedSessions,
          );

          setSessionsStatus(
            "ready",
          );
        } catch (
          error
        ) {
          if (
            isAbortError(
              error,
            )
          ) {
            return;
          }

          setSessions(
            [],
          );

          setSessionsStatus(
            "error",
          );

          setSessionsError(
            getErrorMessage(
              error,
              "Scheduled study sessions could not be loaded.",
            ),
          );
        }
      },
      [],
    );


  useEffect(
    () => {
      const controller =
        new AbortController();

      async function loadInitialPlans():
        Promise<void> {
        try {
          const loadedPlans =
            await listStudyPlans(
              50,
              {
                signal:
                  controller.signal,
              },
            );

          if (
            controller
              .signal
              .aborted
          ) {
            return;
          }

          setPlans(
            loadedPlans,
          );

          setPlansError(
            null,
          );

          setSelectedPlanId(
            (
              currentPlanId,
            ) => {
              if (
                currentPlanId &&
                loadedPlans.some(
                  (
                    plan,
                  ) =>
                    plan.id ===
                    currentPlanId,
                )
              ) {
                return currentPlanId;
              }

              return (
                loadedPlans[0]
                  ?.id ??
                null
              );
            },
          );

          if (
            loadedPlans[0]
          ) {
            setWeekAnchor(
              startOfMonday(
                parseDateOnly(
                  loadedPlans[0]
                    .starts_on,
                ),
              ),
            );

            setSessionsStatus(
              "loading",
            );
          } else {
            setSessions(
              [],
            );

            setSessionsStatus(
              "ready",
            );
          }

          setPlansStatus(
            "ready",
          );
        } catch (
          error
        ) {
          if (
            controller
              .signal
              .aborted ||
            isAbortError(
              error,
            )
          ) {
            return;
          }

          setPlansStatus(
            "error",
          );

          setPlansError(
            getErrorMessage(
              error,
              "Your study plans could not be loaded.",
            ),
          );
        }
      }

      void loadInitialPlans();

      return () => {
        controller.abort();
      };
    },
    [],
  );


  useEffect(
    () => {
      if (
        !selectedPlanId
      ) {
        return;
      }

      const studyPlanId =
        selectedPlanId;

      const controller =
        new AbortController();

      async function loadSelectedPlanSessions():
        Promise<void> {
        await Promise.resolve();

        if (
          controller
            .signal
            .aborted
        ) {
          return;
        }

        setSessionsStatus(
          "loading",
        );

        setSessionsError(
          null,
        );

        try {
          const loadedSessions =
            await listStudySessions(
              studyPlanId,
              200,
              {
                signal:
                  controller.signal,
              },
            );

          if (
            controller
              .signal
              .aborted
          ) {
            return;
          }

          setSessions(
            loadedSessions,
          );

          setSessionsStatus(
            "ready",
          );
        } catch (
          error
        ) {
          if (
            controller
              .signal
              .aborted ||
            isAbortError(
              error,
            )
          ) {
            return;
          }

          setSessions(
            [],
          );

          setSessionsStatus(
            "error",
          );

          setSessionsError(
            getErrorMessage(
              error,
              "Scheduled study sessions could not be loaded.",
            ),
          );
        }
      }

      void loadSelectedPlanSessions();

      return () => {
        controller.abort();
      };
    },
    [
      selectedPlanId,
    ],
  );


  function selectPlan(
    plan:
      StudyPlan,
  ): void {
    setActionError(
      null,
    );

    setSessionsStatus(
      "loading",
    );

    setSessionsError(
      null,
    );

    setSessions(
      [],
    );

    setSelectedPlanId(
      plan.id,
    );

    setWeekAnchor(
      startOfMonday(
        parseDateOnly(
          plan.starts_on,
        ),
      ),
    );
  }


  function handlePlanCreated(
    plan:
      StudyPlan,
  ): void {
    setPlans(
      (
        currentPlans,
      ) => [
        plan,
        ...currentPlans,
      ],
    );

    setSelectedPlanId(
      plan.id,
    );

    setSessions(
      [],
    );

    setSessionsStatus(
      "ready",
    );

    setActionError(
      null,
    );

    setWeekAnchor(
      startOfMonday(
        parseDateOnly(
          plan.starts_on,
        ),
      ),
    );
  }


  function handleSessionCreated(
    session:
      StudySession,
  ): void {
    setSessions(
      (
        currentSessions,
      ) => [
        ...currentSessions,
        session,
      ],
    );

    setActionError(
      null,
    );

    setWeekAnchor(
      startOfMonday(
        new Date(
          session.starts_at,
        ),
      ),
    );
  }


  async function handleDeletePlan():
    Promise<void> {
    if (
      !selectedPlan
    ) {
      return;
    }

    if (
      selectedPlanHasActiveTimer
    ) {
      setActionError(
        "Finish the active study timer before deleting this plan.",
      );

      setDeletePlanOpened(
        false,
      );

      return;
    }

    setDeletingPlan(
      true,
    );

    setActionError(
      null,
    );

    try {
      await deleteStudyPlan(
        selectedPlan.id,
      );

      setDeletePlanOpened(
        false,
      );

      setSelectedPlanId(
        null,
      );

      setSessions(
        [],
      );

      await loadPlans();
    } catch (
      error
    ) {
      setActionError(
        getErrorMessage(
          error,
          "The study plan could not be deleted.",
        ),
      );
    } finally {
      setDeletingPlan(
        false,
      );
    }
  }


  async function handleDeleteSession():
    Promise<void> {
    if (
      !selectedPlan ||
      !sessionToDelete
    ) {
      return;
    }

    if (
      activeStudyActivity
        ?.study_session_id ===
      sessionToDelete.id
    ) {
      setActionError(
        "Finish this study timer before deleting its scheduled session.",
      );

      setSessionToDelete(
        null,
      );

      return;
    }

    const sessionId =
      sessionToDelete.id;

    setDeletingSession(
      true,
    );

    setActionError(
      null,
    );

    try {
      await deleteStudySession(
        selectedPlan.id,
        sessionId,
      );

      setSessions(
        (
          currentSessions,
        ) =>
          currentSessions.filter(
            (
              session,
            ) =>
              session.id !==
              sessionId,
          ),
      );

      setSessionToDelete(
        null,
      );
    } catch (
      error
    ) {
      setActionError(
        getErrorMessage(
          error,
          "The study session could not be deleted.",
        ),
      );
    } finally {
      setDeletingSession(
        false,
      );
    }
  }


  async function handleStartStudying(
    session:
      StudySession,
  ): Promise<void> {
    setActionError(
      null,
    );

    if (
      activeStudyActivity !==
      null
    ) {
      setActionError(
        "Finish the current study timer before starting another session.",
      );

      return;
    }

    try {
      await startFromStudySession(
        session.id,
      );
    } catch (
      error
    ) {
      setActionError(
        getErrorMessage(
          error,
          "The study timer could not be started.",
        ),
      );
    }
  }


  async function handleOpenGeneratePlan():
    Promise<void> {
    setGenerationTasksLoading(
      true,
    );

    setGenerationTasksError(
      null,
    );

    try {
      const prioritizedTasks =
        await listPrioritizedAcademicTasks({
          limit:
            100,
        });

      setGenerationTasks(
        academicTasksToSchedulableTasks(
          prioritizedTasks,
        ),
      );

      setGeneratePlanOpened(
        true,
      );
    } catch (
      error
    ) {
      setGenerationTasksError(
        getErrorMessage(
          error,
          "Your academic tasks could not be loaded for study-plan generation.",
        ),
      );
    } finally {
      setGenerationTasksLoading(
        false,
      );
    }
  }


  async function handleOpenRegeneratePlan():
    Promise<void> {
    if (
      !selectedPlan ||
      selectedPlan.generation_mode !==
        "generated"
    ) {
      setActionError(
        "Only generated study plans can be regenerated.",
      );

      return;
    }

    if (
      selectedPlanHasActiveTimer
    ) {
      setActionError(
        "Finish the active study timer before regenerating this plan.",
      );

      return;
    }

    setRegenerationTasksLoading(
      true,
    );

    setActionError(
      null,
    );

    try {
      const prioritizedTasks =
        await listPrioritizedAcademicTasks({
          limit:
            100,
        });

      setRegenerationTasks(
        academicTasksToSchedulableTasks(
          prioritizedTasks,
        ),
      );

      setRegeneratePlanOpened(
        true,
      );
    } catch (
      error
    ) {
      setActionError(
        getErrorMessage(
          error,
          "Academic tasks could not be loaded for regeneration.",
        ),
      );
    } finally {
      setRegenerationTasksLoading(
        false,
      );
    }
  }


  function handleGeneratedPlan(
    result:
      StudyPlanGenerationResponse,
  ): void {
    setPlans(
      (
        currentPlans,
      ) => [
        result.plan,
        ...currentPlans.filter(
          (
            plan,
          ) =>
            plan.id !==
            result.plan.id,
        ),
      ],
    );

    setSelectedPlanId(
      result.plan.id,
    );

    setSessions(
      result.sessions,
    );

    setSessionsStatus(
      "ready",
    );

    setSessionsError(
      null,
    );

    setActionError(
      null,
    );

    setWeekAnchor(
      startOfMonday(
        parseDateOnly(
          result.plan.starts_on,
        ),
      ),
    );
  }


  function handleRegeneratedPlan(
    result:
      StudyPlanGenerationResponse,
  ): void {
    setPlans(
      (
        currentPlans,
      ) =>
        currentPlans.map(
          (
            plan,
          ) =>
            plan.id ===
            result.plan.id
              ? result.plan
              : plan,
        ),
    );

    setSelectedPlanId(
      result.plan.id,
    );

    setSessions(
      result.sessions,
    );

    setSessionsStatus(
      "ready",
    );

    setSessionsError(
      null,
    );

    setActionError(
      null,
    );
  }


  function handleCloseGeneratePlan():
    void {
    setGeneratePlanOpened(
      false,
    );

    setGenerationTasks(
      [],
    );
  }


  function handleCloseRegeneratePlan():
    void {
    setRegeneratePlanOpened(
      false,
    );

    setRegenerationTasks(
      [],
    );
  }


  function goToPreviousWeek():
    void {
    setWeekAnchor(
      (
        current,
      ) =>
        addDays(
          current,
          -7,
        ),
    );
  }


  function goToNextWeek():
    void {
    setWeekAnchor(
      (
        current,
      ) =>
        addDays(
          current,
          7,
        ),
    );
  }


  function goToCurrentWeek():
    void {
    setWeekAnchor(
      startOfMonday(
        new Date(),
      ),
    );
  }


  function renderSessionCard(
    session:
      StudySession,
  ) {
    const isActiveStudySession =
      activeStudyActivity
        ?.study_session_id ===
      session.id;

    const anotherTimerIsActive =
      activeStudyActivity !==
        null &&
      !isActiveStudySession;

    const timerIsUpdating =
      studyTimerPendingAction !==
      null;

    const studyTooltip =
      anotherTimerIsActive
        ? (
            "Finish the current study timer before "
            + "starting another session."
          )
        : timerIsUpdating
          ? (
              "Wait for the current timer action "
              + "to finish."
            )
          : (
              "Start a focus timer for this "
              + "scheduled session."
            );

    const deleteTooltip =
      isActiveStudySession
        ? (
            "Finish this study timer before "
            + "deleting its scheduled session."
          )
        : (
            "Remove this scheduled session "
            + "from the study plan."
          );

    return (
      <Card
        key={
          session.id
        }
        withBorder
        radius="md"
        padding="sm"
        className={[
          classes.sessionCard,
          isActiveStudySession
            ? classes.sessionCardActive
            : "",
        ].join(
          " ",
        )}
      >
        <Text
          fw={700}
          size="sm"
          className={
            classes.sessionTitle
          }
        >
          {
            session.title
          }
        </Text>

        <Text
          size="xs"
          c="dimmed"
          mt={3}
        >
          {subjectNames.get(
            session.subject_id,
          ) ??
            "Subject"}
        </Text>

        <Group
          gap={5}
          mt="sm"
          wrap="nowrap"
          className={
            classes.sessionTime
          }
        >
          <IconClock
            size={13}
          />

          <Text size="xs">
            {formatTime(
              session.starts_at,
            )}
            {" – "}
            {formatTime(
              session.ends_at,
            )}
          </Text>
        </Group>

        <Group
          justify="space-between"
          align="center"
          gap="xs"
          mt="sm"
          wrap="nowrap"
        >
          <Badge
            size="xs"
            variant="light"
            color={
              session.origin ===
              "generated"
                ? "violet"
                : "blue"
            }
          >
            {
              session.origin
            }
          </Badge>

          <Group
            gap={4}
            wrap="nowrap"
          >
            {isActiveStudySession ? (
              <Tooltip
                label="This scheduled session is currently being timed."
                withArrow
                openDelay={400}
              >
                <Badge
                  size="xs"
                  variant="light"
                  color="violet"
                >
                  Active
                </Badge>
              </Tooltip>
            ) : (
              <Tooltip
                label={
                  studyTooltip
                }
                withArrow
                openDelay={400}
              >
                <span
                  className={
                    classes.studyActionTarget
                  }
                >
                  <Button
                    size="xs"
                    variant="light"
                    leftSection={
                      <IconPlayerPlay
                        size={13}
                      />
                    }
                    disabled={
                      activeStudyActivity !==
                        null ||
                      timerIsUpdating
                    }
                    onClick={() => {
                      void handleStartStudying(
                        session,
                      );
                    }}
                  >
                    Study
                  </Button>
                </span>
              </Tooltip>
            )}

            <Tooltip
              label={
                deleteTooltip
              }
              withArrow
              openDelay={400}
            >
              <span
                className={
                  classes.tooltipTarget
                }
              >
                <ActionIcon
                  size="sm"
                  variant="subtle"
                  color="red"
                  aria-label={
                    `Delete ${session.title}`
                  }
                  disabled={
                    isActiveStudySession
                  }
                  onClick={() =>
                    setSessionToDelete(
                      session,
                    )
                  }
                >
                  <IconTrash
                    size={14}
                  />
                </ActionIcon>
              </span>
            </Tooltip>
          </Group>
        </Group>

        {isActiveStudySession ? (
          <Text
            size="xs"
            fw={600}
            c="violet"
            mt={5}
            className={
              classes.activeSessionText
            }
          >
            Timer running
          </Text>
        ) : null}
      </Card>
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
            fw={700}
          >
            STUDY PLANNING
          </Text>

          <Title order={1}>
            Study plan
          </Title>

          <Text
            c="dimmed"
            maw={700}
            mt="xs"
          >
            Review your saved study
            plans and see scheduled
            sessions across the week.
          </Text>
        </div>

        <ThemeIcon
          size={48}
          radius="lg"
          variant="light"
        >
          <IconCalendarWeek
            size={26}
          />
        </ThemeIcon>
      </div>


      <div
        className={
          classes.workspace
        }
      >
        <Card
          withBorder
          radius="lg"
          padding="lg"
          className={
            classes.planPanel
          }
        >
          <Group
            justify="space-between"
            align="center"
            gap="sm"
            wrap="wrap"
          >
            <div>
              <Text fw={700}>
                Saved plans
              </Text>

              <Text
                size="sm"
                c="dimmed"
              >
                Choose a plan to
                view its schedule.
              </Text>
            </div>

            <Group gap="xs">
              {plansStatus ===
              "ready" ? (
                <Badge
                  variant="light"
                >
                  {plans.length}
                </Badge>
              ) : null}

              <Tooltip
                label="Generate a study plan from your prioritized academic tasks."
                withArrow
                openDelay={400}
              >
                <span
                  className={
                    classes.tooltipTarget
                  }
                >
                  <Button
                    size="xs"
                    variant="light"
                    leftSection={
                      <IconSparkles
                        size={15}
                      />
                    }
                    loading={
                      generationTasksLoading
                    }
                    onClick={() => {
                      void handleOpenGeneratePlan();
                    }}
                  >
                    Generate plan
                  </Button>
                </span>
              </Tooltip>

              <Tooltip
                label="Create a study plan manually."
                withArrow
                openDelay={400}
              >
                <Button
                  size="xs"
                  leftSection={
                    <IconPlus
                      size={15}
                    />
                  }
                  onClick={() =>
                    setCreatePlanOpened(
                      true,
                    )
                  }
                >
                  New plan
                </Button>
              </Tooltip>
            </Group>
          </Group>


          {generationTasksError ? (
            <Alert
              mt="lg"
              color="red"
              title="Automatic generation unavailable"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
              withCloseButton
              onClose={() =>
                setGenerationTasksError(
                  null,
                )
              }
            >
              {
                generationTasksError
              }
            </Alert>
          ) : null}


          {plansStatus ===
          "loading" ? (
            <Stack
              align="center"
              py="xl"
            >
              <Loader
                size="sm"
                aria-label="Loading study plans"
              />

              <Text
                size="sm"
                c="dimmed"
              >
                Loading plans…
              </Text>
            </Stack>
          ) : null}


          {plansStatus ===
          "error" ? (
            <Alert
              mt="lg"
              color="red"
              title="Study plans unavailable"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              <Stack gap="sm">
                <Text size="sm">
                  {plansError}
                </Text>

                <Button
                  size="xs"
                  variant="light"
                  leftSection={
                    <IconRefresh
                      size={15}
                    />
                  }
                  onClick={() => {
                    void loadPlans();
                  }}
                >
                  Retry
                </Button>
              </Stack>
            </Alert>
          ) : null}


          {plansStatus ===
            "ready" &&
          plans.length ===
            0 ? (
            <Paper
              withBorder
              radius="md"
              p="lg"
              mt="lg"
              className={
                classes.emptyState
              }
            >
              <ThemeIcon
                variant="light"
                radius="xl"
                size={44}
              >
                <IconCalendarEvent
                  size={22}
                />
              </ThemeIcon>

              <Text
                fw={700}
                mt="sm"
              >
                No study plans yet
              </Text>

              <Text
                size="sm"
                c="dimmed"
                ta="center"
              >
                Create a manual plan or
                generate one from your
                academic tasks.
              </Text>
            </Paper>
          ) : null}


          {plansStatus ===
            "ready" &&
          plans.length >
            0 ? (
            <Stack
              gap="sm"
              mt="lg"
            >
              {plans.map(
                (
                  plan,
                ) => {
                  const selected =
                    plan.id ===
                    selectedPlanId;

                  return (
                    <UnstyledButton
                      key={
                        plan.id
                      }
                      className={[
                        classes.planButton,
                        selected
                          ? classes.planButtonSelected
                          : "",
                      ].join(
                        " ",
                      )}
                      aria-pressed={
                        selected
                      }
                      onClick={() =>
                        selectPlan(
                          plan,
                        )
                      }
                    >
                      <Group
                        justify="space-between"
                        align="flex-start"
                        wrap="nowrap"
                      >
                        <div>
                          <Text fw={700}>
                            {
                              plan.title
                            }
                          </Text>

                          <Text
                            size="xs"
                            c="dimmed"
                            mt={3}
                          >
                            {formatPlanRange(
                              plan,
                            )}
                          </Text>
                        </div>

                        <Badge
                          size="xs"
                          variant="light"
                          color={
                            plan.generation_mode ===
                            "generated"
                              ? "violet"
                              : "blue"
                          }
                        >
                          {
                            plan.generation_mode
                          }
                        </Badge>
                      </Group>
                    </UnstyledButton>
                  );
                },
              )}
            </Stack>
          ) : null}
        </Card>


        <Card
          withBorder
          radius="lg"
          padding="lg"
          className={
            classes.calendarPanel
          }
        >
          {!selectedPlan ? (
            <div
              className={
                classes.noSelection
              }
            >
              <ThemeIcon
                size={54}
                radius="xl"
                variant="light"
              >
                <IconCalendarWeek
                  size={27}
                />
              </ThemeIcon>

              <Title
                order={3}
                mt="md"
              >
                Select a study plan
              </Title>

              <Text
                c="dimmed"
                ta="center"
                maw={420}
              >
                Choose one of your
                saved plans to review
                its scheduled sessions.
              </Text>
            </div>
          ) : (
            <Stack gap="lg">
              <Group
                justify="space-between"
                align="flex-start"
                gap="md"
              >
                <div>
                  <Group gap="sm">
                    <Title order={2}>
                      {
                        selectedPlan.title
                      }
                    </Title>

                    <Badge
                      variant="light"
                      color={
                        selectedPlan.generation_mode ===
                        "generated"
                          ? "violet"
                          : "blue"
                      }
                    >
                      {
                        selectedPlan.generation_mode
                      }
                    </Badge>

                    <Badge
                      variant="outline"
                    >
                      {
                        selectedPlan.status
                      }
                    </Badge>
                  </Group>

                  <Text
                    c="dimmed"
                    size="sm"
                    mt={4}
                  >
                    {formatPlanRange(
                      selectedPlan,
                    )}
                  </Text>
                </div>


                <Group
                  gap="xs"
                  className={
                    classes.planActions
                  }
                >
                  {selectedPlan.generation_mode ===
                  "generated" ? (
                    <Tooltip
                      label={
                        selectedPlanHasActiveTimer
                          ? (
                              "Finish the active study timer before "
                              + "regenerating this plan."
                            )
                          : (
                              "Rebuild generated sessions using your "
                              + "latest prioritized academic tasks."
                            )
                      }
                      withArrow
                      openDelay={400}
                    >
                      <span
                        className={
                          classes.tooltipTarget
                        }
                      >
                        <Button
                          size="xs"
                          variant="light"
                          leftSection={
                            <IconRefresh
                              size={15}
                            />
                          }
                          loading={
                            regenerationTasksLoading
                          }
                          disabled={
                            selectedPlanHasActiveTimer
                          }
                          onClick={() => {
                            void handleOpenRegeneratePlan();
                          }}
                        >
                          Regenerate
                        </Button>
                      </span>
                    </Tooltip>
                  ) : null}

                  <Tooltip
                    label="Add a manually scheduled study session to this plan."
                    withArrow
                    openDelay={400}
                  >
                    <span
                      className={
                        classes.tooltipTarget
                      }
                    >
                      <Button
                        size="xs"
                        leftSection={
                          <IconPlus
                            size={15}
                          />
                        }
                        disabled={
                          initialSubjects.length ===
                          0
                        }
                        onClick={() =>
                          setCreateSessionOpened(
                            true,
                          )
                        }
                      >
                        Add session
                      </Button>
                    </span>
                  </Tooltip>

                  <Tooltip
                    label={
                      selectedPlanHasActiveTimer
                        ? (
                            "Finish the active study timer before "
                            + "deleting this plan."
                          )
                        : (
                            "Delete this plan and all of its "
                            + "scheduled sessions."
                          )
                    }
                    withArrow
                    openDelay={400}
                  >
                    <span
                      className={
                        classes.tooltipTarget
                      }
                    >
                      <Button
                        size="xs"
                        color="red"
                        variant="light"
                        leftSection={
                          <IconTrash
                            size={15}
                          />
                        }
                        disabled={
                          selectedPlanHasActiveTimer
                        }
                        onClick={() =>
                          setDeletePlanOpened(
                            true,
                          )
                        }
                      >
                        Delete plan
                      </Button>
                    </span>
                  </Tooltip>

                  <Tooltip
                    label="Show the previous week."
                    withArrow
                    openDelay={400}
                  >
                    <Button
                      variant="default"
                      size="xs"
                      aria-label="Previous week"
                      onClick={
                        goToPreviousWeek
                      }
                    >
                      <IconChevronLeft
                        size={17}
                      />
                    </Button>
                  </Tooltip>

                  <Tooltip
                    label="Return the calendar to the current week."
                    withArrow
                    openDelay={400}
                  >
                    <Button
                      variant="default"
                      size="xs"
                      onClick={
                        goToCurrentWeek
                      }
                    >
                      Today
                    </Button>
                  </Tooltip>

                  <Tooltip
                    label="Show the next week."
                    withArrow
                    openDelay={400}
                  >
                    <Button
                      variant="default"
                      size="xs"
                      aria-label="Next week"
                      onClick={
                        goToNextWeek
                      }
                    >
                      <IconChevronRight
                        size={17}
                      />
                    </Button>
                  </Tooltip>
                </Group>
              </Group>


              {actionError ? (
                <Alert
                  color="red"
                  title="Study plan action failed"
                  icon={
                    <IconAlertCircle
                      size={18}
                    />
                  }
                  withCloseButton
                  onClose={() =>
                    setActionError(
                      null,
                    )
                  }
                >
                  {actionError}
                </Alert>
              ) : null}


              {sessionsStatus ===
              "loading" ? (
                <Group
                  justify="center"
                  py="lg"
                >
                  <Loader
                    size="sm"
                    aria-label="Loading study sessions"
                  />

                  <Text
                    size="sm"
                    c="dimmed"
                  >
                    Loading sessions…
                  </Text>
                </Group>
              ) : null}


              {sessionsStatus ===
              "error" ? (
                <Alert
                  color="red"
                  title="Schedule unavailable"
                  icon={
                    <IconAlertCircle
                      size={18}
                    />
                  }
                >
                  <Stack gap="sm">
                    <Text size="sm">
                      {
                        sessionsError
                      }
                    </Text>

                    <Button
                      size="xs"
                      variant="light"
                      leftSection={
                        <IconRefresh
                          size={15}
                        />
                      }
                      onClick={() => {
                        void loadSessions(
                          selectedPlan.id,
                        );
                      }}
                    >
                      Retry
                    </Button>
                  </Stack>
                </Alert>
              ) : null}


              <ScrollArea
                type="auto"
                offsetScrollbars
              >
                <div
                  className={
                    classes.weekGrid
                  }
                >
                  {weekDays.map(
                    (
                      day,
                    ) => {
                      const key =
                        localDateKey(
                          day,
                        );

                      const daySessions =
                        sessionsByDay.get(
                          key,
                        ) ??
                        [];

                      return (
                        <Paper
                          key={key}
                          withBorder
                          radius="md"
                          p="sm"
                          className={
                            classes.dayColumn
                          }
                        >
                          <div
                            className={
                              classes.dayHeader
                            }
                          >
                            <Text
                              size="xs"
                              c="dimmed"
                              tt="uppercase"
                              fw={700}
                            >
                              {new Intl.DateTimeFormat(
                                undefined,
                                {
                                  weekday:
                                    "short",
                                },
                              ).format(
                                day,
                              )}
                            </Text>

                            <Text
                              fw={800}
                              size="lg"
                            >
                              {
                                day.getDate()
                              }
                            </Text>
                          </div>

                          <Stack
                            gap="sm"
                            mt="sm"
                          >
                            {daySessions.length ===
                            0 ? (
                              <Text
                                size="xs"
                                c="dimmed"
                                className={
                                  classes.noSessions
                                }
                              >
                                No sessions
                              </Text>
                            ) : (
                              daySessions.map(
                                renderSessionCard,
                              )
                            )}
                          </Stack>
                        </Paper>
                      );
                    },
                  )}
                </div>
              </ScrollArea>
            </Stack>
          )}
        </Card>
      </div>


      <GenerateStudyPlanModal
        opened={
          generatePlanOpened
        }
        onClose={
          handleCloseGeneratePlan
        }
        tasks={
          generationTasks
        }
        onGenerated={
          handleGeneratedPlan
        }
      />


      <RegenerateStudyPlanModal
        opened={
          regeneratePlanOpened
        }
        onClose={
          handleCloseRegeneratePlan
        }
        studyPlan={
          selectedPlan
        }
        tasks={
          regenerationTasks
        }
        onRegenerated={
          handleRegeneratedPlan
        }
      />


      <CreateStudyPlanModal
        opened={
          createPlanOpened
        }
        onClose={() =>
          setCreatePlanOpened(
            false,
          )
        }
        onCreated={
          handlePlanCreated
        }
      />


      {selectedPlan ? (
        <CreateStudySessionModal
          opened={
            createSessionOpened
          }
          onClose={() =>
            setCreateSessionOpened(
              false,
            )
          }
          studyPlan={
            selectedPlan
          }
          subjects={
            initialSubjects
          }
          onCreated={
            handleSessionCreated
          }
        />
      ) : null}


      <Modal
        opened={
          deletePlanOpened
        }
        onClose={() => {
          if (
            !deletingPlan
          ) {
            setDeletePlanOpened(
              false,
            );
          }
        }}
        title="Delete study plan?"
        centered
      >
        <Stack>
          <Text size="sm">
            This will permanently
            delete the study plan and
            its scheduled sessions.
          </Text>

          <Group
            justify="flex-end"
          >
            <Button
              variant="default"
              disabled={
                deletingPlan
              }
              onClick={() =>
                setDeletePlanOpened(
                  false,
                )
              }
            >
              Cancel
            </Button>

            <Button
              color="red"
              loading={
                deletingPlan
              }
              onClick={() => {
                void handleDeletePlan();
              }}
            >
              Delete plan
            </Button>
          </Group>
        </Stack>
      </Modal>


      <Modal
        opened={
          sessionToDelete !==
          null
        }
        onClose={() => {
          if (
            !deletingSession
          ) {
            setSessionToDelete(
              null,
            );
          }
        }}
        title="Delete study session?"
        centered
      >
        <Stack>
          <Text size="sm">
            This session will be
            removed from the study
            plan.
          </Text>

          <Group
            justify="flex-end"
          >
            <Button
              variant="default"
              disabled={
                deletingSession
              }
              onClick={() =>
                setSessionToDelete(
                  null,
                )
              }
            >
              Cancel
            </Button>

            <Button
              color="red"
              loading={
                deletingSession
              }
              onClick={() => {
                void handleDeleteSession();
              }}
            >
              Delete session
            </Button>
          </Group>
        </Stack>
      </Modal>
    </main>
  );
}