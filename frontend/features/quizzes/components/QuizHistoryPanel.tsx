// File: /frontend/features/quizzes/components/QuizHistoryPanel.tsx
// Purpose: Displays saved Quizzes and lets students review,
// retake, refresh, or delete their saved Quiz history.

"use client";

import {
  Alert,
  Badge,
  Button,
  Group,
  Modal,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconHistory,
  IconPlayerPlay,
  IconRefresh,
  IconTrash,
} from "@tabler/icons-react";
import {
  useState,
} from "react";

import {
  deleteSavedQuiz,
  getQuizAttemptReview,
  listQuizAttempts,
} from "@/features/quizzes/history-api";
import {
  QuizApiError,
} from "@/features/quizzes/api";
import type {
  QuizAttemptReviewResponse,
  QuizSummaryResponse,
} from "@/features/quizzes/types";

import {
  QuizAttemptReview,
} from "./QuizAttemptReview";


interface QuizHistoryPanelProps {
  quizzes:
    QuizSummaryResponse[];

  loading:
    boolean;

  error:
    string | null;

  onRefresh:
    () => Promise<void>;

  onTakeQuiz:
    (
      quizId: string,
    ) => Promise<void>;
}


function formatQuizType(
  value:
    QuizSummaryResponse[
      "quiz_type"
    ],
): string {
  switch (value) {
    case "multiple_choice":
      return "Multiple choice";

    case "true_false":
      return "True or false";

    case "identification":
      return "Identification";

    case "mixed":
      return "Mixed";
  }
}


function formatDate(
  value: string,
): string {
  const date =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle:
        "medium",

      timeStyle:
        "short",
    },
  ).format(
    date,
  );
}


export function QuizHistoryPanel({
  quizzes,
  loading,
  error,
  onRefresh,
  onTakeQuiz,
}: Readonly<
  QuizHistoryPanelProps
>) {
  const [
    deletingQuiz,
    setDeletingQuiz,
  ] = useState<
    QuizSummaryResponse | null
  >(
    null,
  );

  const [
    deleting,
    setDeleting,
  ] = useState(
    false,
  );

  const [
    actionError,
    setActionError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    reviewOpened,
    setReviewOpened,
  ] = useState(
    false,
  );

  const [
    review,
    setReview,
  ] = useState<
    QuizAttemptReviewResponse | null
  >(
    null,
  );

  const [
    reviewLoading,
    setReviewLoading,
  ] = useState(
    false,
  );

  const [
    reviewError,
    setReviewError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    takingQuizId,
    setTakingQuizId,
  ] = useState<
    string | null
  >(
    null,
  );


  async function handleReview(
    quiz:
      QuizSummaryResponse,
  ): Promise<void> {
    setReviewOpened(
      true,
    );

    setReview(
      null,
    );

    setReviewError(
      null,
    );

    setReviewLoading(
      true,
    );

    try {
      const attempts =
        await listQuizAttempts(
          quiz.id,
        );

      const completedAttempt =
        attempts.items.find(
          (
            attempt,
          ) =>
            attempt.status ===
            "completed",
        );

      if (!completedAttempt) {
        setReviewError(
          "This Quiz does not have a completed attempt to review yet.",
        );

        return;
      }

      const loadedReview =
        await getQuizAttemptReview(
          completedAttempt.id,
        );

      setReview(
        loadedReview,
      );
    } catch (caughtError) {
      setReviewError(
        caughtError instanceof
          QuizApiError
          ? caughtError.message
          : "The Quiz attempt could not be reviewed.",
      );
    } finally {
      setReviewLoading(
        false,
      );
    }
  }


  async function handleTakeQuiz(
    quizId: string,
  ): Promise<void> {
    if (
      takingQuizId
    ) {
      return;
    }

    setTakingQuizId(
      quizId,
    );

    setActionError(
      null,
    );

    try {
      await onTakeQuiz(
        quizId,
      );
    } catch (caughtError) {
      setActionError(
        caughtError instanceof
          Error
          ? caughtError.message
          : "The saved Quiz could not be opened.",
      );
    } finally {
      setTakingQuizId(
        null,
      );
    }
  }


  async function handleDelete():
  Promise<void> {
    if (
      !deletingQuiz ||
      deleting
    ) {
      return;
    }

    setDeleting(
      true,
    );

    setActionError(
      null,
    );

    try {
      await deleteSavedQuiz(
        deletingQuiz.id,
      );

      setDeletingQuiz(
        null,
      );

      await onRefresh();
    } catch (caughtError) {
      setActionError(
        caughtError instanceof
          QuizApiError
          ? caughtError.message
          : "The Quiz could not be deleted.",
      );
    } finally {
      setDeleting(
        false,
      );
    }
  }


  return (
    <>
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
          gap="lg"
        >
          <Group
            justify="space-between"
            align="flex-start"
          >
            <Group
              gap="md"
            >
              <ThemeIcon
                size={44}
                radius="md"
                variant="light"
                color="violet"
              >
                <IconHistory
                  size={23}
                />
              </ThemeIcon>

              <div>
                <Title
                  order={2}
                >
                  My Quizzes
                </Title>

                <Text
                  size="sm"
                  c="dimmed"
                  mt={3}
                >
                  Review previous
                  attempts, retake
                  saved Quizzes, or
                  remove ones you no
                  longer need.
                </Text>
              </div>
            </Group>

            <Button
              variant="subtle"
              color="violet"
              leftSection={
                <IconRefresh
                  size={16}
                />
              }
              onClick={
                onRefresh
              }
              loading={
                loading
              }
            >
              Refresh
            </Button>
          </Group>

          {error && (
            <Alert
              color="red"
              title="Saved Quizzes unavailable"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              {
                error
              }
            </Alert>
          )}

          {actionError && (
            <Alert
              color="red"
              title="Quiz action failed"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              {
                actionError
              }
            </Alert>
          )}

          {!loading &&
            !error &&
            quizzes.length === 0 && (
            <Alert
              color="violet"
              variant="light"
              title="No saved Quizzes yet"
            >
              Generate a Quiz first.
              It will appear here
              automatically.
            </Alert>
          )}

          {quizzes.length > 0 && (
            <SimpleGrid
              cols={{
                base:
                  1,
                lg:
                  2,
              }}
              spacing="md"
            >
              {quizzes.map(
                (
                  quiz,
                ) => {
                  const latest =
                    quiz.latest_attempt;

                  const latestCompleted =
                    latest?.status ===
                    "completed";

                  return (
                    <Paper
                      key={
                        quiz.id
                      }
                      withBorder
                      radius="md"
                      p="lg"
                    >
                      <Stack
                        gap="md"
                      >
                        <div>
                          <Group
                            justify="space-between"
                            align="flex-start"
                          >
                            <div>
                              <Title
                                order={3}
                              >
                                {
                                  quiz.title
                                }
                              </Title>

                              <Group
                                gap="xs"
                                mt="xs"
                              >
                                <Badge
                                  variant="light"
                                  color="violet"
                                >
                                  {
                                    formatQuizType(
                                      quiz.quiz_type,
                                    )
                                  }
                                </Badge>

                                <Badge
                                  variant="light"
                                >
                                  {
                                    quiz.difficulty
                                  }
                                </Badge>

                                <Badge
                                  variant="outline"
                                >
                                  {
                                    quiz.question_count
                                  } questions
                                </Badge>
                              </Group>
                            </div>
                          </Group>

                          <Text
                            size="xs"
                            c="dimmed"
                            mt="sm"
                          >
                            Created {
                              formatDate(
                                quiz.created_at,
                              )
                            }
                          </Text>
                        </div>

                        <Paper
                          withBorder
                          radius="sm"
                          p="sm"
                        >
                          <SimpleGrid
                            cols={2}
                          >
                            <div>
                              <Text
                                size="xs"
                                c="dimmed"
                              >
                                Attempts
                              </Text>

                              <Text
                                fw={700}
                              >
                                {
                                  quiz.attempt_count
                                }
                              </Text>
                            </div>

                            <div>
                              <Text
                                size="xs"
                                c="dimmed"
                              >
                                Latest
                              </Text>

                              {!latest ? (
                                <Text
                                  fw={700}
                                >
                                  Not taken
                                </Text>
                              ) : latestCompleted ? (
                                <Text
                                  fw={700}
                                >
                                  {
                                    latest.score_percentage
                                  }%
                                </Text>
                              ) : (
                                <Text
                                  fw={700}
                                  c="orange"
                                >
                                  Incomplete
                                </Text>
                              )}
                            </div>
                          </SimpleGrid>
                        </Paper>

                        <Group
                          gap="xs"
                        >
                          <Button
                            size="xs"
                            variant="light"
                            color="violet"
                            leftSection={
                              <IconPlayerPlay
                                size={15}
                              />
                            }
                            loading={
                              takingQuizId ===
                              quiz.id
                            }
                            onClick={
                              () =>
                                handleTakeQuiz(
                                  quiz.id,
                                )
                            }
                          >
                            {
                              quiz.attempt_count >
                              0
                                ? "Retake"
                                : "Take Quiz"
                            }
                          </Button>

                          <Button
                            size="xs"
                            variant="default"
                            leftSection={
                              <IconHistory
                                size={15}
                              />
                            }
                            disabled={
                              quiz.attempt_count ===
                              0
                            }
                            onClick={
                              () =>
                                handleReview(
                                  quiz,
                                )
                            }
                          >
                            Review latest
                          </Button>

                          <Button
                            size="xs"
                            variant="subtle"
                            color="red"
                            leftSection={
                              <IconTrash
                                size={15}
                              />
                            }
                            onClick={
                              () =>
                                setDeletingQuiz(
                                  quiz,
                                )
                            }
                          >
                            Delete
                          </Button>
                        </Group>
                      </Stack>
                    </Paper>
                  );
                },
              )}
            </SimpleGrid>
          )}
        </Stack>
      </Paper>

      <Modal
        opened={
          deletingQuiz !==
          null
        }
        onClose={
          () => {
            if (!deleting) {
              setDeletingQuiz(
                null,
              );
            }
          }
        }
        title="Delete Quiz?"
        centered
      >
        <Stack
          gap="lg"
        >
          <Text
            size="sm"
          >
            Delete{" "}
            <strong>
              {
                deletingQuiz
                  ?.title
              }
            </strong>
            ? Its questions and
            attempt history will also
            be removed. This cannot be
            undone.
          </Text>

          <Group
            justify="flex-end"
          >
            <Button
              variant="default"
              disabled={
                deleting
              }
              onClick={
                () =>
                  setDeletingQuiz(
                    null,
                  )
              }
            >
              Cancel
            </Button>

            <Button
              color="red"
              loading={
                deleting
              }
              onClick={
                handleDelete
              }
            >
              Delete Quiz
            </Button>
          </Group>
        </Stack>
      </Modal>

      <QuizAttemptReview
        opened={
          reviewOpened
        }
        onClose={
          () => {
            setReviewOpened(
              false,
            );

            setReview(
              null,
            );

            setReviewError(
              null,
            );
          }
        }
        review={
          review
        }
        loading={
          reviewLoading
        }
        error={
          reviewError
        }
      />
    </>
  );
}