// File: /frontend/features/reviewers/components/ReviewerGenerationForm.tsx
// Purpose: Lets authenticated students choose reviewer scope,
// study material, and detail length before generating a reviewer.

"use client";

import {
  Alert,
  Button,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconBook2,
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
  generateReviewer,
  ReviewerApiError,
} from "@/features/reviewers/api";
import type {
  ReviewerFilterOptions,
  ReviewerLength,
  ReviewerResponse,
  ReviewerScopeType,
} from "@/features/reviewers/types";

import classes from "./ReviewerGenerationForm.module.css";

interface ReviewerGenerationFormProps {
  filterOptions: ReviewerFilterOptions;

  onGenerated?: (
    reviewer: ReviewerResponse,
  ) => void;
}

const SCOPE_OPTIONS = [
  {
    value: "subject",
    label: "Whole subject",
  },
  {
    value: "file",
    label: "Single study material",
  },
] satisfies Array<{
  value: ReviewerScopeType;
  label: string;
}>;

const LENGTH_OPTIONS = [
  {
    value: "short",
    label: "Short",
  },
  {
    value: "medium",
    label: "Medium",
  },
  {
    value: "long",
    label: "Long",
  },
] satisfies Array<{
  value: ReviewerLength;
  label: string;
}>;

const SUBJECT_REQUIRED_MESSAGE =
  "Select a subject before generating a reviewer.";

const FILE_REQUIRED_MESSAGE =
  "Select a ready study material for file-based reviewer generation.";

const UNEXPECTED_ERROR_MESSAGE =
  "The reviewer could not be generated. Please try again.";

type GenerationState =
  | {
      status: "idle";
    }
  | {
      status: "loading";
    }
  | {
      status: "error";
      message: string;
    }
  | {
      status: "success";
    };

export function ReviewerGenerationForm({
  filterOptions,
  onGenerated,
}: Readonly<ReviewerGenerationFormProps>) {
  const [
    scopeType,
    setScopeType,
  ] = useState<ReviewerScopeType>(
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
    reviewerLength,
    setReviewerLength,
  ] = useState<ReviewerLength>(
    "medium",
  );

  const [
    state,
    setState,
  ] = useState<GenerationState>({
    status: "idle",
  });

  const activeRequestRef =
    useRef<AbortController | null>(
      null,
    );

  useEffect(() => {
    return () => {
      activeRequestRef.current?.abort();
    };
  }, []);

  const subjectSelectData =
    useMemo(
      () =>
        filterOptions.subjects.map(
          (subject) => ({
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

  const visibleStudyFiles =
    useMemo(
      () => {
        if (!selectedSubjectId) {
          return [];
        }

        return filterOptions.studyFiles.filter(
          (studyFile) =>
            studyFile.subjectId ===
            selectedSubjectId,
        );
      },
      [
        filterOptions.studyFiles,
        selectedSubjectId,
      ],
    );

  const studyFileSelectData =
    useMemo(
      () =>
        visibleStudyFiles.map(
          (studyFile) => ({
            value:
              studyFile.id,

            label:
              studyFile.originalFilename,
          }),
        ),
      [
        visibleStudyFiles,
      ],
    );

  const isLoading =
    state.status === "loading";

  const filtersUnavailable =
    Boolean(
      filterOptions.loadError,
    );

  const noSubjectsAvailable =
    subjectSelectData.length === 0;

  const isGenerationDisabled =
    isLoading ||
    filtersUnavailable ||
    noSubjectsAvailable ||
    !selectedSubjectId ||
    (
      scopeType === "file" &&
      !selectedStudyFileId
    );

  function handleScopeChange(
    value: string | null,
  ): void {
    if (
      value !== "subject" &&
      value !== "file"
    ) {
      return;
    }

    setScopeType(value);

    if (value === "subject") {
      setSelectedStudyFileId(
        null,
      );
    }

    setState({
      status: "idle",
    });
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

    setState({
      status: "idle",
    });
  }

  function handleStudyFileChange(
    studyFileId: string | null,
  ): void {
    setSelectedStudyFileId(
      studyFileId,
    );

    setState({
      status: "idle",
    });
  }

  function handleLengthChange(
    value: string | null,
  ): void {
    if (
      value !== "short" &&
      value !== "medium" &&
      value !== "long"
    ) {
      return;
    }

    setReviewerLength(
      value,
    );

    setState({
      status: "idle",
    });
  }

  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (!selectedSubjectId) {
      setState({
        status: "error",
        message:
          SUBJECT_REQUIRED_MESSAGE,
      });

      return;
    }

    if (
      scopeType === "file" &&
      !selectedStudyFileId
    ) {
      setState({
        status: "error",
        message:
          FILE_REQUIRED_MESSAGE,
      });

      return;
    }

    activeRequestRef.current?.abort();

    const requestController =
      new AbortController();

    activeRequestRef.current =
      requestController;

    setState({
      status: "loading",
    });

    try {
      const reviewer =
        await generateReviewer(
          {
            scope_type:
              scopeType,

            subject_id:
              selectedSubjectId,

            ...(scopeType ===
              "file" &&
            selectedStudyFileId
              ? {
                  study_file_id:
                    selectedStudyFileId,
                }
              : {}),

            reviewer_length:
              reviewerLength,
          },
          {
            signal:
              requestController.signal,
          },
        );

      if (
        requestController.signal
          .aborted
      ) {
        return;
      }

      setState({
        status: "success",
      });

      onGenerated?.(
        reviewer,
      );
    } catch (error) {
      if (
        requestController.signal
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
        ReviewerApiError
          ? error.message
          : UNEXPECTED_ERROR_MESSAGE;

      setState({
        status: "error",
        message,
      });
    } finally {
      if (
        activeRequestRef.current ===
        requestController
      ) {
        activeRequestRef.current =
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
        base: "md",
        sm: "xl",
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
        <Stack gap="lg">
          <div>
            <Group
              gap="sm"
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                variant="light"
                color="violet"
                radius="md"
                size={40}
              >
                <IconBook2
                  size={21}
                  stroke={1.8}
                />
              </ThemeIcon>

              <div>
                <Text
                  fw={750}
                  size="lg"
                >
                  Create a reviewer
                </Text>

                <Text
                  size="sm"
                  c="dimmed"
                  mt={3}
                >
                  Choose what material
                  should be summarized and
                  how detailed the reviewer
                  should be.
                </Text>
              </div>
            </Group>
          </div>

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
              generating a reviewer.
            </Alert>
          )}

          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            spacing="md"
          >
            <Select
              label="Generation scope"
              description="Generate from a whole subject or one specific file."
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
              disabled={
                isLoading ||
                filtersUnavailable
              }
            />

            <Select
              label="Reviewer length"
              description="Choose how much detail the AI should include."
              data={
                LENGTH_OPTIONS
              }
              value={
                reviewerLength
              }
              onChange={
                handleLengthChange
              }
              allowDeselect={
                false
              }
              disabled={
                isLoading ||
                filtersUnavailable
              }
            />
          </SimpleGrid>

          <Select
            label="Subject"
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
            clearable
            required
            disabled={
              isLoading ||
              filtersUnavailable ||
              noSubjectsAvailable
            }
            nothingFoundMessage="No subjects found"
          />

          {scopeType === "file" && (
            <div>
              <Select
                label="Study material"
                placeholder={
                  selectedSubjectId
                    ? "Select a ready study material"
                    : "Select a subject first"
                }
                description="Only processed and indexed materials can be used."
                leftSection={
                  <IconFileText
                    size={17}
                  />
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
                clearable
                required
                disabled={
                  isLoading ||
                  filtersUnavailable ||
                  !selectedSubjectId ||
                  studyFileSelectData
                    .length === 0
                }
                nothingFoundMessage="No ready study materials found"
              />

              {selectedSubjectId &&
                studyFileSelectData
                  .length === 0 && (
                  <Text
                    size="xs"
                    c="orange"
                    mt="xs"
                  >
                    This subject does not
                    have any ready study
                    materials yet.
                  </Text>
                )}
            </div>
          )}

          {state.status ===
            "loading" && (
            <Paper
              withBorder
              radius="md"
              p="md"
              className={
                classes.statusCard
              }
              aria-live="polite"
            >
              <Group
                align="flex-start"
                wrap="nowrap"
              >
                <ThemeIcon
                  variant="light"
                  color="violet"
                  radius="md"
                >
                  <IconSparkles
                    size={19}
                  />
                </ThemeIcon>

                <div>
                  <Text fw={700}>
                    Generating reviewer
                  </Text>

                  <Text
                    size="sm"
                    c="dimmed"
                    mt={3}
                  >
                    Intelleap is reading the
                    selected material and
                    organizing the important
                    concepts.
                  </Text>
                </div>
              </Group>
            </Paper>
          )}

          {state.status ===
            "error" && (
            <Alert
              color="red"
              variant="light"
              title="Reviewer could not be generated"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
              aria-live="assertive"
            >
              {state.message}
            </Alert>
          )}

          {state.status ===
            "success" && (
            <Alert
              color="green"
              variant="light"
              title="Reviewer generated"
              icon={
                <IconSparkles
                  size={18}
                />
              }
              aria-live="polite"
            >
              Your reviewer was generated
              and saved successfully.
            </Alert>
          )}

          <Group justify="flex-end">
            <Button
              type="submit"
              loading={
                isLoading
              }
              disabled={
                isGenerationDisabled
              }
              leftSection={
                <IconSparkles
                  size={18}
                />
              }
            >
              Generate reviewer
            </Button>
          </Group>
        </Stack>
      </form>
    </Paper>
  );
}