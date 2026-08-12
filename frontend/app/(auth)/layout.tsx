// File: /frontend/app/(auth)/layout.tsx
// Purpose: Provides the shared visual shell for public
// authentication pages.

import type {
  ReactNode,
} from "react";

import {
  Box,
  Group,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconBrain,
  IconCalendarTime,
  IconSparkles,
} from "@tabler/icons-react";

import classes from "./auth-layout.module.css";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({
  children,
}: Readonly<AuthLayoutProps>) {
  return (
    <Box className={classes.page}>
      <Box
        className={classes.brandPanel}
        component="aside"
      >
        <Stack
          className={classes.brandContent}
          gap="xl"
        >
          <Text className={classes.brandLabel}>
            Intelleap
          </Text>

          <Stack gap="md">
            <Title
              className={classes.brandTitle}
              order={1}
            >
              Build study habits that fit
              how you learn.
            </Title>

            <Text
              className={
                classes.brandDescription
              }
            >
              Organize academic priorities,
              create personalized study plans,
              and turn uploaded learning
              materials into useful reviewers
              and quizzes.
            </Text>
          </Stack>

          <Stack gap="lg">
            <Group
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                className={classes.featureIcon}
                radius="md"
                size={42}
                variant="transparent"
              >
                <IconBrain
                  color="white"
                  size={22}
                />
              </ThemeIcon>

              <div>
                <Text
                  className={
                    classes.featureTitle
                  }
                >
                  Personalized learning
                </Text>

                <Text
                  className={
                    classes.featureText
                  }
                  size="sm"
                >
                  Recommendations adapt to
                  deadlines, study habits,
                  and academic performance.
                </Text>
              </div>
            </Group>

            <Group
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                className={classes.featureIcon}
                radius="md"
                size={42}
                variant="transparent"
              >
                <IconCalendarTime
                  color="white"
                  size={22}
                />
              </ThemeIcon>

              <div>
                <Text
                  className={
                    classes.featureTitle
                  }
                >
                  Practical study planning
                </Text>

                <Text
                  className={
                    classes.featureText
                  }
                  size="sm"
                >
                  Plans remain editable so
                  students stay in control of
                  their schedules.
                </Text>
              </div>
            </Group>

            <Group
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                className={classes.featureIcon}
                radius="md"
                size={42}
                variant="transparent"
              >
                <IconSparkles
                  color="white"
                  size={22}
                />
              </ThemeIcon>

              <div>
                <Text
                  className={
                    classes.featureTitle
                  }
                >
                  Clear AI explanations
                </Text>

                <Text
                  className={
                    classes.featureText
                  }
                  size="sm"
                >
                  Recommendations explain
                  why a task or topic needs
                  attention.
                </Text>
              </div>
            </Group>
          </Stack>
        </Stack>
      </Box>

      <Box
        className={classes.formPanel}
        component="main"
      >
        <Box className={classes.formCard}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}