// File: /frontend/app/(protected)/dashboard/page.tsx
// Purpose: Provides a temporary authenticated dashboard for
// verifying login, logout, session persistence, and profile loading.

import type { Metadata } from "next";
import { redirect } from "next/navigation";

import {
  Alert,
  Badge,
  Button,
  Container,
  Group,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCircleCheck,
  IconLogout,
  IconUserCircle,
} from "@tabler/icons-react";

import { logoutAction } from "@/features/auth/actions/logout";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Dashboard | STS Capstone Project",
  description: "Authenticated student dashboard.",
};

interface DashboardPageProps {
  searchParams: Promise<{
    logoutError?: string | string[];
  }>;
}

function hasEnabledFlag(
  value: string | string[] | undefined,
): boolean {
  return Array.isArray(value)
    ? value.includes("1")
    : value === "1";
}

export default async function DashboardPage({
  searchParams,
}: Readonly<DashboardPageProps>) {
  const parameters = await searchParams;

  const logoutError = hasEnabledFlag(
    parameters.logoutError,
  );

  const supabase = await createClient();

  const { data: claimsData } =
    await supabase.auth.getClaims();

  const userId = claimsData?.claims?.sub;

  if (!userId) {
    redirect("/login?next=%2Fdashboard");
  }

  const {
    data: profile,
    error: profileError,
  } = await supabase
    .from("profiles")
    .select("full_name, onboarding_completed")
    .eq("id", userId)
    .maybeSingle();

  const displayName =
    profile?.full_name?.trim() || "Student";

  const onboardingCompleted =
    profile?.onboarding_completed ?? false;

  return (
    <Container
      py={{ base: 32, sm: 64 }}
      size="md"
    >
      <Stack gap="xl">
        <Group
          align="flex-start"
          justify="space-between"
        >
          <Stack gap={4}>
            <Text
              c="violet.7"
              fw={700}
              size="sm"
            >
              Protected application
            </Text>

            <Title order={1}>
              Welcome, {displayName}
            </Title>

            <Text c="dimmed">
              Your authenticated session is working.
            </Text>
          </Stack>

          <form action={logoutAction}>
            <Button
              color="gray"
              leftSection={
                <IconLogout size={18} />
              }
              type="submit"
              variant="light"
            >
              Sign out
            </Button>
          </form>
        </Group>

        {logoutError && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Sign-out was unsuccessful"
          >
            The application could not end your session.
            Try signing out again.
          </Alert>
        )}

        {profileError && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Profile could not be loaded"
          >
            Your authentication session is valid, but the
            student profile record could not be read.
          </Alert>
        )}

        <Paper
          p="xl"
          radius="lg"
          shadow="sm"
          withBorder
        >
          <Stack gap="lg">
            <Group
              align="flex-start"
              justify="space-between"
            >
              <Group
                align="flex-start"
                wrap="nowrap"
              >
                <ThemeIcon
                  color="violet"
                  radius="md"
                  size={48}
                  variant="light"
                >
                  <IconUserCircle size={26} />
                </ThemeIcon>

                <Stack gap={4}>
                  <Text fw={700}>
                    Student profile
                  </Text>

                  <Text
                    c="dimmed"
                    size="sm"
                  >
                    Account profile connected to your
                    Supabase user.
                  </Text>
                </Stack>
              </Group>

              <Badge
                color={
                  onboardingCompleted
                    ? "green"
                    : "yellow"
                }
                variant="light"
              >
                {onboardingCompleted
                  ? "Onboarding complete"
                  : "Onboarding pending"}
              </Badge>
            </Group>

            {onboardingCompleted ? (
              <Alert
                color="green"
                icon={
                  <IconCircleCheck size={18} />
                }
                title="Learning profile complete"
              >
                Your saved learning profile can be used by
                future study-planning features.
              </Alert>
            ) : (
              <Alert
                color="violet"
                icon={
                  <IconUserCircle size={18} />
                }
                title="Learning profile required"
              >
                The learning-profile questionnaire will be
                added in the next Phase 2 checkpoint.
              </Alert>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}