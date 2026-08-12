// File: /frontend/features/flashcards/components/FlashcardGenerationForm.tsx
// Purpose: Provides Flashcard scope, subject/file, and card-count
// controls and submits authenticated Flashcard generation requests.

"use client";

import {
  Alert,
  Button,
  Group,
  NumberInput,
  Paper,
  Radio,
  Select,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCards,
  IconSparkles,
} from "@tabler/icons-react";
import {
  useMemo,
  useState,
} from "react";

import {
  FlashcardApiError,
  generateFlashcards,
} from "@/features/flashcards/api";
import type {
  FlashcardDeckResponse,
  FlashcardFilterOptions,
  FlashcardScopeType,
} from "@/features/flashcards/types";

import classes from "./FlashcardGenerationForm.module.css";

const DEFAULT_CARD_COUNT = 20;
const MIN_CARD_COUNT = 5;
const MAX_CARD_COUNT = 50;

const GENERIC_GENERATION_ERROR =
  "The Flashcards could not be generated. Try again.";

interface FlashcardGenerationFormProps {
  filterOptions:
    FlashcardFilterOptions;

  onGenerated: (
    deck: FlashcardDeckResponse,
  ) => void;
}

export function FlashcardGenerationForm({
  filterOptions,
  onGenerated,
}: Readonly<FlashcardGenerationFormProps>) {
  const [
    scopeType,
    setScopeType,
  ] = useState<FlashcardScopeType>(
    "subject",
  );

  const [
    selectedSubjectId,
    setSelectedSubjectId,
  ] = useState<string | null>(
    null,
  );

  const [
    selectedStudyFileId,
    setSelectedStudyFileId,
  ] = useState<string | null>(
    null,
  );

  const [
    cardCount,
    setCardCount,
  ] = useState<number>(
    DEFAULT_CARD_COUNT,
  );

  const [
    isGenerating,
    setIsGenerating,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  const subjectSelectData =
    useMemo(
      () =>
        filterOptions.subjects.map(
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
        filterOptions.subjects,
      ],
    );

  const studyFileSelectData =
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
              studyFile.subjectId ===
              selectedSubjectId,
          )
          .map(
            (
              studyFile,
            ) => ({
              value:
                studyFile.id,

              label:
                studyFile.originalFilename,
            }),
          );
      },
      [
        filterOptions.studyFiles,
        selectedSubjectId,
      ],
    );

  const noSubjectsAvailable =
    subjectSelectData.length === 0;

  const cardCountIsValid =
    Number.isInteger(
      cardCount,
    ) &&
    cardCount >= MIN_CARD_COUNT &&
    cardCount <= MAX_CARD_COUNT;

  const fileSelectionIsValid =
    scopeType === "subject" ||
    Boolean(
      selectedStudyFileId,
    );

  const generationDisabled =
    Boolean(
      filterOptions.loadError,
    ) ||
    noSubjectsAvailable ||
    !selectedSubjectId ||
    !fileSelectionIsValid ||
    !cardCountIsValid ||
    isGenerating;

  function handleScopeChange(
    value: string,
  ): void {
    const nextScope:
      FlashcardScopeType =
      value === "file"
        ? "file"
        : "subject";

    setScopeType(
      nextScope,
    );

    setErrorMessage(
      null,
    );

    if (
      nextScope === "subject"
    ) {
      setSelectedStudyFileId(
        null,
      );
    }
  }

  function handleSubjectChange(
    subjectId: string | null,
  ): void {
    setSelectedSubjectId(
      subjectId,
    );

    setSelectedStudyFileId(
      null,
    );

    setErrorMessage(
      null,
    );
  }

  function handleCardCountChange(
    value: string | number,
  ): void {
    if (
      typeof value === "number"
    ) {
      setCardCount(
        value,
      );

      return;
    }

    const parsedValue =
      Number.parseInt(
        value,
        10,
      );

    setCardCount(
      Number.isNaN(
        parsedValue,
      )
        ? 0
        : parsedValue,
    );
  }

  async function handleGenerate():
    Promise<void> {
    if (
      !selectedSubjectId ||
      !cardCountIsValid
    ) {
      return;
    }

    if (
      scopeType === "file" &&
      !selectedStudyFileId
    ) {
      return;
    }

    setIsGenerating(
      true,
    );

    setErrorMessage(
      null,
    );

    try {
      const deck =
        scopeType === "file"
          ? await generateFlashcards(
              {
                scope_type:
                  "file",

                subject_id:
                  selectedSubjectId,

                study_file_id:
                  selectedStudyFileId as string,

                card_count:
                  cardCount,
              },
            )
          : await generateFlashcards(
              {
                scope_type:
                  "subject",

                subject_id:
                  selectedSubjectId,

                card_count:
                  cardCount,
              },
            );

      onGenerated(
        deck,
      );
    } catch (error) {
      if (
        error instanceof
        FlashcardApiError
      ) {
        setErrorMessage(
          error.message,
        );
      } else {
        setErrorMessage(
          GENERIC_GENERATION_ERROR,
        );
      }
    } finally {
      setIsGenerating(
        false,
      );
    }
  }

  return (
    <Paper
      component="section"
      withBorder
      radius="lg"
      p={{
        base: "md",
        sm: "xl",
      }}
      className={
        classes.formCard
      }
      aria-labelledby="flashcard-generation-title"
    >
      <Stack gap="lg">
        <Group
          align="flex-start"
          wrap="nowrap"
          gap="sm"
        >
          <ThemeIcon
            size={42}
            radius="md"
            variant="light"
            color="violet"
          >
            <IconCards
              size={22}
              stroke={1.8}
            />
          </ThemeIcon>

          <div>
            <Title
              order={2}
              size="h3"
              id="flashcard-generation-title"
            >
              Create Flashcards
            </Title>

            <Text
              size="sm"
              c="dimmed"
              mt={3}
            >
              Choose what material to
              study and how many cards
              you want to generate.
            </Text>
          </div>
        </Group>

        {filterOptions.loadError && (
          <Alert
            icon={
              <IconAlertCircle
                size={18}
              />
            }
            color="red"
            variant="light"
            title="Flashcards unavailable"
          >
            {
              filterOptions.loadError
            }
          </Alert>
        )}

        {!filterOptions.loadError &&
          noSubjectsAvailable && (
          <Alert
            icon={
              <IconAlertCircle
                size={18}
              />
            }
            color="yellow"
            variant="light"
            title="No subjects available"
          >
            Create a subject before
            generating Flashcards.
          </Alert>
        )}

        {errorMessage && (
          <Alert
            icon={
              <IconAlertCircle
                size={18}
              />
            }
            color="red"
            variant="light"
            title="Generation failed"
          >
            {errorMessage}
          </Alert>
        )}

        <Radio.Group
          name="flashcard-scope"
          label="Generation scope"
          value={
            scopeType
          }
          onChange={
            handleScopeChange
          }
        >
          <Group
            mt="xs"
            gap="lg"
          >
            <Radio
              value="subject"
              label="Whole subject"
              disabled={
                isGenerating
              }
            />

            <Radio
              value="file"
              label="Single study material"
              disabled={
                isGenerating
              }
            />
          </Group>
        </Radio.Group>

        <div
          className={
            classes.controlGrid
          }
        >
          <Select
            label="Subject"
            aria-label="Subject"
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
            disabled={
              Boolean(
                filterOptions.loadError,
              ) ||
              noSubjectsAvailable ||
              isGenerating
            }
            searchable
            nothingFoundMessage="No subjects found"
            required
          />

          {scopeType === "file" && (
            <Select
            label="Study material"
            aria-label="Study material"
              placeholder={
                selectedSubjectId
                  ? "Select a ready study material"
                  : "Select a subject first"
              }
              data={
                studyFileSelectData
              }
              value={
                selectedStudyFileId
              }
              onChange={(
                studyFileId,
              ) => {
                setSelectedStudyFileId(
                  studyFileId,
                );

                setErrorMessage(
                  null,
                );
              }}
              disabled={
                Boolean(
                  filterOptions.loadError,
                ) ||
                !selectedSubjectId ||
                isGenerating
              }
              searchable
              nothingFoundMessage="No ready study materials found"
              required
            />
          )}

          <div>
          <NumberInput
            label="Number of cards"
            aria-label="Number of cards"
            value={
              cardCount
            }
            onChange={
              handleCardCountChange
            }
            min={
              MIN_CARD_COUNT
            }
            max={
              MAX_CARD_COUNT
            }
            step={5}
            allowDecimal={
              false
            }
            allowNegative={
              false
            }
            disabled={
              Boolean(
                filterOptions.loadError,
              ) ||
              isGenerating
            }
            required
          />

          <Text
            size="xs"
            c="dimmed"
            mt={4}
          >
            Choose between 5 and 50 cards.
          </Text>
        </div>
        </div>

        {scopeType === "file" &&
          selectedSubjectId &&
          studyFileSelectData.length ===
            0 && (
          <Text
            size="sm"
            c="dimmed"
          >
            This subject has no ready
            study materials yet.
          </Text>
        )}

        <Group
          justify="flex-end"
        >
          <Button
            type="button"
            leftSection={
              <IconSparkles
                size={18}
              />
            }
            loading={
              isGenerating
            }
            disabled={
              generationDisabled
            }
            onClick={
              handleGenerate
            }
          >
            Generate Flashcards
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}