// File: /frontend/features/learning-profile/components/OnboardingShell.tsx
// Purpose: Provides the shared heading, progress indicator, and
// responsive content container for every onboarding step.

import type {
  ReactNode,
} from "react";

import {
  Badge,
  Container,
  Group,
  Paper,
  Progress,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import {
  ONBOARDING_STEP_COUNT,
  type OnboardingStep,
} from "../constants";
import {
  ONBOARDING_STEP_LABELS,
} from "../routing";

interface OnboardingShellProps {
  currentStep: OnboardingStep;
  percentage: number;
  title: string;
  description: string;
  children: ReactNode;
}

export function OnboardingShell({
  currentStep,
  percentage,
  title,
  description,
  children,
}: Readonly<OnboardingShellProps>) {
  const safePercentage = Math.min(
    100,
    Math.max(0, percentage),
  );

  return (
    <Container
      py={{ base: 28, sm: 48 }}
      size="md"
    >
      <Stack gap="xl">
        <Stack gap="md">
          <Group
            align="center"
            justify="space-between"
          >
            <Badge
              color="violet"
              size="lg"
              variant="light"
            >
              Step {currentStep} of{" "}
              {ONBOARDING_STEP_COUNT}
            </Badge>

            <Text
              c="dimmed"
              fw={600}
              size="sm"
            >
              {safePercentage}% complete
            </Text>
          </Group>

          <Progress
            aria-label={`Onboarding progress: ${safePercentage}% complete`}
            color="violet"
            radius="xl"
            size="md"
            value={safePercentage}
          />

          <Stack gap={4}>
            <Text
              c="violet.7"
              fw={700}
              size="sm"
            >
              {
                ONBOARDING_STEP_LABELS[
                  currentStep
                ]
              }
            </Text>

            <Title order={1}>
              {title}
            </Title>

            <Text
              c="dimmed"
              maw={680}
            >
              {description}
            </Text>
          </Stack>
        </Stack>

        <Paper
          p={{ base: "lg", sm: "xl" }}
          radius="lg"
          shadow="sm"
          withBorder
        >
          {children}
        </Paper>
      </Stack>
    </Container>
  );
}