// File: /frontend/features/learning-profile/components/SubjectsForm.tsx
// Purpose: Renders Step 4 of onboarding and manages strong and
// weak subject rows with confidence values.

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

import { saveSubjectsAction } from "../actions/save-subjects";
import {
  createInitialSubjectsState,
  type SubjectConfidenceFormValue,
  type SubjectsFormValues,
} from "../actions/types";

interface SubjectsFormProps {
  initialValues: SubjectsFormValues;
}

interface EditableSubject
  extends SubjectConfidenceFormValue {
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
    createInitialSubjectsState(values);

  return initialState.values.subjects.map(
    (subject, index) => ({
      ...subject,
      id: `initial-subject-${index}`,
    }),
  );
}

export function SubjectsForm({
  initialValues,
}: Readonly<SubjectsFormProps>) {
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

  const [subjects, setSubjects] =
    useState<EditableSubject[]>(() =>
      createEditableSubjects(
        initialValues,
      ),
    );

  function updateSubject(
    subjectId: string,
    updates:
      Partial<SubjectConfidenceFormValue>,
  ): void {
    setSubjects((currentSubjects) =>
      currentSubjects.map((subject) =>
        subject.id === subjectId
          ? {
              ...subject,
              ...updates,
            }
          : subject,
      ),
    );
  }

  function addSubject(): void {
    if (subjects.length >= 30) {
      return;
    }

    setSubjects((currentSubjects) => [
      ...currentSubjects,
      {
        id: crypto.randomUUID(),
        subjectName: "",
        subjectStrength: "weak",
        confidenceLevel: "3",
      },
    ]);
  }

  function removeSubject(
    subjectId: string,
  ): void {
    setSubjects((currentSubjects) =>
      currentSubjects.filter(
        (subject) =>
          subject.id !== subjectId,
      ),
    );
  }

  const serializedSubjects =
    subjects.map(
      ({
        subjectName,
        subjectStrength,
        confidenceLevel,
      }) => ({
        subjectName,
        subjectStrength,
        confidenceLevel,
      }),
    );

  const generalErrors = [
    state.fieldErrors.subjects,
    state.fieldErrors.strongSubjects,
    state.fieldErrors.weakSubjects,
  ].filter(
    (message): message is string =>
      Boolean(message),
  );

  return (
    <form action={formAction} noValidate>
      <input
        name="subjectsJson"
        type="hidden"
        value={JSON.stringify(
          serializedSubjects,
        )}
      />

      <Stack gap="xl">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Subjects need attention"
          >
            <Stack gap={4}>
              <Text size="sm">
                {state.message}
              </Text>

              {generalErrors.map(
                (message) => (
                  <Text
                    key={message}
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
            Subjects and confidence
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Add at least one strong subject
            and one weak subject. Rate your
            confidence in each subject from
            1 to 5.
          </Text>
        </Stack>

        <Stack gap="md">
          {subjects.map(
            (subject, index) => {
              const nameError =
                state.fieldErrors[
                  `subjects.${index}.name`
                ];

              const strengthError =
                state.fieldErrors[
                  `subjects.${index}.strength`
                ];

              const confidenceError =
                state.fieldErrors[
                  `subjects.${index}.confidence`
                ];

              return (
                <Paper
                  key={subject.id}
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
                        Subject {index + 1}
                      </Text>

                      <ActionIcon
                        aria-label={`Remove subject ${index + 1}`}
                        color="red"
                        disabled={
                          isPending ||
                          subjects.length <= 2
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
                        md: 3,
                      }}
                    >
                      <TextInput
                        disabled={isPending}
                        error={nameError}
                        label="Subject name"
                        onChange={(event) =>
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
                        allowDeselect={false}
                        data={
                          SUBJECT_STRENGTH_OPTIONS
                        }
                        disabled={isPending}
                        error={strengthError}
                        label="Strength"
                        onChange={(value) =>
                          updateSubject(
                            subject.id,
                            {
                              subjectStrength:
                                value ?? "",
                            },
                          )
                        }
                        required
                        value={
                          subject.subjectStrength
                        }
                      />

                      <Select
                        allowDeselect={false}
                        data={
                          CONFIDENCE_OPTIONS
                        }
                        disabled={isPending}
                        error={confidenceError}
                        label="Confidence"
                        onChange={(value) =>
                          updateSubject(
                            subject.id,
                            {
                              confidenceLevel:
                                value ?? "",
                            },
                          )
                        }
                        required
                        value={
                          subject.confidenceLevel
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
            subjects.length >= 30
          }
          leftSection={
            <IconPlus size={18} />
          }
          onClick={addSubject}
          type="button"
          variant="light"
        >
          Add another subject
        </Button>

        <Button
          fullWidth
          leftSection={
            <IconDeviceFloppy
              size={18}
            />
          }
          loading={isPending}
          rightSection={
            <IconArrowRight size={18} />
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
          Return to study challenges
        </Anchor>
      </Stack>
    </form>
  );
}