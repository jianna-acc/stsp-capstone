// File: /frontend/app/(auth)/login/page.tsx
// Purpose: Displays the password-login interface, confirmation
// feedback, and safe post-login redirect handling.

import type { Metadata } from "next";

import {
  Alert,
  Anchor,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconCircleCheck,
} from "@tabler/icons-react";

import { LoginForm } from "@/features/auth/components/LoginForm";
import {
  DEFAULT_AFTER_LOGIN_PATH,
  getSafeInternalPath,
} from "@/features/auth/redirects";

export const metadata: Metadata = {
  title:
    "Sign in | STS Capstone Project",
  description:
    "Sign in to the STS Capstone Project student platform.",
};

interface LoginPageProps {
  searchParams: Promise<{
    confirmed?: string | string[];
    loggedOut?: string | string[];
    next?: string | string[];
  }>;
}

function getFirstParameter(
  value: string | string[] | undefined,
): string | undefined {
  return Array.isArray(value)
    ? value[0]
    : value;
}

function hasEnabledFlag(
  value: string | string[] | undefined,
): boolean {
  return Array.isArray(value)
    ? value.includes("1")
    : value === "1";
}

export default async function LoginPage({
  searchParams,
}: Readonly<LoginPageProps>) {
  const parameters = await searchParams;

  const confirmed = hasEnabledFlag(
    parameters.confirmed,
  );

  const loggedOut = hasEnabledFlag(
    parameters.loggedOut,
  );

  const nextPath = getSafeInternalPath(
    getFirstParameter(parameters.next),
    DEFAULT_AFTER_LOGIN_PATH,
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
          Enter your student account
          credentials to continue.
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
          successfully. You may now sign
          in.
        </Alert>
      )}

      {loggedOut && (
        <Alert
          color="green"
          icon={
            <IconCircleCheck size={18} />
          }
          title="Signed out"
        >
          Your session was ended
          successfully.
        </Alert>
      )}

      <LoginForm nextPath={nextPath} />

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