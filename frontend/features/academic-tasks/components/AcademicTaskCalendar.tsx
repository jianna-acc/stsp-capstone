// File: /frontend/features/academic-tasks/components/AcademicTaskCalendar.tsx
// Purpose: Displays Academic Tasks by deadline in navigable
// week and month calendar views.

"use client";

import {
  Badge,
  Button,
  Card,
  Group,
  Paper,
  ScrollArea,
  SegmentedControl,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconChevronLeft,
  IconChevronRight,
} from "@tabler/icons-react";
import {
  useMemo,
  useState,
} from "react";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  addDays,
  addMonths,
  formatMonthLabel,
  formatWeekRange,
  getMonthGridDays,
  getWeekDays,
  groupAcademicTasksByDeadlineDay,
  isSameMonth,
  localDateKey,
} from "../academic-task-calendar";
import type {
  AcademicTaskPriorityBreakdown,
  AcademicTaskResponse,
} from "../types";

import {
  AcademicTaskCalendarItem,
} from "./AcademicTaskCalendarItem";

import classes from "./AcademicTasksWorkspace.module.css";

interface AcademicTaskCalendarProps {
  tasks:
    AcademicTaskResponse[];

  priorityByTaskId:
    Record<
      string,
      AcademicTaskPriorityBreakdown
    >;

  subjects:
    SubjectSummary[];

  selectedTaskId:
    string |
    null;

  onTaskSelect: (
    task:
      AcademicTaskResponse,
  ) => void;
}

type CalendarView =
  | "week"
  | "month";

const WEEKDAY_LABELS = [
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
  "Sun",
] as const;

export function AcademicTaskCalendar({
  tasks,
  priorityByTaskId,
  subjects,
  selectedTaskId,
  onTaskSelect,
}: AcademicTaskCalendarProps) {
  const [
    calendarAnchor,
    setCalendarAnchor,
  ] =
    useState<Date>(
      () =>
        new Date(),
    );

  const [
    viewMode,
    setViewMode,
  ] =
    useState<CalendarView>(
      "week",
    );

  const weekDays =
    useMemo(
      () =>
        getWeekDays(
          calendarAnchor,
        ),
      [
        calendarAnchor,
      ],
    );

  const monthDays =
    useMemo(
      () =>
        getMonthGridDays(
          calendarAnchor,
        ),
      [
        calendarAnchor,
      ],
    );

  /*
   * Cancelled tasks remain stored but do not
   * appear on the active calendar.
   */
  const calendarTasks =
    useMemo(
      () =>
        tasks.filter(
          (
            task,
          ) =>
            task.status !==
            "cancelled",
        ),
      [
        tasks,
      ],
    );

  const tasksByDay =
    useMemo(
      () =>
        groupAcademicTasksByDeadlineDay(
          calendarTasks,
        ),
      [
        calendarTasks,
      ],
    );

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

  const todayKey =
    localDateKey(
      new Date(),
    );

  const visibleTaskCount =
    useMemo(
      () => {
        if (
          viewMode ===
          "month"
        ) {
          return calendarTasks.filter(
            (
              task,
            ) => {
              const deadline =
                new Date(
                  task.deadline,
                );

              return (
                !Number.isNaN(
                  deadline.getTime(),
                ) &&
                isSameMonth(
                  deadline,
                  calendarAnchor,
                )
              );
            },
          ).length;
        }

        const firstDay =
          weekDays[
            0
          ];

        const lastDay =
          weekDays[
            weekDays.length -
              1
          ];

        if (
          !firstDay ||
          !lastDay
        ) {
          return 0;
        }

        const startKey =
          localDateKey(
            firstDay,
          );

        const endKey =
          localDateKey(
            lastDay,
          );

        return calendarTasks.filter(
          (
            task,
          ) => {
            const deadline =
              new Date(
                task.deadline,
              );

            if (
              Number.isNaN(
                deadline.getTime(),
              )
            ) {
              return false;
            }

            const key =
              localDateKey(
                deadline,
              );

            return (
              key >=
                startKey &&
              key <=
                endKey
            );
          },
        ).length;
      },
      [
        calendarAnchor,
        calendarTasks,
        viewMode,
        weekDays,
      ],
    );

  const calendarLabel =
    viewMode ===
    "week"
      ? formatWeekRange(
          weekDays,
        )
      : formatMonthLabel(
          calendarAnchor,
        );

  const countLabel =
    viewMode ===
    "week"
      ? visibleTaskCount ===
        1
        ? "task this week"
        : "tasks this week"
      : visibleTaskCount ===
          1
        ? "task this month"
        : "tasks this month";

  function goToPreviousPeriod() {
    setCalendarAnchor(
      (
        current,
      ) =>
        viewMode ===
        "week"
          ? addDays(
              current,
              -7,
            )
          : addMonths(
              current,
              -1,
            ),
    );
  }

  function goToNextPeriod() {
    setCalendarAnchor(
      (
        current,
      ) =>
        viewMode ===
        "week"
          ? addDays(
              current,
              7,
            )
          : addMonths(
              current,
              1,
            ),
    );
  }

  function goToToday() {
    setCalendarAnchor(
      new Date(),
    );
  }

  function renderTask(
    task:
      AcademicTaskResponse,
  ) {
    return (
      <AcademicTaskCalendarItem
        key={
          task.id
        }
        task={
          task
        }
        priority={
          priorityByTaskId[
            task.id
          ]
        }
        subject={
          subjectById.get(
            task.subject_id,
          )
        }
        selected={
          selectedTaskId ===
          task.id
        }
        onSelect={
          onTaskSelect
        }
      />
    );
  }

  return (
    <Card
      withBorder
      radius="lg"
      padding="lg"
      className={
        classes.calendarPanel
      }
    >
      <Stack
        gap="lg"
      >
        <Group
          justify="space-between"
          align="flex-start"
          className={
            classes.calendarToolbar
          }
        >
          <div>
            <Group
              gap="sm"
            >
              <Title
                order={
                  2
                }
              >
                Calendar
              </Title>

              <Badge
                variant="light"
                color="violet"
              >
                {
                  visibleTaskCount
                }{" "}
                {
                  countLabel
                }
              </Badge>
            </Group>

            <Text
              c="dimmed"
              size="sm"
              mt={
                3
              }
            >
              {
                calendarLabel
              }
            </Text>
          </div>

          <Group
            gap="xs"
            className={
              classes.calendarControls
            }
          >
            <SegmentedControl
              size="xs"
              value={
                viewMode
              }
              data={[
                {
                  value:
                    "week",

                  label:
                    "Week",
                },

                {
                  value:
                    "month",

                  label:
                    "Month",
                },
              ]}
              onChange={(
                value,
              ) => {
                if (
                  value ===
                    "week" ||
                  value ===
                    "month"
                ) {
                  setViewMode(
                    value,
                  );
                }
              }}
            />

            <Group
              gap={
                4
              }
              className={
                classes.calendarNavigation
              }
            >
              <Button
                variant="default"
                size="xs"
                aria-label={
                  viewMode ===
                  "week"
                    ? "Previous week"
                    : "Previous month"
                }
                onClick={
                  goToPreviousPeriod
                }
              >
                <IconChevronLeft
                  size={
                    17
                  }
                />
              </Button>

              <Button
                variant="default"
                size="xs"
                onClick={
                  goToToday
                }
              >
                Today
              </Button>

              <Button
                variant="default"
                size="xs"
                aria-label={
                  viewMode ===
                  "week"
                    ? "Next week"
                    : "Next month"
                }
                onClick={
                  goToNextPeriod
                }
              >
                <IconChevronRight
                  size={
                    17
                  }
                />
              </Button>
            </Group>
          </Group>
        </Group>

        {viewMode ===
        "week" ? (
          <ScrollArea
            type="auto"
            offsetScrollbars
          >
            <div
              className={
                classes.calendarWeekGrid
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

                  const dayTasks =
                    tasksByDay.get(
                      key,
                    ) ??
                    [];

                  const isToday =
                    key ===
                    todayKey;

                  return (
                    <Paper
                      key={
                        key
                      }
                      withBorder
                      radius="md"
                      p="sm"
                      className={
                        classes.calendarDay
                      }
                      data-today={
                        isToday
                          ? "true"
                          : undefined
                      }
                      aria-current={
                        isToday
                          ? "date"
                          : undefined
                      }
                    >
                      <div
                        className={
                          classes.calendarDayHeader
                        }
                      >
                        <Group
                          justify="space-between"
                          align="flex-start"
                          wrap="nowrap"
                        >
                          <div>
                            <Text
                              size="xs"
                              c={
                                isToday
                                  ? "violet"
                                  : "dimmed"
                              }
                              tt="uppercase"
                              fw={
                                700
                              }
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
                              fw={
                                800
                              }
                              size="lg"
                              c={
                                isToday
                                  ? "violet"
                                  : undefined
                              }
                            >
                              {
                                day.getDate()
                              }
                            </Text>
                          </div>

                          {isToday ? (
                            <Badge
                              size="xs"
                              color="violet"
                              variant="light"
                            >
                              Today
                            </Badge>
                          ) : null}
                        </Group>
                      </div>

                      <Stack
                        gap="xs"
                        mt="sm"
                      >
                        {dayTasks.length ===
                        0 ? (
                          <Text
                            size="xs"
                            c="dimmed"
                            className={
                              classes.calendarEmptyDay
                            }
                          >
                            No tasks due
                          </Text>
                        ) : (
                          dayTasks.map(
                            renderTask,
                          )
                        )}
                      </Stack>
                    </Paper>
                  );
                },
              )}
            </div>
          </ScrollArea>
        ) : (
          <ScrollArea
            type="auto"
            offsetScrollbars
          >
            <div
              className={
                classes.calendarMonthContainer
              }
            >
              <div
                className={
                  classes.calendarMonthWeekdays
                }
              >
                {WEEKDAY_LABELS.map(
                  (
                    label,
                  ) => (
                    <Text
                      key={
                        label
                      }
                      size="xs"
                      fw={
                        700
                      }
                      c="dimmed"
                      tt="uppercase"
                      ta="center"
                      className={
                        classes.calendarMonthWeekday
                      }
                    >
                      {
                        label
                      }
                    </Text>
                  ),
                )}
              </div>

              <div
                className={
                  classes.calendarMonthGrid
                }
              >
                {monthDays.map(
                  (
                    day,
                  ) => {
                    const key =
                      localDateKey(
                        day,
                      );

                    const dayTasks =
                      tasksByDay.get(
                        key,
                      ) ??
                      [];

                    const isToday =
                      key ===
                      todayKey;

                    const outsideMonth =
                      !isSameMonth(
                        day,
                        calendarAnchor,
                      );

                    return (
                      <Paper
                        key={
                          key
                        }
                        withBorder
                        radius="md"
                        p="sm"
                        className={[
                          classes.calendarDay,
                          classes.calendarMonthDay,
                        ].join(
                          " ",
                        )}
                        data-today={
                          isToday
                            ? "true"
                            : undefined
                        }
                        data-outside-month={
                          outsideMonth
                            ? "true"
                            : undefined
                        }
                        aria-current={
                          isToday
                            ? "date"
                            : undefined
                        }
                      >
                        <Group
                          justify="space-between"
                          align="center"
                          wrap="nowrap"
                          className={
                            classes.calendarMonthDayHeader
                          }
                        >
                          <Text
                            fw={
                              800
                            }
                            size="sm"
                            c={
                              isToday
                                ? "violet"
                                : outsideMonth
                                  ? "dimmed"
                                  : undefined
                            }
                          >
                            {
                              day.getDate()
                            }
                          </Text>

                          {isToday ? (
                            <Badge
                              size="xs"
                              color="violet"
                              variant="light"
                            >
                              Today
                            </Badge>
                          ) : null}
                        </Group>

                        <Stack
                          gap="xs"
                          mt="xs"
                        >
                          {dayTasks.map(
                            renderTask,
                          )}
                        </Stack>
                      </Paper>
                    );
                  },
                )}
              </div>
            </div>
          </ScrollArea>
        )}
      </Stack>
    </Card>
  );
}