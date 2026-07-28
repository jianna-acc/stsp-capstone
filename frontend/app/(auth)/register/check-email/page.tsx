// File: /frontend/app/(auth)/register/check-email/page.tsx
// Purpose: Tells newly registered students to confirm their
// email address before attempting to sign in.

import type { Metadata } from "next";

import {
  Button,
  Center,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { IconMailCheck } from "@tabler/icons-react";

export const metadata: Metadata = {
  title:
    "Check your email | STS Capstone Project",
};

export default function CheckEmailPage() {
  return (
    <Stack gap="xl">
      <Center>
        <ThemeIcon
          color="violet"
          radius="xl"
          size={72}
          variant="light"
        >
          <IconMailCheck size={36} />
        </ThemeIcon>
      </Center>

      <Stack gap="sm">
        <Title
          order={2}
          ta="center"
        >
          Check your email
        </Title>

        <Text
          c="dimmed"
          ta="center"
        >
          We sent a confirmation link to
          the email address used during
          registration.
        </Text>

        <Text
          c="dimmed"
          size="sm"
          ta="center"
        >
          Open the message and select the
          confirmation link. Check your
          spam or junk folder when the
          email does not appear immediately.
        </Text>
      </Stack>

      <Button
        component="a"
        fullWidth
        href="/login"
        size="md"
      >
        Continue to sign in
      </Button>

      <Button
        color="gray"
        component="a"
        fullWidth
        href="/register"
        size="md"
        variant="subtle"
      >
        Use a different email
      </Button>
    </Stack>
  );
}