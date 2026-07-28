// File: /frontend/app/(auth)/register/page.tsx
// Purpose: Displays the account-registration interface.

import type { Metadata } from "next";

import {
  Anchor,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import { RegisterForm } from "@/features/auth/components/RegisterForm";

export const metadata: Metadata = {
  title:
    "Create account | STS Capstone Project",
  description:
    "Create a student account for the STS Capstone Project.",
};

export default function RegisterPage() {
  return (
    <Stack gap="xl">
      <Stack gap="xs">
        <Text
          c="violet.7"
          fw={700}
          size="sm"
        >
          Start your learning profile
        </Text>

        <Title order={2}>
          Create your account
        </Title>

        <Text c="dimmed">
          Enter your details. We will send
          an email to confirm your account
          before you continue.
        </Text>
      </Stack>

      <RegisterForm />

      <Text
        c="dimmed"
        ta="center"
      >
        Already have an account?{" "}
        <Anchor
          fw={700}
          href="/login"
        >
          Sign in
        </Anchor>
      </Text>
    </Stack>
  );
}