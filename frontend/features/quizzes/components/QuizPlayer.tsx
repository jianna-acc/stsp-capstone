// File: /frontend/features/quizzes/components/QuizPlayer.tsx
// Purpose: Runs the one-question-at-a-time Quiz experience,
// including attempts, immediate feedback, and final results.

"use client";

import {
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  Progress,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconArrowRight,
  IconPlayerPlay,
} from "@tabler/icons-react";
import {
  useState,
} from "react";

import {
  getQuizAttemptResult,
  startQuizAttempt,
  submitQuizAnswer,
} from "@/features/quizzes/attempts-api";
import {
  QuizApiError,
} from "@/features/quizzes/api";
import type {
  QuizAnswerFeedbackResponse,
  QuizAttemptResponse,
  QuizAttemptResultResponse,
  QuizResponse,
} from "@/features/quizzes/types";

import {
  QuizQuestionView,
} from "./QuizQuestionView";
import {
  QuizResult,
} from "./QuizResult";

interface QuizPlayerProps {
  quiz:
    QuizResponse;
}

const UNEXPECTED_ERROR =
  "The Quiz could not be completed. Please try again.";

export function QuizPlayer({
  quiz,
}: Readonly<
  QuizPlayerProps
>) {
  const [
    attempt,
    setAttempt,
  ] = useState<
    QuizAttemptResponse | null
  >(
    null,
  );

  const [
    displayPosition,
    setDisplayPosition,
  ] = useState(
    1,
  );

  const [
    answer,
    setAnswer,
  ] = useState(
    "",
  );

  const [
    feedback,
    setFeedback,
  ] = useState<
    QuizAnswerFeedbackResponse | null
  >(
    null,
  );

  const [
    result,
    setResult,
  ] = useState<
    QuizAttemptResultResponse | null
  >(
    null,
  );

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    isStarting,
    setIsStarting,
  ] = useState(
    false,
  );

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(
    false,
  );

  const [
    isLoadingResult,
    setIsLoadingResult,
  ] = useState(
    false,
  );

  const currentQuestion =
    quiz.questions.find(
      (
        question,
      ) =>
        question.position ===
        displayPosition,
    ) ?? null;

  async function handleStart():
  Promise<void> {
    if (isStarting) {
      return;
    }

    setIsStarting(
      true,
    );

    setError(
      null,
    );

    setResult(
      null,
    );

    setFeedback(
      null,
    );

    setAnswer(
      "",
    );

    try {
      const startedAttempt =
        await startQuizAttempt(
          quiz.id,
        );

      setAttempt(
        startedAttempt,
      );

      setDisplayPosition(
        startedAttempt
          .current_position,
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof
          QuizApiError
          ? caughtError.message
          : UNEXPECTED_ERROR,
      );
    } finally {
      setIsStarting(
        false,
      );
    }
  }

  async function handleSubmit():
  Promise<void> {
    if (
      !attempt ||
      !currentQuestion ||
      feedback ||
      isSubmitting
    ) {
      return;
    }

    const normalizedAnswer =
      answer.trim();

    if (!normalizedAnswer) {
      return;
    }

    setIsSubmitting(
      true,
    );

    setError(
      null,
    );

    try {
      const submission =
        await submitQuizAnswer(
          attempt.id,
          currentQuestion
            .position,
          normalizedAnswer,
        );

      setAttempt(
        submission.attempt,
      );

      setFeedback(
        submission.feedback,
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof
          QuizApiError
          ? caughtError.message
          : UNEXPECTED_ERROR,
      );
    } finally {
      setIsSubmitting(
        false,
      );
    }
  }

  function handleNext():
  void {
    if (
      !feedback ||
      feedback.attempt_completed ||
      feedback.next_position ===
        null
    ) {
      return;
    }

    setDisplayPosition(
      feedback.next_position,
    );

    setAnswer(
      "",
    );

    setFeedback(
      null,
    );

    setError(
      null,
    );
  }

  async function handleViewResults():
  Promise<void> {
    if (
      !attempt ||
      !feedback?.attempt_completed ||
      isLoadingResult
    ) {
      return;
    }

    setIsLoadingResult(
      true,
    );

    setError(
      null,
    );

    try {
      const attemptResult =
        await getQuizAttemptResult(
          attempt.id,
        );

      setResult(
        attemptResult,
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof
          QuizApiError
          ? caughtError.message
          : UNEXPECTED_ERROR,
      );
    } finally {
      setIsLoadingResult(
        false,
      );
    }
  }

  if (result) {
    return (
      <QuizResult
        result={
          result
        }
        onRetake={
          handleStart
        }
        isRetaking={
          isStarting
        }
      />
    );
  }

  if (!attempt) {
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
          gap="lg"
        >
          <div>
            <Badge
              color="green"
              variant="light"
            >
              Ready to start
            </Badge>

            <Title
              order={2}
              mt="xs"
            >
              {
                quiz.title
              }
            </Title>

            <Text
              c="dimmed"
              mt="xs"
            >
              Answer one question at a
              time. After submitting,
              you will immediately see
              whether your answer was
              correct and why.
            </Text>
          </div>

          <Group
            gap="xl"
          >
            <div>
              <Text
                size="xs"
                c="dimmed"
              >
                Questions
              </Text>

              <Text
                fw={700}
              >
                {
                  quiz.question_count
                }
              </Text>
            </div>

            <div>
              <Text
                size="xs"
                c="dimmed"
              >
                Difficulty
              </Text>

              <Text
                fw={700}
                tt="capitalize"
              >
                {
                  quiz.difficulty
                }
              </Text>
            </div>
          </Group>

          {error && (
            <Alert
              color="red"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
              title="Quiz could not start"
            >
              {
                error
              }
            </Alert>
          )}

          <Group
            justify="flex-end"
          >
            <Button
              onClick={
                handleStart
              }
              loading={
                isStarting
              }
              leftSection={
                <IconPlayerPlay
                  size={18}
                />
              }
              variant="gradient"
              gradient={{
                from:
                  "violet",
                to:
                  "grape",
              }}
            >
              Start Quiz
            </Button>
          </Group>
        </Stack>
      </Paper>
    );
  }

  if (!currentQuestion) {
    return (
      <Alert
        color="red"
        title="Quiz question unavailable"
        icon={
          <IconAlertCircle
            size={18}
          />
        }
      >
        The current Quiz question could
        not be loaded.
      </Alert>
    );
  }

  const progress =
    (
      displayPosition /
      attempt.question_count
    ) * 100;

  return (
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
            <Text
              size="sm"
              fw={700}
            >
              Question {
                displayPosition
              } of {
                attempt.question_count
              }
            </Text>

            <Text
              size="sm"
              c="dimmed"
            >
              {
                Math.round(
                  progress,
                )
              }%
            </Text>
          </Group>

          <Progress
            value={
              progress
            }
            radius="xl"
          />
        </Stack>
      </Paper>

      {error && (
        <Alert
          color="red"
          title="Quiz error"
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

      <QuizQuestionView
        question={
          currentQuestion
        }
        answer={
          answer
        }
        feedback={
          feedback
        }
        isSubmitting={
          isSubmitting
        }
        onAnswerChange={
          setAnswer
        }
        onSubmit={
          handleSubmit
        }
      />

      {feedback && (
        <Group
          justify="flex-end"
        >
          {feedback
            .attempt_completed ? (
            <Button
              onClick={
                handleViewResults
              }
              loading={
                isLoadingResult
              }
              rightSection={
                <IconArrowRight
                  size={17}
                />
              }
              variant="gradient"
              gradient={{
                from:
                  "violet",
                to:
                  "grape",
              }}
            >
              View Results
            </Button>
          ) : (
            <Button
              onClick={
                handleNext
              }
              rightSection={
                <IconArrowRight
                  size={17}
                />
              }
            >
              Next Question
            </Button>
          )}
        </Group>
      )}
    </Stack>
  );
}