// File: /frontend/app/(protected)/dashboard/page.tsx
// Purpose: Displays the authenticated student dashboard after
// the required learning-profile onboarding has been completed.

import type {
  Metadata,
} from "next";

import {
  Anchor,
  Badge,
  Button,
  Container,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconBook,
  IconCalendarTime,
  IconCircleCheck,
  IconClock,
  IconLogout,
  IconUserCircle,
} from "@tabler/icons-react";

import {
  logoutAction,
} from "@/features/auth/actions/logout";
import {
  formatDuration,
} from "@/features/learning-profile/display";
import {
  requireCompletedLearningProfile,
} from "@/features/learning-profile/server/guards";

export const metadata: Metadata = {
  title:
    "Dashboard | STS Capstone Project",
  description:
    "Authenticated student dashboard.",
};

export default async function DashboardPage() {
  const snapshot =
    await requireCompletedLearningProfile();

  const learningProfile =
    snapshot.learningProfile;

  const displayName =
    snapshot.profile.full_name?.trim() ||
    "Student";

  return (
    <Container
      py={{ base: 32, sm: 56 }}
      size="lg"
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
              Student dashboard
            </Text>

            <Title order={1}>
              Welcome, {displayName}
            </Title>

            <Text c="dimmed">
              Your account and personalized
              learning profile are ready.
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

        <Paper
          p={{ base: "lg", sm: "xl" }}
          radius="lg"
          shadow="sm"
          withBorder
        >
          <Group
            align="flex-start"
            justify="space-between"
          >
            <Group
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                color="green"
                radius="md"
                size={48}
                variant="light"
              >
                <IconCircleCheck
                  size={26}
                />
              </ThemeIcon>

              <Stack gap={3}>
                <Text fw={700}>
                  Learning profile complete
                </Text>

                <Text
                  c="dimmed"
                  size="sm"
                >
                  Your study preferences,
                  challenges, subjects, and
                  availability have been
                  saved.
                </Text>
              </Stack>
            </Group>

            <Badge
              color="green"
              variant="light"
            >
              Onboarding complete
            </Badge>
          </Group>
        </Paper>

        <SimpleGrid
          cols={{
            base: 1,
            sm: 2,
            lg: 4,
          }}
          spacing="lg"
        >
          <Paper
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack gap="sm">
              <ThemeIcon
                color="violet"
                radius="md"
                variant="light"
              >
                <IconClock size={19} />
              </ThemeIcon>

              <Text
                c="dimmed"
                size="sm"
              >
                Preferred session
              </Text>

              <Text fw={700}>
                {formatDuration(
                  learningProfile
                    ?.preferred_study_duration_minutes ??
                    null,
                )}
              </Text>
            </Stack>
          </Paper>

          <Paper
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack gap="sm">
              <ThemeIcon
                color="violet"
                radius="md"
                variant="light"
              >
                <IconBook size={19} />
              </ThemeIcon>

              <Text
                c="dimmed"
                size="sm"
              >
                Saved subjects
              </Text>

              <Text fw={700}>
                {snapshot.subjects.length}
              </Text>
            </Stack>
          </Paper>

          <Paper
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack gap="sm">
              <ThemeIcon
                color="violet"
                radius="md"
                variant="light"
              >
                <IconCalendarTime
                  size={19}
                />
              </ThemeIcon>

              <Text
                c="dimmed"
                size="sm"
              >
                Available periods
              </Text>

              <Text fw={700}>
                {
                  snapshot.availability
                    .length
                }
              </Text>
            </Stack>
          </Paper>

          <Paper
            p="lg"
            radius="lg"
            withBorder
          >
            <Stack gap="sm">
              <ThemeIcon
                color="violet"
                radius="md"
                variant="light"
              >
                <IconUserCircle
                  size={19}
                />
              </ThemeIcon>

              <Text
                c="dimmed"
                size="sm"
              >
                Student profile
              </Text>

              <Anchor
                fw={700}
                href="/profile"
              >
                View profile
              </Anchor>
            </Stack>
          </Paper>
        </SimpleGrid>

        <Paper
          p={{ base: "lg", sm: "xl" }}
          radius="lg"
          withBorder
        >
          <Stack gap="sm">
            <Title order={2}>
              Phase 2 foundation ready
            </Title>

            <Text c="dimmed">
              Future dashboard, study-plan,
              task, reviewer, quiz, and AI
              features can now use the saved
              learning-profile information.
            </Text>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}