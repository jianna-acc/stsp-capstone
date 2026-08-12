// File: /frontend/app/(auth)/auth/auth-code-error/page.tsx
// Purpose: Displays a safe and friendly error when an email
// confirmation token is missing, invalid, expired, or already used.

import type {
  Metadata,
} from "next";

import {
  Alert,
  Button,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconAlertTriangle,
} from "@tabler/icons-react";

export const metadata: Metadata = {
  title:
    "Confirmation link error | Intelleap",
  description:
    "Explains that an account-confirmation link could not be verified.",
};

export default function AuthCodeErrorPage() {
  return (
    <Stack gap="xl">
      <Stack gap="xs">
        <Text
          c="red.7"
          fw={700}
          size="sm"
        >
          Confirmation unsuccessful
        </Text>

        <Title order={2}>
          This confirmation link could
          not be verified
        </Title>

        <Text c="dimmed">
          The link may be incomplete,
          expired, or already used.
        </Text>
      </Stack>

      <Alert
        color="red"
        icon={
          <IconAlertTriangle size={18} />
        }
        title="Your account was not confirmed through this link"
      >
        Return to registration when you
        need a new account, or continue to
        sign in when you already confirmed
        the email earlier.
      </Alert>

      <Stack gap="sm">
        <Button
          component="a"
          fullWidth
          href="/register"
          size="md"
        >
          Return to registration
        </Button>

        <Button
          color="gray"
          component="a"
          fullWidth
          href="/login"
          size="md"
          variant="light"
        >
          Continue to sign in
        </Button>
      </Stack>
    </Stack>
  );
}