// File: /frontend/features/quizzes/components/QuizResult.tsx
// Purpose: Displays final Quiz score plus strong and weak
// topic summaries after an attempt is completed.

"use client";

import {
  Badge,
  Button,
  Group,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconRefresh,
  IconTargetArrow,
  IconTrendingUp,
  IconTrophy,
} from "@tabler/icons-react";

import type {
  QuizAttemptResultResponse,
  QuizTopicResult,
} from "@/features/quizzes/types";

interface QuizResultProps {
  result:
    QuizAttemptResultResponse;

  onRetake:
    () => void;

  isRetaking:
    boolean;
}

interface TopicGroupProps {
  title:
    string;

  description:
    string;

  topics:
    QuizTopicResult[];

  strong:
    boolean;
}

function TopicGroup({
  title,
  description,
  topics,
  strong,
}: Readonly<
  TopicGroupProps
>) {
  return (
    <Paper
      withBorder
      radius="md"
      p="md"
    >
      <Stack
        gap="md"
      >
        <Group
          gap="sm"
        >
          <ThemeIcon
            variant="light"
            color={
              strong
                ? "green"
                : "orange"
            }
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
            <Text
              fw={700}
            >
              {
                title
              }
            </Text>

            <Text
              size="xs"
              c="dimmed"
            >
              {
                description
              }
            </Text>
          </div>
        </Group>

        {topics.length ===
        0 ? (
          <Text
            size="sm"
            c="dimmed"
          >
            No topics in this group.
          </Text>
        ) : (
          <Stack
            gap="sm"
          >
            {topics.map(
              (
                topic,
              ) => (
                <div
                  key={
                    topic.topic
                  }
                >
                  <Group
                    justify="space-between"
                    mb={4}
                  >
                    <Text
                      size="sm"
                      fw={600}
                    >
                      {
                        topic.topic
                      }
                    </Text>

                    <Text
                      size="xs"
                      c="dimmed"
                    >
                      {
                        topic.correct_count
                      }/{topic.question_count}
                      {" · "}
                      {
                        topic.accuracy_percentage
                      }%
                    </Text>
                  </Group>

                  <Progress
                    value={
                      topic.accuracy_percentage
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

export function QuizResult({
  result,
  onRetake,
  isRetaking,
}: Readonly<
  QuizResultProps
>) {
  return (
    <Paper
      component="section"
      withBorder
      radius="lg"
      p={{
        base:
          "md",
        sm:
          "xl",
      }}
    >
      <Stack
        gap="xl"
      >
        <Group
          justify="space-between"
          align="flex-start"
        >
          <Group
            gap="md"
          >
            <ThemeIcon
              size={50}
              radius="lg"
              variant="light"
              color="violet"
            >
              <IconTrophy
                size={27}
              />
            </ThemeIcon>

            <div>
              <Badge
                variant="light"
                color="green"
              >
                Quiz complete
              </Badge>

              <Title
                order={2}
                mt={4}
              >
                Your Results
              </Title>

              <Text
                c="dimmed"
                size="sm"
              >
                Review your score and
                the topics that may
                need more practice.
              </Text>
            </div>
          </Group>
        </Group>

        <Paper
          withBorder
          radius="md"
          p="lg"
        >
          <Stack
            gap="sm"
          >
            <Group
              justify="space-between"
              align="flex-end"
            >
              <div>
                <Text
                  size="sm"
                  c="dimmed"
                >
                  Final score
                </Text>

                <Text
                  fw={800}
                  fz={34}
                >
                  {
                    result.score_percentage
                  }%
                </Text>
              </div>

              <Text
                fw={700}
              >
                {
                  result.correct_count
                } / {
                  result.question_count
                } correct
              </Text>
            </Group>

            <Progress
              value={
                result.score_percentage
              }
              size="lg"
              radius="xl"
            />
          </Stack>
        </Paper>

        <SimpleGrid
          cols={{
            base:
              1,
            md:
              2,
          }}
          spacing="md"
        >
          <TopicGroup
            title="Strong topics"
            description="70% accuracy or higher"
            topics={
              result.strong_topics
            }
            strong
          />

          <TopicGroup
            title="Topics to review"
            description="Below 70% accuracy"
            topics={
              result.weak_topics
            }
            strong={
              false
            }
          />
        </SimpleGrid>

        <Group
          justify="flex-end"
        >
          <Button
            variant="light"
            color="violet"
            leftSection={
              <IconRefresh
                size={17}
              />
            }
            loading={
              isRetaking
            }
            onClick={
              onRetake
            }
          >
            Retake Quiz
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}