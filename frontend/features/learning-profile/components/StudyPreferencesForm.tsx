// File: /frontend/features/learning-profile/components/StudyPreferencesForm.tsx
// Purpose: Renders Step 2 of onboarding and submits preferred
// study duration, study times, and learning methods.

"use client";

import {
  useActionState,
} from "react";

import {
  Alert,
  Anchor,
  Button,
  Checkbox,
  Input,
  Select,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconArrowRight,
  IconDeviceFloppy,
} from "@tabler/icons-react";

import {
  saveStudyPreferencesAction,
} from "../actions/save-study-preferences";
import {
  createInitialStudyPreferencesState,
  type StudyPreferencesFormValues,
} from "../actions/types";
import type {
  LearningMethod,
  PreferredStudyTime,
} from "../constants";

interface StudyPreferencesFormProps {
  initialValues: StudyPreferencesFormValues;
}

interface StudyTimeOption {
  value: PreferredStudyTime;
  label: string;
  description: string;
}

interface LearningMethodOption {
  value: LearningMethod;
  label: string;
  description: string;
}

const STUDY_DURATION_OPTIONS = [
  {
    value: "15",
    label: "15 minutes",
  },
  {
    value: "25",
    label: "25 minutes",
  },
  {
    value: "30",
    label: "30 minutes",
  },
  {
    value: "45",
    label: "45 minutes",
  },
  {
    value: "60",
    label: "1 hour",
  },
  {
    value: "90",
    label: "1 hour and 30 minutes",
  },
  {
    value: "120",
    label: "2 hours",
  },
];

const STUDY_TIME_OPTIONS:
  StudyTimeOption[] = [
    {
      value: "early_morning",
      label: "Early morning",
      description:
        "Before 7:00 AM",
    },
    {
      value: "morning",
      label: "Morning",
      description:
        "7:00 AM to 12:00 PM",
    },
    {
      value: "afternoon",
      label: "Afternoon",
      description:
        "12:00 PM to 5:00 PM",
    },
    {
      value: "evening",
      label: "Evening",
      description:
        "5:00 PM to 9:00 PM",
    },
    {
      value: "late_night",
      label: "Late night",
      description:
        "After 9:00 PM",
    },
  ];

const LEARNING_METHOD_OPTIONS:
  LearningMethodOption[] = [
    {
      value: "visual",
      label: "Visual",
      description:
        "Diagrams, charts, videos, and demonstrations",
    },
    {
      value: "auditory",
      label: "Auditory",
      description:
        "Lectures, discussions, and verbal explanations",
    },
    {
      value: "reading_writing",
      label: "Reading and writing",
      description:
        "Notes, articles, summaries, and written exercises",
    },
    {
      value: "kinesthetic",
      label: "Hands-on",
      description:
        "Practice, activities, examples, and simulations",
    },
    {
      value: "collaborative",
      label: "Collaborative",
      description:
        "Group study, peer discussion, and shared exercises",
    },
    {
      value: "mixed",
      label: "Mixed approach",
      description:
        "A combination of several learning methods",
    },
  ];

export function StudyPreferencesForm({
  initialValues,
}: Readonly<StudyPreferencesFormProps>) {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    saveStudyPreferencesAction,
    createInitialStudyPreferencesState(
      initialValues,
    ),
  );

  return (
    <form
      action={formAction}
      noValidate
    >
      <Stack gap="xl">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Study preferences need attention"
          >
            {state.message}
          </Alert>
        )}

        <Stack gap={4}>
          <Text fw={700}>
            Preferred study duration
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Choose the length of one focused
            study session that usually works
            well for you.
          </Text>
        </Stack>

        <Select
          data={STUDY_DURATION_OPTIONS}
          defaultValue={
            state.values
              .preferredStudyDurationMinutes ||
            null
          }
          disabled={isPending}
          error={
            state.fieldErrors
              .preferredStudyDurationMinutes
          }
          label="Study-session duration"
          name="preferredStudyDurationMinutes"
          placeholder="Select a duration"
          required
          size="md"
        />

        <Input.Wrapper
          description="You may select more than one time."
          error={
            state.fieldErrors
              .preferredStudyTimes
          }
          label="When do you prefer to study?"
          required
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            mt="sm"
            spacing="md"
          >
            {STUDY_TIME_OPTIONS.map(
              (option) => (
                <Checkbox
                  defaultChecked={
                    state.values
                      .preferredStudyTimes
                      .includes(option.value)
                  }
                  disabled={isPending}
                  key={option.value}
                  label={
                    <Stack gap={1}>
                      <Text
                        fw={600}
                        size="sm"
                      >
                        {option.label}
                      </Text>

                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        {option.description}
                      </Text>
                    </Stack>
                  }
                  name="preferredStudyTimes"
                  value={option.value}
                />
              ),
            )}
          </SimpleGrid>
        </Input.Wrapper>

        <Input.Wrapper
          description="Choose all approaches that help you understand lessons."
          error={
            state.fieldErrors
              .preferredLearningMethods
          }
          label="How do you prefer to learn?"
          required
        >
          <SimpleGrid
            cols={{
              base: 1,
              sm: 2,
            }}
            mt="sm"
            spacing="md"
          >
            {LEARNING_METHOD_OPTIONS.map(
              (option) => (
                <Checkbox
                  defaultChecked={
                    state.values
                      .preferredLearningMethods
                      .includes(option.value)
                  }
                  disabled={isPending}
                  key={option.value}
                  label={
                    <Stack gap={1}>
                      <Text
                        fw={600}
                        size="sm"
                      >
                        {option.label}
                      </Text>

                      <Text
                        c="dimmed"
                        size="xs"
                      >
                        {option.description}
                      </Text>
                    </Stack>
                  }
                  name="preferredLearningMethods"
                  value={option.value}
                />
              ),
            )}
          </SimpleGrid>
        </Input.Wrapper>

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
          href="/onboarding/profile"
          ta="center"
        >
          Return to student profile
        </Anchor>
      </Stack>
    </form>
  );
}