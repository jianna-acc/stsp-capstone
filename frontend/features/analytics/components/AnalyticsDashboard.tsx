// File: /frontend/features/analytics/components/AnalyticsDashboard.tsx
// Purpose: Displays authenticated overall study performance,
// evidence availability, Quiz topics, and performance charts.

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
}


interface PerformanceChartRow {
  metric: string;
  score: number;
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

  const rounded =
    Math.round(
      metric.value,
    );

  return `${rounded} min`;
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
      p="lg"
      className={
        classes.metricCard
      }
    >
      <Stack
        gap="md"
        h="100%"
      >
        <Group
          justify="space-between"
          align="flex-start"
        >
          <ThemeIcon
            variant="light"
            color={color}
            radius="md"
            size={42}
          >
            {icon}
          </ThemeIcon>
        </Group>

        <div>
          <Text
            size="sm"
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
        </div>

        <Text
          size="xs"
          c="dimmed"
          mt="auto"
        >
          {description}
        </Text>
      </Stack>
    </Paper>
  );
}


function TopicPanel({
  title,
  description,
  topics,
  strong,
}: Readonly<TopicPanelProps>) {
  return (
    <Paper
      withBorder
      radius="lg"
      p="lg"
      className={
        classes.topicPanel
      }
    >
      <Stack gap="lg">
        <Group
          gap="sm"
          align="flex-start"
        >
          <ThemeIcon
            variant="light"
            color={
              strong
                ? "green"
                : "orange"
            }
            radius="md"
          >
            {strong ? (
              <IconTrendingUp
                size={18}
              />
            ) : (
              <IconTargetArrow
                size={18}
              />
            )}
          </ThemeIcon>

          <div>
            <Text fw={700}>
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

        {topics.length === 0 ? (
          <Text
            size="sm"
            c="dimmed"
          >
            No Quiz topics are available
            in this group for the selected
            period.
          </Text>
        ) : (
          <Stack gap="md">
            {topics.map(
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
                    align="flex-start"
                    gap="md"
                    wrap="nowrap"
                    mb={6}
                  >
                    <div>
                      <Text
                        size="sm"
                        fw={650}
                      >
                        {topic.topic}
                      </Text>

                      <Text
                        size="xs"
                        c="dimmed"
                      >
                        Sample size:{" "}
                        {
                          topic.sample_size
                        }
                      </Text>
                    </div>

                    <Text
                      size="sm"
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
                  />
                </div>
              ),
            )}
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}


export function AnalyticsDashboard() {
  const [
    period,
    setPeriod,
  ] = useState<AnalyticsPeriod>(
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
        base: 28,
        sm: 48,
      }}
      className={
        classes.dashboard
      }
    >
      <Stack gap="xl">
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
              size="sm"
            >
              Study analytics
            </Text>

            <Title order={1}>
              Performance Overview
            </Title>

            <Text
              c="dimmed"
              mt={4}
              maw={680}
            >
              Track your Quiz results,
              Flashcard recall, study
              materials, and topic-level
              performance.
            </Text>
          </div>

          <Stack
            gap={6}
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
            />
          </Stack>
        </Group>

        {loading && (
          <Paper
            withBorder
            radius="lg"
            p="xl"
          >
            <Group
              justify="center"
              py="xl"
            >
              <Loader
                size="sm"
              />

              <Text
                c="dimmed"
              >
                Loading your Analytics...
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
              >
                <div>
                  <Title
                    order={2}
                    size="h3"
                  >
                    Learning Overview
                  </Title>

                  <Text
                    size="sm"
                    c="dimmed"
                  >
                    Inventory counts are
                    current. Performance
                    metrics follow the
                    selected reporting
                    period.
                  </Text>
                </div>

                <Badge
                  variant="light"
                  color={
                    overview.data_state ===
                    "ready"
                      ? "green"
                      : "yellow"
                  }
                >
                  {
                    overview.data_state ===
                    "ready"
                      ? "All metrics ready"
                      : "Partial data"
                  }
                </Badge>
              </Group>

              <SimpleGrid
                cols={{
                  base: 1,
                  sm: 2,
                  lg: 3,
                }}
                spacing="lg"
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
                      size={21}
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
                      size={21}
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
                      size={21}
                    />
                  }
                />
              </SimpleGrid>

              <div>
                <Title
                  order={2}
                  size="h3"
                >
                  Performance
                </Title>

                <Text
                  size="sm"
                  c="dimmed"
                >
                  Quiz accuracy and
                  self-assessed Flashcard
                  recall for the selected
                  period.
                </Text>
              </div>

              <SimpleGrid
                cols={{
                  base: 1,
                  sm: 2,
                  lg: 3,
                }}
                spacing="lg"
              >
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
                      size={21}
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
                      size={21}
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
                    getMetricDescription(
                      overview
                        .study_minutes,
                    )
                  }
                  color="gray"
                  icon={
                    <IconClock
                      size={21}
                    />
                  }
                />
              </SimpleGrid>

              <Paper
                withBorder
                radius="lg"
                p={{
                  base: "md",
                  sm: "xl",
                }}
                className={
                  classes.chartCard
                }
              >
                <Stack gap="lg">
                  <div>
                    <Title
                      order={3}
                      size="h4"
                    >
                      Performance Comparison
                    </Title>

                    <Text
                      size="sm"
                      c="dimmed"
                    >
                      Compare the available
                      Quiz and Flashcard
                      performance evidence.
                    </Text>
                  </div>

                  {
                    performanceChartData
                      .length === 0 ? (
                      <Paper
                        withBorder
                        radius="md"
                        p="xl"
                        className={
                          classes.emptyState
                        }
                      >
                        <Text
                          ta="center"
                          c="dimmed"
                          size="sm"
                        >
                          Complete a Quiz or
                          rate Flashcards to
                          begin building your
                          performance chart.
                        </Text>
                      </Paper>
                    ) : (
                      <BarChart
                        h={280}
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
                              value * 100,
                            ) / 100,
                          )
                        }
                        unit="%"
                        gridAxis="y"
                        tickLine="y"
                        withTooltip
                        withBarValueLabel
                      />
                    )
                  }
                </Stack>
              </Paper>

              <div>
                <Title
                  order={2}
                  size="h3"
                >
                  Quiz Topic Performance
                </Title>

                <Text
                  size="sm"
                  c="dimmed"
                >
                  Topic classifications use
                  your completed Quiz-answer
                  evidence.
                </Text>
              </div>

              <SimpleGrid
                cols={{
                  base: 1,
                  md: 2,
                }}
                spacing="lg"
              >
                <TopicPanel
                  title="Strong Topics"
                  description="Currently at or above the strong-topic threshold"
                  topics={
                    overview
                      .strong_topics
                  }
                  strong
                />

                <TopicPanel
                  title="Topics to Review"
                  description="Currently below the strong-topic threshold"
                  topics={
                    overview
                      .weak_topics
                  }
                  strong={
                    false
                  }
                />
              </SimpleGrid>
            </>
          )}
      </Stack>
    </Container>
  );
}