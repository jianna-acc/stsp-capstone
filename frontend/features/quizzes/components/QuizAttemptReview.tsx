// File: /frontend/features/quizzes/components/QuizAttemptReview.tsx
// Purpose: Displays a completed Quiz attempt with submitted
// answers, correct answers, explanations, and final score.

"use client";

import {
  Alert,
  Badge,
  Divider,
  Group,
  Modal,
  Paper,
  Progress,
  ScrollArea,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconCheck,
  IconX,
} from "@tabler/icons-react";

import type {
  QuizAttemptReviewResponse,
} from "@/features/quizzes/types";


interface QuizAttemptReviewProps {
  opened:
    boolean;

  onClose:
    () => void;

  review:
    QuizAttemptReviewResponse | null;

  loading:
    boolean;

  error:
    string | null;
}


function formatQuestionType(
  value:
    QuizAttemptReviewResponse[
      "answers"
    ][number][
      "question"
    ][
      "question_type"
    ],
): string {
  switch (value) {
    case "multiple_choice":
      return "Multiple choice";

    case "true_false":
      return "True or false";

    case "identification":
      return "Identification";
  }
}


export function QuizAttemptReview({
  opened,
  onClose,
  review,
  loading,
  error,
}: Readonly<
  QuizAttemptReviewProps
>) {
  return (
    <Modal
      opened={
        opened
      }
      onClose={
        onClose
      }
      title="Quiz attempt review"
      size="xl"
      centered
    >
      {loading && (
        <Text
          c="dimmed"
        >
          Loading your completed
          Quiz attempt...
        </Text>
      )}

      {!loading &&
        error && (
        <Alert
          color="red"
          title="Review unavailable"
        >
          {
            error
          }
        </Alert>
      )}

      {!loading &&
        !error &&
        review && (
        <Stack
          gap="lg"
        >
          <Paper
            withBorder
            radius="md"
            p="md"
          >
            <Stack
              gap="xs"
            >
              <Group
                justify="space-between"
              >
                <div>
                  <Text
                    size="xs"
                    c="dimmed"
                  >
                    Final score
                  </Text>

                  <Title
                    order={2}
                  >
                    {
                      review.result
                        .score_percentage
                    }%
                  </Title>
                </div>

                <Badge
                  color="violet"
                  variant="light"
                  size="lg"
                >
                  {
                    review.result
                      .correct_count
                  } / {
                    review.result
                      .question_count
                  } correct
                </Badge>
              </Group>

              <Progress
                value={
                  review.result
                    .score_percentage
                }
                size="lg"
                radius="xl"
              />
            </Stack>
          </Paper>

          <ScrollArea.Autosize
            mah="65vh"
          >
            <Stack
              gap="md"
            >
              {review.answers.map(
                (
                  answer,
                ) => (
                  <Paper
                    key={
                      answer.answer_id
                    }
                    withBorder
                    radius="md"
                    p="md"
                  >
                    <Stack
                      gap="sm"
                    >
                      <Group
                        justify="space-between"
                        align="flex-start"
                      >
                        <div>
                          <Badge
                            variant="light"
                            color="violet"
                          >
                            Question {
                              answer
                                .question
                                .position
                            }
                          </Badge>

                          <Text
                            size="xs"
                            c="dimmed"
                            mt={5}
                          >
                            {
                              formatQuestionType(
                                answer
                                  .question
                                  .question_type,
                              )
                            }
                            {" · "}
                            {
                              answer
                                .question
                                .topic
                            }
                          </Text>
                        </div>

                        <Badge
                          color={
                            answer.is_correct
                              ? "green"
                              : "red"
                          }
                          leftSection={
                            answer.is_correct
                              ? (
                                <IconCheck
                                  size={13}
                                />
                              )
                              : (
                                <IconX
                                  size={13}
                                />
                              )
                          }
                        >
                          {
                            answer.is_correct
                              ? "Correct"
                              : "Incorrect"
                          }
                        </Badge>
                      </Group>

                      <Text
                        fw={700}
                      >
                        {
                          answer
                            .question
                            .question
                        }
                      </Text>

                      <Divider />

                      <div>
                        <Text
                          size="xs"
                          c="dimmed"
                        >
                          Your answer
                        </Text>

                        <Text>
                          {
                            answer
                              .submitted_answer
                          }
                        </Text>
                      </div>

                      {!answer.is_correct && (
                        <div>
                          <Text
                            size="xs"
                            c="dimmed"
                          >
                            Correct answer
                          </Text>

                          <Text
                            fw={600}
                            c="green"
                          >
                            {
                              answer
                                .correct_answer
                            }
                          </Text>
                        </div>
                      )}

                      <div>
                        <Text
                          size="xs"
                          c="dimmed"
                        >
                          Explanation
                        </Text>

                        <Text
                          size="sm"
                        >
                          {
                            answer
                              .explanation
                          }
                        </Text>
                      </div>
                    </Stack>
                  </Paper>
                ),
              )}
            </Stack>
          </ScrollArea.Autosize>
        </Stack>
      )}
    </Modal>
  );
}