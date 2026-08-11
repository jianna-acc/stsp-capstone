// File: /frontend/features/quizzes/components/QuizGenerationForm.tsx
// Purpose: Lets authenticated students choose Quiz scope,
// question type, difficulty, and question count before generation.

"use client";

import {
  Alert,
  Button,
  Group,
  NumberInput,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconBrain,
  IconFileText,
  IconSparkles,
} from "@tabler/icons-react";
import {
  type FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  generateQuiz,
  QuizApiError,
} from "@/features/quizzes/api";
import type {
  QuizDifficulty,
  QuizFilterOptions,
  QuizResponse,
  QuizScopeType,
  QuizType,
} from "@/features/quizzes/types";

import classes from "./QuizGenerationForm.module.css";

interface QuizGenerationFormProps {
  filterOptions:
    QuizFilterOptions;

  onGenerated?: (
    quiz: QuizResponse,
  ) => void;
}

const SCOPE_OPTIONS = [
  {
    value:
      "subject",
    label:
      "Whole subject",
  },
  {
    value:
      "file",
    label:
      "Single study material",
  },
] satisfies Array<{
  value: QuizScopeType;
  label: string;
}>;

const QUIZ_TYPE_OPTIONS = [
  {
    value:
      "mixed",
    label:
      "Mixed",
  },
  {
    value:
      "multiple_choice",
    label:
      "Multiple choice",
  },
  {
    value:
      "true_false",
    label:
      "True or false",
  },
  {
    value:
      "identification",
    label:
      "Identification",
  },
] satisfies Array<{
  value: QuizType;
  label: string;
}>;

const DIFFICULTY_OPTIONS = [
  {
    value:
      "easy",
    label:
      "Easy",
  },
  {
    value:
      "medium",
    label:
      "Medium",
  },
  {
    value:
      "hard",
    label:
      "Hard",
  },
] satisfies Array<{
  value: QuizDifficulty;
  label: string;
}>;

const SUBJECT_REQUIRED_MESSAGE =
  "Select a subject before generating a Quiz.";

const FILE_REQUIRED_MESSAGE =
  "Select a ready study material for file-based Quiz generation.";

const QUESTION_COUNT_MESSAGE =
  "Choose between 1 and 50 questions.";

const UNEXPECTED_ERROR_MESSAGE =
  "The Quiz could not be generated. Please try again.";

type GenerationState =
  | {
      status:
        "idle";
    }
  | {
      status:
        "loading";
    }
  | {
      status:
        "error";
      message:
        string;
    }
  | {
      status:
        "success";
    };

export function QuizGenerationForm({
  filterOptions,
  onGenerated,
}: Readonly<
  QuizGenerationFormProps
>) {
  const [
    scopeType,
    setScopeType,
  ] = useState<
    QuizScopeType
  >(
    "subject",
  );

  const [
    selectedSubjectId,
    setSelectedSubjectId,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    selectedStudyFileId,
    setSelectedStudyFileId,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    quizType,
    setQuizType,
  ] = useState<
    QuizType
  >(
    "mixed",
  );

  const [
    difficulty,
    setDifficulty,
  ] = useState<
    QuizDifficulty
  >(
    "medium",
  );

  const [
    questionCount,
    setQuestionCount,
  ] = useState(
    10,
  );

  const [
    state,
    setState,
  ] = useState<
    GenerationState
  >({
    status:
      "idle",
  });

  const activeRequestRef =
    useRef<
      AbortController | null
    >(
      null,
    );

  useEffect(
    () => {
      return () => {
        activeRequestRef
          .current
          ?.abort();
      };
    },
    [],
  );

  const subjectSelectData =
    useMemo(
      () =>
        filterOptions
          .subjects
          .map(
            (
              subject,
            ) => ({
              value:
                subject.id,

              label:
                subject.name,
            }),
          ),
      [
        filterOptions
          .subjects,
      ],
    );

  const visibleStudyFiles =
    useMemo(
      () => {
        if (
          !selectedSubjectId
        ) {
          return [];
        }

        return filterOptions
          .studyFiles
          .filter(
            (
              studyFile,
            ) =>
              studyFile
                .subjectId ===
              selectedSubjectId,
          );
      },
      [
        filterOptions
          .studyFiles,
        selectedSubjectId,
      ],
    );

  const studyFileSelectData =
    useMemo(
      () =>
        visibleStudyFiles
          .map(
            (
              studyFile,
            ) => ({
              value:
                studyFile.id,

              label:
                studyFile
                  .originalFilename,
            }),
          ),
      [
        visibleStudyFiles,
      ],
    );

  const isLoading =
    state.status ===
    "loading";

  const filtersUnavailable =
    Boolean(
      filterOptions
        .loadError,
    );

  const noSubjectsAvailable =
    subjectSelectData
      .length === 0;

  const validQuestionCount =
    Number.isInteger(
      questionCount,
    ) &&
    questionCount >= 1 &&
    questionCount <= 50;

  const isGenerationDisabled =
    isLoading ||
    filtersUnavailable ||
    noSubjectsAvailable ||
    !selectedSubjectId ||
    !validQuestionCount ||
    (
      scopeType ===
        "file" &&
      !selectedStudyFileId
    );

  function resetStatus():
  void {
    setState({
      status:
        "idle",
    });
  }

  function handleScopeChange(
    value: string | null,
  ): void {
    if (
      value !==
        "subject" &&
      value !==
        "file"
    ) {
      return;
    }

    setScopeType(
      value,
    );

    if (
      value ===
      "subject"
    ) {
      setSelectedStudyFileId(
        null,
      );
    }

    resetStatus();
  }

  function handleSubjectChange(
    subjectId:
      string | null,
  ): void {
    setSelectedSubjectId(
      subjectId,
    );

    setSelectedStudyFileId(
      null,
    );

    resetStatus();
  }

  function handleStudyFileChange(
    studyFileId:
      string | null,
  ): void {
    setSelectedStudyFileId(
      studyFileId,
    );

    resetStatus();
  }

  function handleQuizTypeChange(
    value: string | null,
  ): void {
    if (
      value !==
        "multiple_choice" &&
      value !==
        "true_false" &&
      value !==
        "identification" &&
      value !==
        "mixed"
    ) {
      return;
    }

    setQuizType(
      value,
    );

    resetStatus();
  }

  function handleDifficultyChange(
    value: string | null,
  ): void {
    if (
      value !== "easy" &&
      value !== "medium" &&
      value !== "hard"
    ) {
      return;
    }

    setDifficulty(
      value,
    );

    resetStatus();
  }

  function handleQuestionCountChange(
    value:
      string | number,
  ): void {
    if (
      typeof value ===
        "number"
    ) {
      setQuestionCount(
        value,
      );

      resetStatus();
    }
  }

  async function handleSubmit(
    event:
      FormEvent,
  ): Promise<void> {
    event.preventDefault();

    if (
      !selectedSubjectId
    ) {
      setState({
        status:
          "error",

        message:
          SUBJECT_REQUIRED_MESSAGE,
      });

      return;
    }

    if (
      scopeType ===
        "file" &&
      !selectedStudyFileId
    ) {
      setState({
        status:
          "error",

        message:
          FILE_REQUIRED_MESSAGE,
      });

      return;
    }

    if (
      !validQuestionCount
    ) {
      setState({
        status:
          "error",

        message:
          QUESTION_COUNT_MESSAGE,
      });

      return;
    }

    activeRequestRef
      .current
      ?.abort();

    const requestController =
      new AbortController();

    activeRequestRef.current =
      requestController;

    setState({
      status:
        "loading",
    });

    try {
      const quiz =
        await generateQuiz(
          {
            scope_type:
              scopeType,

            subject_id:
              selectedSubjectId,

            ...(
              scopeType ===
                "file" &&
              selectedStudyFileId
                ? {
                    study_file_id:
                      selectedStudyFileId,
                  }
                : {}
            ),

            quiz_type:
              quizType,

            difficulty,

            question_count:
              questionCount,
          },
          {
            signal:
              requestController
                .signal,
          },
        );

      if (
        requestController
          .signal
          .aborted
      ) {
        return;
      }

      setState({
        status:
          "success",
      });

      onGenerated?.(
        quiz,
      );
    } catch (error) {
      if (
        requestController
          .signal
          .aborted ||
        (
          error instanceof
            DOMException &&
          error.name ===
            "AbortError"
        )
      ) {
        return;
      }

      const message =
        error instanceof
          QuizApiError
          ? error.message
          : UNEXPECTED_ERROR_MESSAGE;

      setState({
        status:
          "error",

        message,
      });
    } finally {
      if (
        activeRequestRef
          .current ===
        requestController
      ) {
        activeRequestRef
          .current =
          null;
      }
    }
  }

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
      className={
        classes.formCard
      }
    >
      <form
        onSubmit={
          handleSubmit
        }
      >
        <Stack
          gap="lg"
        >
          <Group
            gap="md"
            align="flex-start"
          >
            <ThemeIcon
              size={44}
              radius="md"
              variant="light"
              color="violet"
            >
              <IconBrain
                size={23}
              />
            </ThemeIcon>

            <div>
              <Text
                fw={750}
                size="lg"
              >
                Create a Quiz
              </Text>

              <Text
                size="sm"
                c="dimmed"
                mt={3}
              >
                Choose your source,
                question style,
                difficulty, and number
                of questions.
              </Text>
            </div>
          </Group>

          {filterOptions
            .loadError && (
            <Alert
              color="yellow"
              variant="light"
              title="Study materials unavailable"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              {
                filterOptions
                  .loadError
              }
            </Alert>
          )}

          {!filterOptions
            .loadError &&
            noSubjectsAvailable && (
            <Alert
              color="yellow"
              variant="light"
              title="No subjects available"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              Add a subject and upload
              study materials before
              generating a Quiz.
            </Alert>
          )}

          <SimpleGrid
            cols={{
              base:
                1,
              md:
                2,
            }}
            spacing="md"
          >
            <Select
              label="Quiz source"
              description="Generate from a whole subject or one file."
              data={
                SCOPE_OPTIONS
              }
              value={
                scopeType
              }
              onChange={
                handleScopeChange
              }
              allowDeselect={
                false
              }
              leftSection={
                <IconFileText
                  size={16}
                />
              }
              disabled={
                isLoading
              }
            />

            <Select
              label="Subject"
              description="Choose the subject for this Quiz."
              placeholder="Select a subject"
              data={
                subjectSelectData
              }
              value={
                selectedSubjectId
              }
              onChange={
                handleSubjectChange
              }
              searchable
              disabled={
                isLoading ||
                filtersUnavailable ||
                noSubjectsAvailable
              }
              required
            />

            {scopeType ===
              "file" && (
              <Select
                label="Study material"
                description="Only processed and ready files are available."
                placeholder={
                  selectedSubjectId
                    ? "Select a study material"
                    : "Select a subject first"
                }
                data={
                  studyFileSelectData
                }
                value={
                  selectedStudyFileId
                }
                onChange={
                  handleStudyFileChange
                }
                searchable
                disabled={
                  isLoading ||
                  !selectedSubjectId
                }
                nothingFoundMessage="No ready study materials found."
                required
              />
            )}

            <Select
              label="Question type"
              description="Choose one style or generate a mixed Quiz."
              data={
                QUIZ_TYPE_OPTIONS
              }
              value={
                quizType
              }
              onChange={
                handleQuizTypeChange
              }
              allowDeselect={
                false
              }
              disabled={
                isLoading
              }
            />

            <Select
              label="Difficulty"
              description="Control the level of recall and reasoning."
              data={
                DIFFICULTY_OPTIONS
              }
              value={
                difficulty
              }
              onChange={
                handleDifficultyChange
              }
              allowDeselect={
                false
              }
              disabled={
                isLoading
              }
            />

            <NumberInput
              label="Number of questions"
              description="Generate between 1 and 50 questions."
              min={1}
              max={50}
              step={1}
              clampBehavior="strict"
              allowDecimal={
                false
              }
              value={
                questionCount
              }
              onChange={
                handleQuestionCountChange
              }
              disabled={
                isLoading
              }
              required
            />
          </SimpleGrid>

          {state.status ===
            "error" && (
            <Alert
              color="red"
              variant="light"
              title="Quiz generation failed"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              {
                state.message
              }
            </Alert>
          )}

          {state.status ===
            "success" && (
            <Alert
              color="green"
              variant="light"
              title="Quiz ready"
            >
              Your Quiz was generated
              successfully and is ready
              to take.
            </Alert>
          )}

          <Group
            justify="flex-end"
          >
            <Button
              type="submit"
              variant="gradient"
              gradient={{
                from:
                  "violet",
                to:
                  "grape",
              }}
              leftSection={
                <IconSparkles
                  size={17}
                />
              }
              loading={
                isLoading
              }
              disabled={
                isGenerationDisabled
              }
            >
              Generate Quiz
            </Button>
          </Group>
        </Stack>
      </form>
    </Paper>
  );
}