// File: /frontend/components/foundation/MantineFoundationCheck.tsx
// Purpose: Verifies that Mantine components, theme colors,
// notifications, modals, icons, and responsive layouts work correctly.

"use client";

import {
  Badge,
  Button,
  Card,
  Container,
  Group,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import {
  IconBell,
  IconCheck,
  IconComponents,
  IconLayoutDashboard,
  IconShieldCheck,
  IconSparkles,
} from "@tabler/icons-react";

import classes from "./MantineFoundationCheck.module.css";

const systemChecks = [
  {
    title: "Theme connected",
    description:
      "The custom purple palette, rounded shapes, and soft shadows are active.",
    icon: IconSparkles,
  },
  {
    title: "Providers connected",
    description:
      "Notifications and confirmation modals are available throughout the app.",
    icon: IconComponents,
  },
  {
    title: "Responsive foundation",
    description:
      "The layout adjusts for desktop, tablet, and mobile screens.",
    icon: IconLayoutDashboard,
  },
];

export function MantineFoundationCheck() {
  function showNotification() {
    notifications.show({
      title: "Notification system is working",
      message:
        "Mantine notifications are connected to the application.",
      color: "green",
      icon: <IconCheck size={18} />,
    });
  }

  function showConfirmationModal() {
    modals.openConfirmModal({
      title: "Confirm system test",
      centered: true,

      children: (
        <Text size="sm">
          This modal confirms that the global Mantine modal
          manager is connected correctly.
        </Text>
      ),

      labels: {
        confirm: "Confirm test",
        cancel: "Cancel",
      },

      confirmProps: {
        color: "brand",
      },

      onConfirm: () => {
        notifications.show({
          title: "Confirmation successful",
          message:
            "The modal and notification systems are both working.",
          color: "green",
          icon: <IconShieldCheck size={18} />,
        });
      },
    });
  }

  return (
    <main className={classes.page}>
      <Container size="md" w="100%">
        <Card className={classes.card} p="xl">
          <Stack gap="xl">
            <div>
              <Badge color="brand" variant="light">
                Phase 1D
              </Badge>

              <Title order={1} mt="md">
                Mantine foundation is ready
              </Title>

              <Text c="dimmed" mt="sm" maw={660}>
                The global theme and interface providers are now
                connected. Use the controls below to test the
                interactive systems.
              </Text>
            </div>

            <SimpleGrid cols={{ base: 1, sm: 3 }}>
              {systemChecks.map((check) => {
                const CheckIcon = check.icon;

                return (
                  <div
                    className={classes.statusCard}
                    key={check.title}
                  >
                    <ThemeIcon
                      color="brand"
                      variant="light"
                      size={44}
                      radius="md"
                    >
                      <CheckIcon size={22} />
                    </ThemeIcon>

                    <Text fw={600} mt="md">
                      {check.title}
                    </Text>

                    <Text c="dimmed" size="sm" mt={6}>
                      {check.description}
                    </Text>
                  </div>
                );
              })}
            </SimpleGrid>

            <Group className={classes.actions}>
              <Button
                leftSection={<IconBell size={18} />}
                onClick={showNotification}
              >
                Test notification
              </Button>

              <Button
                variant="default"
                leftSection={<IconShieldCheck size={18} />}
                onClick={showConfirmationModal}
              >
                Test confirmation modal
              </Button>
            </Group>

            <Text size="sm" c="dimmed">
              Temporary application name: STS Capstone Project
            </Text>
          </Stack>
        </Card>
      </Container>
    </main>
  );
}