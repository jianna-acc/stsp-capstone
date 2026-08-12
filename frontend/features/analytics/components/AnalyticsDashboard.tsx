// File: /frontend/features/analytics/components/AnalyticsDashboard.tsx
// Purpose: Displays authenticated study performance,
// compact charts, weekly Study Time, and expandable topic evidence.

"use client";

import {
  BarChart,
} from "@mantine/charts";
import {
  Alert,
  Badge,
  Button,
  Container,
  Group,
  Loader,
  Paper,
  Progress,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconBook2,
  IconBooks,
  IconCards,
  IconCircleCheck,
  IconClock,
  IconListCheck,
  IconRefresh,
  IconTargetArrow,
  IconTrendingUp,
} from "@tabler/icons-react";
import type {
  ReactNode,
} from "react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AnalyticsApiError,
  getAnalyticsOverview,
} from "@/features/analytics/api";
import {
  ANALYTICS_PERIOD_OPTIONS,
} from "@/features/analytics/types";

import type {
  AnalyticsCountMetric,
  AnalyticsMetric,
  AnalyticsOverviewResponse,
  AnalyticsPeriod,
  AnalyticsTopicPerformance,
} from "@/features/analytics/types";

import classes from "./AnalyticsDashboard.module.css";


const TOPIC_PREVIEW_LIMIT =
  3;


interface MetricCardProps {
  title: string;
  value: string;
  description: string;
  icon: ReactNode;
  color: string;
}


interface TopicPanelProps {
  title: string;
  description: string;
  topics: AnalyticsTopicPerformance[];
  strong: boolean;
  expanded: boolean;
  onToggle: () => void;
}


interface PerformanceChartRow {
  metric: string;
  score: number;
}


interface WeeklyStudyChartRow {
  week: string;
  minutes: number;
}


function formatPercentage(
  value: number,
): string {
  const rounded =
    Math.round(
      value * 100,
    ) / 100;

  return `${rounded}%`;
}


function formatStudyMinutes(
  value: number,
): string {
  const rounded =
    Math.round(
      value * 10,
    ) / 10;

  if (
    Number.isInteger(
      rounded,
    )
  ) {
    return `${rounded} min`;
  }

  return `${rounded.toFixed(
    1,
  )} min`;
}


function formatWeekDate(
  value: string,
): string {
  const parsed =
    new Date(
      `${value}T00:00:00Z`,
    );

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month:
        "short",

      day:
        "numeric",

      timeZone:
        "UTC",
    },
  ).format(
    parsed,
  );
}


function formatWeekRange(
  weekStart: string,
  weekEnd: string,
): string {
  return [
    formatWeekDate(
      weekStart,
    ),
    " – ",
    formatWeekDate(
      weekEnd,
    ),
  ].join(
    "",
  );
}


function getCountValue(
  metric: AnalyticsCountMetric,
): string {
  if (
    metric.availability ===
      "unavailable" ||
    metric.value === null
  ) {
    return "—";
  }

  return String(
    metric.value,
  );
}


function getCountDescription(
  metric: AnalyticsCountMetric,
): string {
  if (
    metric.availability ===
      "unavailable"
  ) {
    return (
      metric.message ??
      "This metric is not available yet."
    );
  }

  if (
    metric.value === null
  ) {
    return (
      metric.message ??
      "No current data is available."
    );
  }

  return "Current inventory";
}


function getPercentageValue(
  metric: AnalyticsMetric,
): string {
  if (
    metric.availability ===
      "unavailable" ||
    metric.value === null
  ) {
    return "—";
  }

  return formatPercentage(
    metric.value,
  );
}


function getMetricDescription(
  metric: AnalyticsMetric,
): string {
  if (
    metric.availability ===
      "unavailable"
  ) {
    return (
      metric.message ??
      "This metric is not available yet."
    );
  }

  if (
    metric.value === null
  ) {
    return (
      metric.message ??
      "No performance evidence is available for this period."
    );
  }

  return (
    `Sample size: ${metric.sample_size}`
  );
}


function getStudyTimeValue(
  metric: AnalyticsMetric,
): string {
  if (
    metric.availability ===
      "unavailable" ||
    metric.value === null
  ) {
    return "—";
  }

  return formatStudyMinutes(
    metric.value,
  );
}


function getStudyTimeDescription(
  metric: AnalyticsMetric,
): string {
  if (
    metric.availability ===
      "unavailable"
  ) {
    return (
      metric.message ??
      "Study Time is not available yet."
    );
  }

  if (
    metric.value === null
  ) {
    return (
      metric.message ??
      "No completed study sessions are available for this period."
    );
  }

  const label =
    metric.sample_size ===
      1
      ? "session"
      : "sessions";

  return (
    `${metric.sample_size} completed ${label}`
  );
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


function MetricCard({
  title,
  value,
  description,
  icon,
  color,
}: Readonly<MetricCardProps>) {
  return (
    <Paper
      withBorder
      radius="lg"
      p="md"
      className={
        classes.metricCard
      }
    >
      <Group
        align="center"
        gap="md"
        wrap="nowrap"
      >
        <ThemeIcon
          variant="light"
          color={color}
          radius="md"
          size={38}
          className={
            classes.metricIcon
          }
        >
          {icon}
        </ThemeIcon>

        <div
          className={
            classes.metricContent
          }
        >
          <Text
            size="xs"
            c="dimmed"
          >
            {title}
          </Text>

          <Text
            fw={800}
            className={
              classes.metricValue
            }
          >
            {value}
          </Text>

          <Text
            size="xs"
            c="dimmed"
            className={
              classes.metricDescription
            }
          >
            {description}
          </Text>
        </div>
      </Group>
    </Paper>
  );
}


function TopicPanel({
  title,
  description,
  topics,
  strong,
  expanded,
  onToggle,
}: Readonly<TopicPanelProps>) {
  const visibleTopics =
    expanded
      ? topics
      : topics.slice(
          0,
          TOPIC_PREVIEW_LIMIT,
        );

  const canExpand =
    topics.length >
    TOPIC_PREVIEW_LIMIT;

  return (
    <Paper
      withBorder
      radius="lg"
      p="md"
      className={
        classes.topicPanel
      }
    >
      <Stack gap="md">
        <Group
          gap="sm"
          align="flex-start"
          wrap="nowrap"
        >
          <ThemeIcon
            variant="light"
            color={
              strong
                ? "green"
                : "orange"
            }
            radius="md"
            size={34}
          >
            {strong ? (
              <IconTrendingUp
                size={17}
              />
            ) : (
              <IconTargetArrow
                size={17}
              />
            )}
          </ThemeIcon>

          <div>
            <Text
              fw={700}
              size="sm"
            >
              {title}
            </Text>

            <Text
              size="xs"
              c="dimmed"
            >
              {description}
            </Text>
          </div>
        </Group>


        {topics.length ===
        0 ? (
          <Text
            size="sm"
            c="dimmed"
          >
            No Quiz topics are
            available in this group
            for the selected period.
          </Text>
        ) : (
          <>
            <Stack gap="sm">
              {visibleTopics.map(
                (
                  topic,
                ) => (
                  <div
                    key={
                      topic.topic
                    }
                    className={
                      classes.topicRow
                    }
                  >
                    <Group
                      justify="space-between"
                      align="center"
                      gap="sm"
                      wrap="nowrap"
                      mb={4}
                    >
                      <div
                        className={
                          classes.topicName
                        }
                      >
                        <Text
                          size="xs"
                          fw={650}
                          lineClamp={1}
                          title={
                            topic.topic
                          }
                        >
                          {topic.topic}
                        </Text>

                        <Text
                          size="xs"
                          c="dimmed"
                        >
                          {
                            topic.sample_size
                          }{" "}
                          {
                            topic.sample_size ===
                            1
                              ? "answer"
                              : "answers"
                          }
                        </Text>
                      </div>

                      <Text
                        size="xs"
                        fw={700}
                      >
                        {
                          formatPercentage(
                            topic.score_percent,
                          )
                        }
                      </Text>
                    </Group>

                    <Progress
                      value={
                        topic.score_percent
                      }
                      color={
                        strong
                          ? "green"
                          : "orange"
                      }
                      radius="xl"
                      size="sm"
                    />
                  </div>
                ),
              )}
            </Stack>

            {canExpand ? (
              <Button
                type="button"
                size="xs"
                variant="subtle"
                color={
                  strong
                    ? "green"
                    : "orange"
                }
                onClick={
                  onToggle
                }
                aria-expanded={
                  expanded
                }
                className={
                  classes.topicToggle
                }
              >
                {expanded
                  ? "Show less"
                  : (
                      `Show all (${topics.length})`
                    )}
              </Button>
            ) : null}
          </>
        )}
      </Stack>
    </Paper>
  );
}


export function AnalyticsDashboard() {
  const [
    period,
    setPeriod,
  ] =
    useState<AnalyticsPeriod>(
      "all_time",
    );

  const [
    overview,
    setOverview,
  ] = useState<
    AnalyticsOverviewResponse | null
  >(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    retryVersion,
    setRetryVersion,
  ] = useState(
    0,
  );

  const [
    strongTopicsExpanded,
    setStrongTopicsExpanded,
  ] = useState(
    false,
  );

  const [
    weakTopicsExpanded,
    setWeakTopicsExpanded,
  ] = useState(
    false,
  );


  useEffect(
    () => {
      const controller =
        new AbortController();

      void getAnalyticsOverview(
        period,
        {
          signal:
            controller.signal,
        },
      )
        .then(
          (
            result,
          ) => {
            if (
              controller
                .signal
                .aborted
            ) {
              return;
            }

            setOverview(
              result,
            );

            setErrorMessage(
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
              isAbortError(
                error,
              )
            ) {
              return;
            }

            setOverview(
              null,
            );

            setErrorMessage(
              error instanceof
                AnalyticsApiError
                ? error.message
                : (
                    "Analytics could not "
                    + "be loaded."
                  ),
            );
          },
        )
        .finally(
          () => {
            if (
              !controller
                .signal
                .aborted
            ) {
              setLoading(
                false,
              );
            }
          },
        );

      return () => {
        controller.abort();
      };
    },
    [
      period,
      retryVersion,
    ],
  );


  const performanceChartData =
    useMemo<
      PerformanceChartRow[]
    >(
      () => {
        if (
          !overview
        ) {
          return [];
        }

        const rows:
          PerformanceChartRow[] =
          [];

        if (
          overview
            .quiz_accuracy_percent
            .availability ===
              "available" &&
          overview
            .quiz_accuracy_percent
            .value !== null
        ) {
          rows.push({
            metric:
              "Quiz accuracy",

            score:
              overview
                .quiz_accuracy_percent
                .value,
          });
        }

        if (
          overview
            .flashcard_performance_percent
            .availability ===
              "available" &&
          overview
            .flashcard_performance_percent
            .value !== null
        ) {
          rows.push({
            metric:
              "Flashcard recall",

            score:
              overview
                .flashcard_performance_percent
                .value,
          });
        }

        return rows;
      },
      [
        overview,
      ],
    );


  const weeklyStudyChartData =
    useMemo<
      WeeklyStudyChartRow[]
    >(
      () => {
        if (
          !overview
        ) {
          return [];
        }

        return overview
          .study_time_by_week
          .map(
            (
              week,
            ) => ({
              week:
                formatWeekRange(
                  week.week_start,
                  week.week_end,
                ),

              minutes:
                week.study_minutes,
            }),
          );
      },
      [
        overview,
      ],
    );


  const weeklyChartMinWidth =
    Math.max(
      420,
      weeklyStudyChartData
        .length * 100,
    );


  function handlePeriodChange(
    value: string,
  ): void {
    const nextPeriod =
      value as AnalyticsPeriod;

    if (
      nextPeriod ===
      period
    ) {
      return;
    }

    setLoading(
      true,
    );

    setErrorMessage(
      null,
    );

    setOverview(
      null,
    );

    setStrongTopicsExpanded(
      false,
    );

    setWeakTopicsExpanded(
      false,
    );

    setPeriod(
      nextPeriod,
    );
  }


  function retry():
    void {
    setLoading(
      true,
    );

    setErrorMessage(
      null,
    );

    setOverview(
      null,
    );

    setRetryVersion(
      (
        current,
      ) =>
        current + 1,
    );
  }


  return (
    <Container
      size="xl"
      py={{
        base:
          20,

        sm:
          28,
      }}
      className={
        classes.dashboard
      }
    >
      <Stack gap="lg">
        <Group
          justify="space-between"
          align="flex-end"
          gap="lg"
          className={
            classes.header
          }
        >
          <div>
            <Text
              c="violet.7"
              fw={700}
              size="xs"
            >
              Study analytics
            </Text>

            <Title order={1}>
              Performance Overview
            </Title>

            <Text
              c="dimmed"
              mt={2}
              size="sm"
              maw={680}
            >
              Track performance,
              materials, and actual
              focus time in one place.
            </Text>
          </div>

          <Stack
            gap={4}
            className={
              classes.periodContainer
            }
          >
            <Text
              size="xs"
              fw={700}
              c="dimmed"
            >
              REPORTING PERIOD
            </Text>

            <SegmentedControl
              value={
                period
              }
              onChange={
                handlePeriodChange
              }
              data={[
                ...ANALYTICS_PERIOD_OPTIONS,
              ]}
              disabled={
                loading
              }
              fullWidth
              size="sm"
            />
          </Stack>
        </Group>


        {loading && (
          <Paper
            withBorder
            radius="lg"
            p="lg"
          >
            <Group
              justify="center"
              py="lg"
            >
              <Loader
                size="sm"
              />

              <Text
                c="dimmed"
                size="sm"
              >
                Loading your
                Analytics...
              </Text>
            </Group>
          </Paper>
        )}


        {!loading &&
          errorMessage && (
            <Alert
              color="red"
              title="Analytics could not be loaded"
            >
              <Stack gap="sm">
                <Text size="sm">
                  {errorMessage}
                </Text>

                <Group>
                  <Button
                    type="button"
                    size="xs"
                    variant="light"
                    color="red"
                    leftSection={
                      <IconRefresh
                        size={15}
                      />
                    }
                    onClick={
                      retry
                    }
                  >
                    Retry
                  </Button>
                </Group>
              </Stack>
            </Alert>
          )}


        {!loading &&
          overview && (
            <>
              <Group
                justify="space-between"
                align="center"
                gap="md"
              >
                <div>
                  <Title
                    order={2}
                    size="h4"
                  >
                    Learning Overview
                  </Title>

                  <Text
                    size="xs"
                    c="dimmed"
                  >
                    Current inventory and
                    selected-period
                    performance.
                  </Text>
                </div>

                <Badge
                  variant="light"
                  color={
                    overview
                      .data_state ===
                    "ready"
                      ? "green"
                      : "yellow"
                  }
                >
                  {
                    overview
                      .data_state ===
                    "ready"
                      ? (
                          "All metrics ready"
                        )
                      : "Partial data"
                  }
                </Badge>
              </Group>


              <SimpleGrid
                cols={{
                  base:
                    1,

                  xs:
                    2,

                  lg:
                    3,
                }}
                spacing="md"
              >
                <MetricCard
                  title="Subjects"
                  value={
                    getCountValue(
                      overview
                        .subject_count,
                    )
                  }
                  description={
                    getCountDescription(
                      overview
                        .subject_count,
                    )
                  }
                  color="violet"
                  icon={
                    <IconBooks
                      size={19}
                    />
                  }
                />

                <MetricCard
                  title="Study Materials"
                  value={
                    getCountValue(
                      overview
                        .study_material_count,
                    )
                  }
                  description={
                    getCountDescription(
                      overview
                        .study_material_count,
                    )
                  }
                  color="blue"
                  icon={
                    <IconBook2
                      size={19}
                    />
                  }
                />

                <MetricCard
                  title="Ready Materials"
                  value={
                    getCountValue(
                      overview
                        .ready_study_material_count,
                    )
                  }
                  description={
                    getCountDescription(
                      overview
                        .ready_study_material_count,
                    )
                  }
                  color="green"
                  icon={
                    <IconCircleCheck
                      size={19}
                    />
                  }
                />

                <MetricCard
                  title="Quiz Accuracy"
                  value={
                    getPercentageValue(
                      overview
                        .quiz_accuracy_percent,
                    )
                  }
                  description={
                    getMetricDescription(
                      overview
                        .quiz_accuracy_percent,
                    )
                  }
                  color="violet"
                  icon={
                    <IconListCheck
                      size={19}
                    />
                  }
                />

                <MetricCard
                  title="Flashcard Recall"
                  value={
                    getPercentageValue(
                      overview
                        .flashcard_performance_percent,
                    )
                  }
                  description={
                    getMetricDescription(
                      overview
                        .flashcard_performance_percent,
                    )
                  }
                  color="teal"
                  icon={
                    <IconCards
                      size={19}
                    />
                  }
                />

                <MetricCard
                  title="Study Time"
                  value={
                    getStudyTimeValue(
                      overview
                        .study_minutes,
                    )
                  }
                  description={
                    getStudyTimeDescription(
                      overview
                        .study_minutes,
                    )
                  }
                  color="gray"
                  icon={
                    <IconClock
                      size={19}
                    />
                  }
                />
              </SimpleGrid>


              <SimpleGrid
                cols={{
                  base:
                    1,

                  lg:
                    2,
                }}
                spacing="md"
                className={
                  classes.chartGrid
                }
              >
                <Paper
                  withBorder
                  radius="lg"
                  p="md"
                  className={
                    classes.chartCard
                  }
                >
                  <Stack gap="sm">
                    <div>
                      <Title
                        order={3}
                        size="h5"
                      >
                        Weekly Study Time
                      </Title>

                      <Text
                        size="xs"
                        c="dimmed"
                        className={
                          classes.weeklyNote
                        }
                      >
                        Completed focus
                        minutes by
                        Monday–Sunday week.
                        Breaks and pauses
                        are excluded.
                      </Text>
                    </div>

                    {
                      weeklyStudyChartData
                        .length ===
                      0 ? (
                        <Paper
                          withBorder
                          radius="md"
                          p="lg"
                          className={
                            classes.emptyState
                          }
                        >
                          <Text
                            ta="center"
                            c="dimmed"
                            size="xs"
                          >
                            Complete a study
                            session to build
                            your weekly chart.
                          </Text>
                        </Paper>
                      ) : (
                        <div
                          className={
                            classes.weeklyChartScroll
                          }
                        >
                          <div
                            className={
                              classes.weeklyChartInner
                            }
                            style={{
                              minWidth:
                                `${weeklyChartMinWidth}px`,
                            }}
                          >
                            <BarChart
                              h={210}
                              data={
                                weeklyStudyChartData
                              }
                              dataKey="week"
                              series={[
                                {
                                  name:
                                    "minutes",

                                  label:
                                    "Study Time",

                                  color:
                                    "violet.6",
                                },
                              ]}
                              valueFormatter={(
                                value,
                              ) =>
                                String(
                                  Math.round(
                                    value *
                                      100,
                                  ) /
                                    100,
                                )
                              }
                              unit=" min"
                              gridAxis="y"
                              tickLine="y"
                              withTooltip
                            />
                          </div>
                        </div>
                      )
                    }
                  </Stack>
                </Paper>


                <Paper
                  withBorder
                  radius="lg"
                  p="md"
                  className={
                    classes.chartCard
                  }
                >
                  <Stack gap="sm">
                    <div>
                      <Title
                        order={3}
                        size="h5"
                      >
                        Performance
                        Comparison
                      </Title>

                      <Text
                        size="xs"
                        c="dimmed"
                      >
                        Quiz accuracy and
                        Flashcard recall for
                        this period.
                      </Text>
                    </div>

                    {
                      performanceChartData
                        .length ===
                      0 ? (
                        <Paper
                          withBorder
                          radius="md"
                          p="lg"
                          className={
                            classes.emptyState
                          }
                        >
                          <Text
                            ta="center"
                            c="dimmed"
                            size="xs"
                          >
                            Complete a Quiz
                            or review
                            Flashcards to
                            build this chart.
                          </Text>
                        </Paper>
                      ) : (
                        <BarChart
                          h={210}
                          data={
                            performanceChartData
                          }
                          dataKey="metric"
                          series={[
                            {
                              name:
                                "score",

                              label:
                                "Performance",

                              color:
                                "violet.6",
                            },
                          ]}
                          yAxisProps={{
                            domain: [
                              0,
                              100,
                            ],
                          }}
                          valueFormatter={(
                            value,
                          ) =>
                            String(
                              Math.round(
                                value *
                                  100,
                              ) /
                                100,
                            )
                          }
                          unit="%"
                          gridAxis="y"
                          tickLine="y"
                          withTooltip
                        />
                      )
                    }
                  </Stack>
                </Paper>
              </SimpleGrid>


              <Group
                justify="space-between"
                align="flex-end"
              >
                <div>
                  <Title
                    order={2}
                    size="h4"
                  >
                    Quiz Topic Performance
                  </Title>

                  <Text
                    size="xs"
                    c="dimmed"
                  >
                    Showing the most useful
                    topic evidence first.
                  </Text>
                </div>
              </Group>


              <SimpleGrid
                cols={{
                  base:
                    1,

                  md:
                    2,
                }}
                spacing="md"
              >
                <TopicPanel
                  title="Strong Topics"
                  description="At or above the strong-topic threshold"
                  topics={
                    overview
                      .strong_topics
                  }
                  strong
                  expanded={
                    strongTopicsExpanded
                  }
                  onToggle={() => {
                    setStrongTopicsExpanded(
                      (
                        current,
                      ) =>
                        !current,
                    );
                  }}
                />

                <TopicPanel
                  title="Topics to Review"
                  description="Below the strong-topic threshold"
                  topics={
                    overview
                      .weak_topics
                  }
                  strong={
                    false
                  }
                  expanded={
                    weakTopicsExpanded
                  }
                  onToggle={() => {
                    setWeakTopicsExpanded(
                      (
                        current,
                      ) =>
                        !current,
                    );
                  }}
                />
              </SimpleGrid>
            </>
          )}
      </Stack>
    </Container>
  );
}