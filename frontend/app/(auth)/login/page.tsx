// File: /frontend/app/(auth)/login/page.tsx
// Purpose: Provides a temporary login destination and confirms
// successful email verification until the login form is added.

import type {
  Metadata,
} from "next";

import {
  Alert,
  Anchor,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconCircleCheck,
  IconTool,
} from "@tabler/icons-react";

export const metadata: Metadata = {
  title:
    "Sign in | STS Capstone Project",
};

interface LoginPlaceholderPageProps {
  searchParams: Promise<{
    confirmed?: string | string[];
  }>;
}

function isConfirmationSuccessful(
  value: string | string[] | undefined,
): boolean {
  if (Array.isArray(value)) {
    return value.includes("1");
  }

  return value === "1";
}

export default async function LoginPlaceholderPage({
  searchParams,
}: Readonly<LoginPlaceholderPageProps>) {
  const parameters = await searchParams;

  const confirmed =
    isConfirmationSuccessful(
      parameters.confirmed,
    );

  return (
    <Stack gap="xl">
      <Stack gap="xs">
        <Text
          c="violet.7"
          fw={700}
          size="sm"
        >
          Welcome back
        </Text>

        <Title order={2}>
          Sign in
        </Title>

        <Text c="dimmed">
          The password-login form will be
          connected in the next
          authentication checkpoint.
        </Text>
      </Stack>

      {confirmed && (
        <Alert
          color="green"
          icon={
            <IconCircleCheck size={18} />
          }
          title="Email confirmed"
        >
          Your email was verified
          successfully. Your account is
          ready for sign-in.
        </Alert>
      )}

      <Alert
        color="violet"
        icon={<IconTool size={18} />}
        title="Login foundation in progress"
      >
        The route and authentication
        layout are ready. The complete
        password-login form will be added
        next.
      </Alert>

      <Text
        c="dimmed"
        ta="center"
      >
        Need an account?{" "}
        <Anchor
          fw={700}
          href="/register"
        >
          Create one
        </Anchor>
      </Text>
    </Stack>
  );
}