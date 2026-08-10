// File: /frontend/features/quizzes/components/QuizQuestionView.tsx
// Purpose: Displays exactly one Quiz question, collects one
// student answer, and presents immediate grading feedback.

"use client";

import {
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  Radio,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import {
  IconCheck,
  IconSend,
  IconX,
} from "@tabler/icons-react";

import type {
  QuizAnswerFeedbackResponse,
  QuizQuestionResponse,
} from "@/features/quizzes/types";

interface QuizQuestionViewProps {
  question:
    QuizQuestionResponse;

  answer:
    string;

  feedback:
    QuizAnswerFeedbackResponse | null;

  isSubmitting:
    boolean;

  onAnswerChange: (
    value: string,
  ) => void;

  onSubmit:
    () => void;
}

function formatQuestionType(
  questionType:
    QuizQuestionResponse[
      "question_type"
    ],
): string {
  switch (
    questionType
  ) {
    case "multiple_choice":
      return "Multiple choice";

    case "true_false":
      return "True or false";

    case "identification":
      return "Identification";
  }
}

export function QuizQuestionView({
  question,
  answer,
  feedback,
  isSubmitting,
  onAnswerChange,
  onSubmit,
}: Readonly<
  QuizQuestionViewProps
>) {
  const answerLocked =
    feedback !== null;

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
        <Group
          justify="space-between"
          align="flex-start"
        >
          <div>
            <Badge
              color="violet"
              variant="light"
            >
              {
                formatQuestionType(
                  question.question_type,
                )
              }
            </Badge>

            <Text
              size="sm"
              c="dimmed"
              mt="xs"
            >
              Topic: {
                question.topic
              }
            </Text>
          </div>

          <Badge
            variant="outline"
          >
            Question {
              question.position
            }
          </Badge>
        </Group>

        <Title
          order={3}
        >
          {
            question.question
          }
        </Title>

        {question.question_type ===
          "identification" ? (
          <TextInput
            label="Your answer"
            placeholder="Type your answer"
            value={
              answer
            }
            onChange={
              (
                event,
              ) =>
                onAnswerChange(
                  event.currentTarget
                    .value,
                )
            }
            disabled={
              answerLocked ||
              isSubmitting
            }
            autoComplete="off"
          />
        ) : (
          <Radio.Group
            value={
              answer
            }
            onChange={
              onAnswerChange
            }
            label="Choose your answer"
          >
            <Stack
              gap="sm"
              mt="sm"
            >
              {question.choices.map(
                (
                  choice,
                ) => (
                  <Radio
                    key={
                      choice
                    }
                    value={
                      choice
                    }
                    label={
                      choice
                    }
                    disabled={
                      answerLocked ||
                      isSubmitting
                    }
                  />
                ),
              )}
            </Stack>
          </Radio.Group>
        )}

        {feedback && (
          <Alert
            color={
              feedback.is_correct
                ? "green"
                : "red"
            }
            variant="light"
            title={
              feedback.is_correct
                ? "Correct"
                : "Not quite"
            }
            icon={
              feedback.is_correct
                ? (
                  <IconCheck
                    size={18}
                  />
                )
                : (
                  <IconX
                    size={18}
                  />
                )
            }
          >
            <Stack
              gap="xs"
            >
              {!feedback.is_correct && (
                <Text
                  size="sm"
                >
                  <strong>
                    Correct answer:
                  </strong>{" "}
                  {
                    feedback.correct_answer
                  }
                </Text>
              )}

              <Text
                size="sm"
              >
                {
                  feedback.explanation
                }
              </Text>
            </Stack>
          </Alert>
        )}

        {!feedback && (
          <Group
            justify="flex-end"
          >
            <Button
              onClick={
                onSubmit
              }
              leftSection={
                <IconSend
                  size={17}
                />
              }
              loading={
                isSubmitting
              }
              disabled={
                !answer.trim()
              }
              variant="gradient"
              gradient={{
                from:
                  "violet",
                to:
                  "grape",
              }}
            >
              Submit Answer
            </Button>
          </Group>
        )}
      </Stack>
    </Paper>
  );
}