// File: /frontend/features/reviewers/components/ReviewerResult.tsx
// Purpose: Displays a generated reviewer with its overview,
// topics, key points, definitions, and grounded sources.

import {
  Alert,
  Badge,
  Button,
  Divider,
  Group,
  List,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconBook2,
  IconFileText,
  IconListCheck,
  IconRefresh,
  IconSparkles,
} from "@tabler/icons-react";

import type {
  ReviewerResponse,
  ReviewerSource,
} from "@/features/reviewers/types";

import classes from "./ReviewerResult.module.css";

interface ReviewerResultProps {
  reviewer: ReviewerResponse;
  onRegenerate?: () => Promise<void>;
  isRegenerating?: boolean;
  regenerationError?: string | null;
}

function formatLength(
  length:
    ReviewerResponse["reviewer_length"],
): string {
  switch (length) {
    case "short":
      return "Short";

    case "medium":
      return "Medium";

    case "long":
      return "Long";
  }
}

function formatScope(
  scopeType:
    ReviewerResponse["scope_type"],
): string {
  return scopeType === "file"
    ? "Single material"
    : "Whole subject";
}

function getSourceLocation(
  source: ReviewerSource,
): string {
  if (
    source.locator_label?.trim()
  ) {
    return source.locator_label;
  }

  return `Material section ${
    source.chunk_index + 1
  }`;
}

export function ReviewerResult({
  reviewer,
  onRegenerate,
  isRegenerating = false,
  regenerationError = null,
}: Readonly<ReviewerResultProps>) {
  return (
    <Paper
      component="article"
      withBorder
      radius="lg"
      p={{
        base: "md",
        sm: "xl",
      }}
      className={
        classes.resultCard
      }
      aria-labelledby="reviewer-result-title"
    >
      <Stack gap="xl">
        <header>
          <Group
            justify="space-between"
            align="flex-start"
            gap="md"
          >
            <Group
              align="flex-start"
              wrap="nowrap"
              gap="sm"
            >
              <ThemeIcon
                size={44}
                radius="md"
                variant="light"
                color="violet"
              >
                <IconSparkles
                  size={23}
                  stroke={1.8}
                />
              </ThemeIcon>

              <div>
                <Text
                  size="xs"
                  fw={700}
                  c="violet"
                  tt="uppercase"
                >
                  AI-generated reviewer
                </Text>

                <Title
                  order={2}
                  id="reviewer-result-title"
                  mt={3}
                >
                  {reviewer.title}
                </Title>
              </div>
            </Group>

            <Group
                gap="xs"
                justify="flex-end"
                >
                <Badge
                    variant="light"
                    color="violet"
                >
                    {formatLength(
                    reviewer.reviewer_length,
                    )}
                </Badge>

                <Badge
                    variant="light"
                    color="gray"
                >
                    {formatScope(
                    reviewer.scope_type,
                    )}
                </Badge>

                <Badge
                    variant="light"
                    color="gray"
                >
                    Generation{" "}
                    {reviewer.generation_count}
                </Badge>

                {onRegenerate && (
                    <Button
                    variant="light"
                    color="violet"
                    leftSection={
                        <IconRefresh
                        size={16}
                        />
                    }
                    loading={
                        isRegenerating
                    }
                    disabled={
                        isRegenerating
                    }
                    onClick={() => {
                        void onRegenerate();
                    }}
                    >
                    Regenerate Reviewer
                    </Button>
                )}
                </Group>
          </Group>
        </header>

        {regenerationError && (
          <Alert
            color="red"
            variant="light"
            icon={
              <IconAlertCircle
                size={18}
              />
            }
            title="Regeneration failed"
          >
            {regenerationError}
          </Alert>
        )}
        <section
          aria-labelledby="reviewer-overview-title"
        >
          <Group
            gap="xs"
            mb="sm"
          >
            <IconBook2
              size={20}
              stroke={1.8}
            />

            <Text
              id="reviewer-overview-title"
              fw={750}
              size="lg"
            >
              Overview
            </Text>
          </Group>

          <Text
            className={
              classes.overview
            }
          >
            {
              reviewer.content
                .overview
            }
          </Text>
        </section>

        <Divider />

        <section
          aria-labelledby="reviewer-topics-title"
        >
          <Group
            justify="space-between"
            align="flex-end"
            mb="md"
          >
            <div>
              <Text
                id="reviewer-topics-title"
                fw={750}
                size="lg"
              >
                Topics to review
              </Text>

              <Text
                size="sm"
                c="dimmed"
              >
                Key ideas organized from
                your selected study
                material.
              </Text>
            </div>

            <Badge
              variant="light"
              color="violet"
            >
              {
                reviewer.content
                  .topics.length
              }{" "}
              topic
              {reviewer.content
                .topics.length === 1
                ? ""
                : "s"}
            </Badge>
          </Group>

          <Stack gap="md">
            {reviewer.content.topics.map(
              (
                topic,
                topicIndex,
              ) => (
                <Paper
                  key={[
                    topic.title,
                    topicIndex,
                  ].join("-")}
                  withBorder
                  radius="md"
                  p={{
                    base: "md",
                    sm: "lg",
                  }}
                  className={
                    classes.topicCard
                  }
                >
                  <Stack gap="md">
                    <div>
                      <Text
                        size="xs"
                        fw={700}
                        c="violet"
                        tt="uppercase"
                      >
                        Topic{" "}
                        {topicIndex + 1}
                      </Text>

                      <Title
                        order={3}
                        size="h4"
                        mt={3}
                      >
                        {topic.title}
                      </Title>

                      <Text
                        mt="xs"
                        className={
                          classes.topicSummary
                        }
                      >
                        {
                          topic.summary
                        }
                      </Text>
                    </div>

                    <div>
                      <Group
                        gap="xs"
                        mb="xs"
                      >
                        <IconListCheck
                          size={18}
                          stroke={1.8}
                        />

                        <Text
                          fw={700}
                          size="sm"
                        >
                          Key points
                        </Text>
                      </Group>

                      <List
                        spacing="xs"
                        className={
                          classes.keyPoints
                        }
                      >
                        {topic.key_points.map(
                          (
                            keyPoint,
                            keyPointIndex,
                          ) => (
                            <List.Item
                              key={[
                                topicIndex,
                                keyPointIndex,
                                keyPoint,
                              ].join(
                                "-",
                              )}
                            >
                              {keyPoint}
                            </List.Item>
                          ),
                        )}
                      </List>
                    </div>

                    {topic.definitions
                      .length > 0 && (
                      <div>
                        <Text
                          fw={700}
                          size="sm"
                          mb="xs"
                        >
                          Important terms
                        </Text>

                        <SimpleGrid
                          cols={{
                            base: 1,
                            sm: 2,
                          }}
                          spacing="sm"
                        >
                          {topic.definitions.map(
                            (
                              definition,
                              definitionIndex,
                            ) => (
                              <Paper
                                key={[
                                  definition.term,
                                  definitionIndex,
                                ].join(
                                  "-",
                                )}
                                withBorder
                                radius="md"
                                p="sm"
                                className={
                                  classes.definitionCard
                                }
                              >
                                <Text
                                  fw={700}
                                  size="sm"
                                >
                                  {
                                    definition.term
                                  }
                                </Text>

                                <Text
                                  size="sm"
                                  c="dimmed"
                                  mt={3}
                                >
                                  {
                                    definition.definition
                                  }
                                </Text>
                              </Paper>
                            ),
                          )}
                        </SimpleGrid>
                      </div>
                    )}
                  </Stack>
                </Paper>
              ),
            )}
          </Stack>
        </section>

        {reviewer.sources.length >
          0 && (
          <>
            <Divider />

            <section
              aria-labelledby="reviewer-sources-title"
            >
              <Group
                justify="space-between"
                align="flex-end"
                mb="md"
              >
                <div>
                  <Text
                    id="reviewer-sources-title"
                    fw={750}
                    size="lg"
                  >
                    Sources used
                  </Text>

                  <Text
                    size="sm"
                    c="dimmed"
                  >
                    Sections of your
                    uploaded materials used
                    to create this reviewer.
                  </Text>
                </div>

                <Badge
                  variant="light"
                  color="gray"
                >
                  {
                    reviewer.sources
                      .length
                  }{" "}
                  source
                  {reviewer.sources
                    .length === 1
                    ? ""
                    : "s"}
                </Badge>
              </Group>

              <div
                className={
                  classes.sourceGrid
                }
              >
                {reviewer.sources.map(
                  (
                    source,
                    sourceIndex,
                  ) => (
                    <Paper
                      key={[
                        source.study_file_id,
                        source.chunk_index,
                        sourceIndex,
                      ].join("-")}
                      withBorder
                      radius="md"
                      p="md"
                      className={
                        classes.sourceCard
                      }
                    >
                      <Group
                        align="flex-start"
                        wrap="nowrap"
                        gap="sm"
                      >
                        <ThemeIcon
                          variant="light"
                          color="violet"
                          radius="md"
                          className={
                            classes.sourceIcon
                          }
                        >
                          <IconFileText
                            size={18}
                            stroke={1.8}
                          />
                        </ThemeIcon>

                        <div
                          className={
                            classes.sourceDetails
                          }
                        >
                          <Text
                            fw={650}
                            size="sm"
                            className={
                              classes.sourceName
                            }
                          >
                            {
                              source.source_name
                            }
                          </Text>

                          <Text
                            size="xs"
                            c="dimmed"
                            mt={3}
                          >
                            {getSourceLocation(
                              source,
                            )}
                          </Text>
                        </div>
                      </Group>
                    </Paper>
                  ),
                )}
              </div>
            </section>
          </>
        )}
      </Stack>
    </Paper>
  );
}