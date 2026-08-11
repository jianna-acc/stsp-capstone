// File: /frontend/features/learning-profile/components/SubjectsForm.tsx
// Purpose: Renders the onboarding subject-strength and academic
// output-confidence questionnaire.

"use client";

import {
  useActionState,
  useState,
} from "react";

import {
  ActionIcon,
  Alert,
  Anchor,
  Button,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconArrowRight,
  IconDeviceFloppy,
  IconPlus,
  IconTrash,
} from "@tabler/icons-react";

import {
  saveSubjectsAction,
} from "../actions/save-subjects";
import {
  createInitialSubjectsState,
  type OutputConfidenceFormValue,
  type SubjectFormValue,
  type SubjectsFormValues,
} from "../actions/types";
import {
  LEARNING_OUTPUT_TYPE_LABELS,
  type LearningOutputType,
} from "../constants";

interface SubjectsFormProps {
  initialValues: SubjectsFormValues;
}

interface EditableSubject
  extends SubjectFormValue {
  id: string;
}

const SUBJECT_STRENGTH_OPTIONS = [
  {
    value: "strong",
    label: "Strong subject",
  },
  {
    value: "weak",
    label: "Weak subject",
  },
];

const CONFIDENCE_OPTIONS = [
  {
    value: "1",
    label: "1 — Very low",
  },
  {
    value: "2",
    label: "2 — Low",
  },
  {
    value: "3",
    label: "3 — Moderate",
  },
  {
    value: "4",
    label: "4 — High",
  },
  {
    value: "5",
    label: "5 — Very high",
  },
];

function createEditableSubjects(
  values: SubjectsFormValues,
): EditableSubject[] {
  const initialState =
    createInitialSubjectsState(
      values,
    );

  return initialState.values.subjects.map(
    (
      subject,
      index,
    ) => ({
      ...subject,
      id:
        `initial-subject-${index}`,
    }),
  );
}

export function SubjectsForm({
  initialValues,
}: Readonly<
  SubjectsFormProps
>) {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    saveSubjectsAction,
    createInitialSubjectsState(
      initialValues,
    ),
  );

  const [
    subjects,
    setSubjects,
  ] = useState<
    EditableSubject[]
  >(() =>
    createEditableSubjects(
      initialValues,
    ),
  );

  const [
    outputConfidences,
    setOutputConfidences,
  ] = useState<
    OutputConfidenceFormValue[]
  >(() =>
    createInitialSubjectsState(
      initialValues,
    ).values.outputConfidences,
  );

  function updateSubject(
    subjectId: string,
    updates:
      Partial<SubjectFormValue>,
  ): void {
    setSubjects(
      (currentSubjects) =>
        currentSubjects.map(
          (subject) =>
            subject.id ===
            subjectId
              ? {
                  ...subject,
                  ...updates,
                }
              : subject,
        ),
    );
  }

  function updateOutputConfidence(
    outputType:
      LearningOutputType,
    confidenceLevel: string,
  ): void {
    setOutputConfidences(
      (
        currentConfidences,
      ) =>
        currentConfidences.map(
          (confidence) =>
            confidence.outputType ===
            outputType
              ? {
                  ...confidence,
                  confidenceLevel,
                }
              : confidence,
        ),
    );
  }

  function addSubject(): void {
    if (
      subjects.length >= 30
    ) {
      return;
    }

    setSubjects(
      (
        currentSubjects,
      ) => [
        ...currentSubjects,
        {
          id:
            crypto.randomUUID(),
          subjectName: "",
          subjectStrength:
            "weak",
        },
      ],
    );
  }

  function removeSubject(
    subjectId: string,
  ): void {
    setSubjects(
      (
        currentSubjects,
      ) =>
        currentSubjects.filter(
          (subject) =>
            subject.id !==
            subjectId,
        ),
    );
  }

  const serializedSubjects =
    subjects.map(
      ({
        subjectName,
        subjectStrength,
      }) => ({
        subjectName,
        subjectStrength,
      }),
    );

  const generalErrors = [
    state.fieldErrors.subjects,
    state.fieldErrors
      .strongSubjects,
    state.fieldErrors
      .weakSubjects,
    state.fieldErrors
      .outputConfidences,
  ].filter(
    (
      message,
    ): message is string =>
      Boolean(
        message,
      ),
  );

  return (
    <form
      action={formAction}
      noValidate
    >
      <input
        name="subjectsJson"
        type="hidden"
        value={JSON.stringify(
          serializedSubjects,
        )}
      />

      <input
        name="outputConfidencesJson"
        type="hidden"
        value={JSON.stringify(
          outputConfidences,
        )}
      />

      <Stack gap="xl">
        {state.status ===
          "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle
                size={18}
              />
            }
            title="Learning profile needs attention"
          >
            <Stack gap={4}>
              <Text size="sm">
                {state.message}
              </Text>

              {generalErrors.map(
                (message) => (
                  <Text
                    key={
                      message
                    }
                    size="sm"
                  >
                    {message}
                  </Text>
                ),
              )}
            </Stack>
          </Alert>
        )}

        <Stack gap={4}>
          <Text fw={700}>
            Strong and weak
            subjects
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Add at least one
            subject you consider
            strong and one you
            currently find
            challenging.
          </Text>
        </Stack>

        <Stack gap="md">
          {subjects.map(
            (
              subject,
              index,
            ) => {
              const nameError =
                state.fieldErrors[
                  `subjects.${index}.name`
                ];

              const strengthError =
                state.fieldErrors[
                  `subjects.${index}.strength`
                ];

              return (
                <Paper
                  key={
                    subject.id
                  }
                  p="md"
                  radius="md"
                  withBorder
                >
                  <Stack gap="md">
                    <Group
                      justify="space-between"
                    >
                      <Text
                        fw={700}
                        size="sm"
                      >
                        Subject{" "}
                        {index +
                          1}
                      </Text>

                      <ActionIcon
                        aria-label={
                          `Remove subject ${index + 1}`
                        }
                        color="red"
                        disabled={
                          isPending ||
                          subjects.length <=
                            2
                        }
                        onClick={() =>
                          removeSubject(
                            subject.id,
                          )
                        }
                        type="button"
                        variant="subtle"
                      >
                        <IconTrash
                          size={18}
                        />
                      </ActionIcon>
                    </Group>

                    <SimpleGrid
                      cols={{
                        base: 1,
                        md: 2,
                      }}
                    >
                      <TextInput
                        disabled={
                          isPending
                        }
                        error={
                          nameError
                        }
                        label="Subject name"
                        onChange={(
                          event,
                        ) =>
                          updateSubject(
                            subject.id,
                            {
                              subjectName:
                                event
                                  .currentTarget
                                  .value,
                            },
                          )
                        }
                        placeholder="Example: Mathematics"
                        required
                        value={
                          subject.subjectName
                        }
                      />

                      <Select
                        allowDeselect={
                          false
                        }
                        data={
                          SUBJECT_STRENGTH_OPTIONS
                        }
                        disabled={
                          isPending
                        }
                        error={
                          strengthError
                        }
                        label="Strength"
                        onChange={(
                          value,
                        ) =>
                          updateSubject(
                            subject.id,
                            {
                              subjectStrength:
                                value ??
                                "",
                            },
                          )
                        }
                        required
                        value={
                          subject.subjectStrength
                        }
                      />
                    </SimpleGrid>
                  </Stack>
                </Paper>
              );
            },
          )}
        </Stack>

        <Button
          disabled={
            isPending ||
            subjects.length >=
              30
          }
          leftSection={
            <IconPlus
              size={18}
            />
          }
          onClick={
            addSubject
          }
          type="button"
          variant="light"
        >
          Add another subject
        </Button>

        <Stack gap={4}>
          <Text fw={700}>
            Confidence by
            academic output
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Rate how confident
            you currently feel
            completing each kind
            of academic work.
            These ratings will
            help Study AI
            prioritize tasks
            that may require
            more support.
          </Text>
        </Stack>

        <SimpleGrid
          cols={{
            base: 1,
            md: 2,
          }}
        >
          {outputConfidences.map(
            (
              confidence,
              index,
            ) => {
              const outputType =
                confidence.outputType as
                  LearningOutputType;

              const error =
                state.fieldErrors[
                  `outputConfidences.${index}.confidence`
                ];

              return (
                <Select
                  key={
                    confidence.outputType
                  }
                  allowDeselect={
                    false
                  }
                  data={
                    CONFIDENCE_OPTIONS
                  }
                  disabled={
                    isPending
                  }
                  error={
                    error
                  }
                  label={
                    LEARNING_OUTPUT_TYPE_LABELS[
                      outputType
                    ]
                  }
                  onChange={(
                    value,
                  ) =>
                    updateOutputConfidence(
                      outputType,
                      value ??
                        "",
                    )
                  }
                  required
                  value={
                    confidence.confidenceLevel
                  }
                />
              );
            },
          )}
        </SimpleGrid>

        <Button
          fullWidth
          leftSection={
            <IconDeviceFloppy
              size={18}
            />
          }
          loading={
            isPending
          }
          rightSection={
            <IconArrowRight
              size={18}
            />
          }
          size="md"
          type="submit"
        >
          Save and continue
        </Button>

        <Anchor
          href="/onboarding/study-challenges"
          ta="center"
        >
          Return to study
          challenges
        </Anchor>
      </Stack>
    </form>
  );
}