// File: /frontend/features/learning-profile/components/StudentProfileForm.tsx
// Purpose: Renders Step 1 of onboarding and connects the student
// profile fields to the save-and-continue Server Action.

"use client";

import {
  useActionState,
} from "react";

import {
  Alert,
  Button,
  Select,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconArrowRight,
  IconDeviceFloppy,
} from "@tabler/icons-react";

import {
  saveStudentProfileAction,
} from "../actions/save-student-profile";
import {
  createInitialStudentProfileState,
  type StudentProfileFormValues,
} from "../actions/types";

interface StudentProfileFormProps {
  initialValues: StudentProfileFormValues;
}

const YEAR_LEVEL_OPTIONS = [
  {
    value: "Grade 7",
    label: "Grade 7",
  },
  {
    value: "Grade 8",
    label: "Grade 8",
  },
  {
    value: "Grade 9",
    label: "Grade 9",
  },
  {
    value: "Grade 10",
    label: "Grade 10",
  },
  {
    value: "Grade 11",
    label: "Grade 11",
  },
  {
    value: "Grade 12",
    label: "Grade 12",
  },
  {
    value: "First Year",
    label: "First Year",
  },
  {
    value: "Second Year",
    label: "Second Year",
  },
  {
    value: "Third Year",
    label: "Third Year",
  },
  {
    value: "Fourth Year",
    label: "Fourth Year",
  },
  {
    value: "Fifth Year or higher",
    label: "Fifth Year or higher",
  },
  {
    value: "Graduate Student",
    label: "Graduate Student",
  },
  {
    value: "Other",
    label: "Other",
  },
];

const TIMEZONE_OPTIONS = [
  {
    value: "Asia/Manila",
    label:
      "Philippines — Asia/Manila",
  },
  {
    value: "Asia/Singapore",
    label:
      "Singapore — Asia/Singapore",
  },
  {
    value: "Asia/Tokyo",
    label: "Japan — Asia/Tokyo",
  },
  {
    value: "Asia/Seoul",
    label:
      "South Korea — Asia/Seoul",
  },
  {
    value: "Australia/Sydney",
    label:
      "Australia — Australia/Sydney",
  },
  {
    value: "America/Los_Angeles",
    label:
      "United States — Pacific Time",
  },
  {
    value: "America/New_York",
    label:
      "United States — Eastern Time",
  },
  {
    value: "Europe/London",
    label:
      "United Kingdom — Europe/London",
  },
];

export function StudentProfileForm({
  initialValues,
}: Readonly<StudentProfileFormProps>) {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    saveStudentProfileAction,
    createInitialStudentProfileState(
      initialValues,
    ),
  );

  return (
    <form
      action={formAction}
      noValidate
    >
      <Stack gap="lg">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Profile needs attention"
          >
            {state.message}
          </Alert>
        )}

        <Stack gap={4}>
          <Text fw={700}>
            Basic academic information
          </Text>

          <Text
            c="dimmed"
            size="sm"
          >
            This information helps the
            system organize recommendations
            around your academic context.
          </Text>
        </Stack>

        <TextInput
          autoComplete="name"
          autoFocus
          defaultValue={
            state.values.fullName
          }
          disabled={isPending}
          error={
            state.fieldErrors.fullName
          }
          label="Full name"
          name="fullName"
          placeholder="Enter your full name"
          required
          size="md"
        />

        <TextInput
          autoComplete="organization"
          defaultValue={
            state.values.schoolName
          }
          disabled={isPending}
          error={
            state.fieldErrors.schoolName
          }
          label="School or institution"
          name="schoolName"
          placeholder="Example: De La Salle University"
          required
          size="md"
        />

        <TextInput
          defaultValue={
            state.values.programName
          }
          disabled={isPending}
          error={
            state.fieldErrors.programName
          }
          label="Program, course, or academic track"
          name="programName"
          placeholder="Example: BS Information Technology"
          required
          size="md"
        />

        <Select
          data={YEAR_LEVEL_OPTIONS}
          defaultValue={
            state.values.yearLevel ||
            null
          }
          disabled={isPending}
          error={
            state.fieldErrors.yearLevel
          }
          label="Current year level"
          name="yearLevel"
          placeholder="Select your year level"
          required
          searchable
          size="md"
        />

        <Select
          data={TIMEZONE_OPTIONS}
          defaultValue={
            state.values.timezone ||
            "Asia/Manila"
          }
          disabled={isPending}
          error={
            state.fieldErrors.timezone
          }
          label="Timezone"
          name="timezone"
          required
          searchable
          size="md"
        />

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
      </Stack>
    </form>
  );
}