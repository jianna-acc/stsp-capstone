// File: /frontend/features/learning-profile/components/CompleteOnboardingForm.tsx
// Purpose: Displays the final onboarding-completion button with
// pending and error states from the completion Server Action.

"use client";

import {
  useActionState,
} from "react";

import {
  Alert,
  Button,
  Stack,
  Text,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCircleCheck,
} from "@tabler/icons-react";

import {
  completeOnboardingAction,
} from "../actions/complete-onboarding";
import {
  initialCompleteOnboardingActionState,
} from "../actions/types";

export function CompleteOnboardingForm() {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    completeOnboardingAction,
    initialCompleteOnboardingActionState,
  );

  return (
    <form action={formAction}>
      <Stack gap="md">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Onboarding could not be completed"
          >
            {state.message}
          </Alert>
        )}

        <Text
          c="dimmed"
          size="sm"
        >
          Selecting the button below will
          verify that every required
          learning-profile section has been
          completed.
        </Text>

        <Button
          fullWidth
          leftSection={
            <IconCircleCheck size={19} />
          }
          loading={isPending}
          size="lg"
          type="submit"
        >
          Complete onboarding
        </Button>
      </Stack>
    </form>
  );
}