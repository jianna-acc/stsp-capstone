// File: /frontend/components/foundation/BackendHealthCheck.tsx
// Purpose: Lets developers verify the connection between the
// Next.js frontend and the FastAPI backend.

"use client";

import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Group,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCircleCheck,
  IconPlugConnected,
  IconRefresh,
  IconServer,
} from "@tabler/icons-react";

import {
  ApiRequestError,
  getApiHealth,
} from "@/services/api";
import type { ApiHealthResponse } from "@/types/api";

import classes from "./BackendHealthCheck.module.css";

type HealthCheckState =
  | {
      status: "idle";
    }
  | {
      status: "loading";
    }
  | {
      status: "success";
      data: ApiHealthResponse;
    }
  | {
      status: "error";
      message: string;
    };

function getStatusDetails(
  status: HealthCheckState["status"],
): {
  color: string;
  label: string;
} {
  switch (status) {
    case "loading":
      return {
        color: "blue",
        label: "Checking",
      };

    case "success":
      return {
        color: "green",
        label: "Connected",
      };

    case "error":
      return {
        color: "red",
        label: "Unavailable",
      };

    default:
      return {
        color: "gray",
        label: "Not checked",
      };
  }
}

export function BackendHealthCheck() {
  const [state, setState] =
    useState<HealthCheckState>({
      status: "idle",
    });

  const statusDetails =
    getStatusDetails(state.status);

  async function checkBackend(): Promise<void> {
    setState({
      status: "loading",
    });

    try {
      const healthData = await getApiHealth();

      setState({
        status: "success",
        data: healthData,
      });
    } catch (error) {
      const message =
        error instanceof ApiRequestError
          ? error.message
          : "An unexpected connection error occurred.";

      setState({
        status: "error",
        message,
      });
    }
  }

  const buttonLabel =
    state.status === "success"
      ? "Check again"
      : state.status === "error"
        ? "Retry connection"
        : "Check backend";

  const ButtonIcon =
    state.status === "error"
      ? IconRefresh
      : IconPlugConnected;

  return (
    <section className={classes.root}>
      <Stack gap="lg">
        <Group
          className={classes.header}
          justify="space-between"
          align="flex-start"
          wrap="nowrap"
        >
          <Group gap="sm" wrap="nowrap">
            <ThemeIcon
              color="brand"
              variant="light"
              size={44}
              radius="md"
            >
              <IconServer size={22} />
            </ThemeIcon>

            <div className={classes.heading}>
              <Title order={3}>
                Backend connection
              </Title>

              <Text c="dimmed" size="sm" mt={4}>
                Verify that the frontend can communicate
                with the FastAPI health endpoint.
              </Text>
            </div>
          </Group>

          <Badge
            color={statusDetails.color}
            variant="light"
          >
            {statusDetails.label}
          </Badge>
        </Group>

        <div
          className={classes.result}
          aria-live="polite"
        >
          {state.status === "idle" && (
            <Text size="sm" c="dimmed">
              No connection test has been run yet.
              Start the backend before checking.
            </Text>
          )}

          {state.status === "loading" && (
            <Alert
              color="blue"
              variant="light"
              title="Checking the backend"
              icon={<IconPlugConnected size={18} />}
            >
              The frontend is waiting for a response from
              the FastAPI application.
            </Alert>
          )}

          {state.status === "success" && (
            <Stack gap="sm">
              <Alert
                color="green"
                variant="light"
                title="Backend connected"
                icon={<IconCircleCheck size={18} />}
              >
                The frontend successfully received a valid
                health response.
              </Alert>

              <SimpleGrid
                cols={{ base: 1, sm: 2 }}
                spacing="sm"
              >
                <div className={classes.detailItem}>
                  <Text size="xs" c="dimmed">
                    Service
                  </Text>

                  <Text fw={600}>
                    {state.data.service}
                  </Text>
                </div>

                <div className={classes.detailItem}>
                  <Text size="xs" c="dimmed">
                    Status
                  </Text>

                  <Text fw={600}>
                    {state.data.status}
                  </Text>
                </div>

                <div className={classes.detailItem}>
                  <Text size="xs" c="dimmed">
                    Version
                  </Text>

                  <Text fw={600}>
                    {state.data.version}
                  </Text>
                </div>

                <div className={classes.detailItem}>
                  <Text size="xs" c="dimmed">
                    Environment
                  </Text>

                  <Text fw={600}>
                    {state.data.environment}
                  </Text>
                </div>
              </SimpleGrid>
            </Stack>
          )}

          {state.status === "error" && (
            <Stack gap="sm">
              <Alert
                color="red"
                variant="light"
                title="Could not reach the backend"
                icon={<IconAlertCircle size={18} />}
              >
                {state.message}
              </Alert>

              <Text size="sm" c="dimmed">
                Confirm that FastAPI is running and that
                NEXT_PUBLIC_API_BASE_URL contains the
                correct backend address.
              </Text>
            </Stack>
          )}
        </div>

        <Button
          className={classes.action}
          onClick={checkBackend}
          loading={state.status === "loading"}
          leftSection={<ButtonIcon size={18} />}
        >
          {buttonLabel}
        </Button>
      </Stack>
    </section>
  );
}