// File: /frontend/features/learning-profile/components/StudyChallengesForm.tsx
// Purpose: Renders Step 3 of onboarding and submits common study
// challenges and estimated academic task-completion time.

"use client";

import { useActionState } from "react";

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

import { saveStudyChallengesAction } from "../actions/save-study-challenges";
import {
  createInitialStudyChallengesState,
  type StudyChallengesFormValues,
} from "../actions/types";
import type { StudyChallenge } from "../constants";

interface StudyChallengesFormProps {
  initialValues: StudyChallengesFormValues;
}

interface StudyChallengeOption {
  value: StudyChallenge;
  label: string;
  description: string;
}

const TASK_COMPLETION_OPTIONS = [
  {
    value: "15",
    label: "Around 15 minutes",
  },
  {
    value: "30",
    label: "Around 30 minutes",
  },
  {
    value: "45",
    label: "Around 45 minutes",
  },
  {
    value: "60",
    label: "Around 1 hour",
  },
  {
    value: "90",
    label: "Around 1 hour and 30 minutes",
  },
  {
    value: "120",
    label: "Around 2 hours",
  },
  {
    value: "180",
    label: "Around 3 hours",
  },
  {
    value: "240",
    label: "Around 4 hours",
  },
];

const STUDY_CHALLENGE_OPTIONS:
  StudyChallengeOption[] = [
    {
      value: "procrastination",
      label: "Procrastination",
      description:
        "I delay beginning important academic work.",
    },
    {
      value: "distractions",
      label: "Distractions",
      description:
        "Notifications, social media, or my surroundings interrupt me.",
    },
    {
      value: "time_management",
      label: "Time management",
      description:
        "I find it difficult to divide my time across different tasks.",
    },
    {
      value: "motivation",
      label: "Lack of motivation",
      description:
        "I sometimes struggle to begin or continue studying.",
    },
    {
      value: "difficult_content",
      label: "Difficult lessons",
      description:
        "Some topics are difficult for me to understand independently.",
    },
    {
      value: "heavy_workload",
      label: "Heavy workload",
      description:
        "I often have several assignments or deadlines at the same time.",
    },
    {
      value: "forgetfulness",
      label: "Forgetfulness",
      description:
        "I sometimes forget lessons, deadlines, or planned study sessions.",
    },
    {
      value: "test_anxiety",
      label: "Test anxiety",
      description:
        "Examinations or assessments affect my confidence and focus.",
    },
    {
      value: "other",
      label: "Other challenges",
      description:
        "I experience challenges that are not included above.",
    },
  ];

export function StudyChallengesForm({
  initialValues,
}: Readonly<StudyChallengesFormProps>) {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    saveStudyChallengesAction,
    createInitialStudyChallengesState(
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
            title="Study challenges need attention"
          >
            {state.message}
          </Alert>
        )}

        <Stack gap={4}>
          <Text fw={700}>
            Common study challenges
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Select the difficulties that
            commonly affect your study
            sessions or academic tasks.
          </Text>
        </Stack>

        <Input.Wrapper
          description="You may select more than one challenge."
          error={
            state.fieldErrors
              .commonStudyChallenges
          }
          label="Which challenges do you commonly experience?"
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
            {STUDY_CHALLENGE_OPTIONS.map(
              (option) => (
                <Checkbox
                  defaultChecked={
                    state.values
                      .commonStudyChallenges
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
                  name="commonStudyChallenges"
                  value={option.value}
                />
              ),
            )}
          </SimpleGrid>
        </Input.Wrapper>

        <Stack gap={4}>
          <Text fw={700}>
            Estimated task-completion time
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            Estimate how long a typical
            assignment, activity, or study
            task usually takes you.
          </Text>
        </Stack>

        <Select
          data={TASK_COMPLETION_OPTIONS}
          defaultValue={
            state.values
              .estimatedTaskCompletionMinutes ||
            null
          }
          disabled={isPending}
          error={
            state.fieldErrors
              .estimatedTaskCompletionMinutes
          }
          label="Typical task duration"
          name="estimatedTaskCompletionMinutes"
          placeholder="Select an estimated duration"
          required
          size="md"
        />

        <Button
          fullWidth
          leftSection={
            <IconDeviceFloppy size={18} />
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
          href="/onboarding/study-preferences"
          ta="center"
        >
          Return to study preferences
        </Anchor>
      </Stack>
    </form>
  );
}