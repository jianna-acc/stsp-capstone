// File: /frontend/features/study-plans/components/GenerateStudyPlanModal.tsx
// Purpose: Collects study-plan generation settings and sends
// schedulable tasks to the Track D generation endpoint.

"use client";

import {
  Alert,
  Button,
  Group,
  Modal,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import {
  useState,
  type FormEvent,
} from "react";

import {
  generateStudyPlan,
} from "../api";
import type {
  SchedulableTask,
  StudyPlanGenerationResponse,
} from "../types";


interface GenerateStudyPlanModalProps {
  opened: boolean;
  onClose: () => void;
  tasks: SchedulableTask[];
  onGenerated: (
    result: StudyPlanGenerationResponse,
  ) => void;
}


function getPlanSpanDays(
  startsOn: string,
  endsOn: string,
): number {
  const start =
    Date.parse(
      `${startsOn}T00:00:00Z`,
    );

  const end =
    Date.parse(
      `${endsOn}T00:00:00Z`,
    );

  return Math.round(
    (
      end -
      start
    ) /
      86_400_000,
  );
}


export function GenerateStudyPlanModal({
  opened,
  onClose,
  tasks,
  onGenerated,
}: GenerateStudyPlanModalProps) {
  const [
    title,
    setTitle,
  ] =
    useState("");

  const [
    startsOn,
    setStartsOn,
  ] =
    useState("");

  const [
    endsOn,
    setEndsOn,
  ] =
    useState("");

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);

  const [
    submitting,
    setSubmitting,
  ] =
    useState(false);

  const [
    result,
    setResult,
  ] =
    useState<
      StudyPlanGenerationResponse | null
    >(null);


  function reset(): void {
    setTitle("");
    setStartsOn("");
    setEndsOn("");
    setError(
      null,
    );
    setSubmitting(
      false,
    );
    setResult(
      null,
    );
  }


  function handleClose(): void {
    reset();
    onClose();
  }


  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    const normalizedTitle =
      title.trim();

    if (!normalizedTitle) {
      setError(
        "Plan title is required.",
      );
      return;
    }

    if (
      normalizedTitle.length >
      160
    ) {
      setError(
        "Plan title cannot exceed 160 characters.",
      );
      return;
    }

    if (
      !startsOn ||
      !endsOn
    ) {
      setError(
        "Start and end dates are required.",
      );
      return;
    }

    if (
      endsOn <
      startsOn
    ) {
      setError(
        "End date cannot be before start date.",
      );
      return;
    }

    if (
      getPlanSpanDays(
        startsOn,
        endsOn,
      ) > 366
    ) {
      setError(
        "Study plan cannot exceed 366 days.",
      );
      return;
    }

    if (
      tasks.length ===
      0
    ) {
      setError(
        "No schedulable tasks are available.",
      );
      return;
    }

    if (
      tasks.length >
      500
    ) {
      setError(
        "A study plan can include at most 500 tasks.",
      );
      return;
    }

    setSubmitting(
      true,
    );
    setError(
      null,
    );

    try {
      const generatedResult =
        await generateStudyPlan({
          title:
            normalizedTitle,
          starts_on:
            startsOn,
          ends_on:
            endsOn,
          tasks,
        });

      setResult(
        generatedResult,
      );

      onGenerated(
        generatedResult,
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "The study plan could not be generated.",
      );
    } finally {
      setSubmitting(
        false,
      );
    }
  }


  const unscheduledMinutes =
    result?.unscheduled_tasks.reduce(
      (
        total,
        task,
      ) =>
        total +
        task.remaining_minutes,
      0,
    ) ?? 0;


  return (
    <Modal
      opened={opened}
      onClose={
        handleClose
      }
      title="Generate study plan"
      centered
    >
      {result ? (
        <Stack>
          <Alert
            title="Study plan generated"
          >
            {result.sessions.length ===
            1
              ? "1 study session was generated."
              : `${result.sessions.length} study sessions were generated.`}
          </Alert>

          {result
            .unscheduled_tasks
            .length >
          0 ? (
            <Alert
              color="yellow"
              title="Some work could not be scheduled"
            >
              {result
                .unscheduled_tasks
                .length ===
              1
                ? `1 task still has ${unscheduledMinutes} minutes of unscheduled work.`
                : `${result.unscheduled_tasks.length} tasks still have ${unscheduledMinutes} minutes of unscheduled work.`}
            </Alert>
          ) : (
            <Text
              size="sm"
              c="dimmed"
            >
              All requested work
              fit within the
              available study
              schedule.
            </Text>
          )}

          <Group
            justify="flex-end"
          >
            <Button
              onClick={
                handleClose
              }
            >
              Done
            </Button>
          </Group>
        </Stack>
      ) : (
        <form
          onSubmit={
            handleSubmit
          }
        >
          <Stack>
            <Text
              size="sm"
              c="dimmed"
            >
              The scheduler will
              use{" "}
              {tasks.length}{" "}
              eligible{" "}
              {tasks.length ===
              1
                ? "task"
                : "tasks"}{" "}
              together with your
              saved study
              availability and
              preferences.
            </Text>

            {tasks.length ===
            0 ? (
              <Alert
                color="yellow"
              >
                No schedulable
                tasks are
                available.
              </Alert>
            ) : null}

            <TextInput
              label="Plan title"
              placeholder="Finals study plan"
              required
              maxLength={
                160
              }
              value={
                title
              }
              onChange={(
                event,
              ) =>
                setTitle(
                  event
                    .currentTarget
                    .value,
                )
              }
            />

            <TextInput
              label="Start date"
              type="date"
              required
              value={
                startsOn
              }
              onChange={(
                event,
              ) =>
                setStartsOn(
                  event
                    .currentTarget
                    .value,
                )
              }
            />

            <TextInput
              label="End date"
              type="date"
              required
              value={
                endsOn
              }
              onChange={(
                event,
              ) =>
                setEndsOn(
                  event
                    .currentTarget
                    .value,
                )
              }
            />

            {error ? (
              <Alert
                color="red"
              >
                {error}
              </Alert>
            ) : null}

            <Group
              justify="flex-end"
            >
              <Button
                variant="default"
                onClick={
                  handleClose
                }
                disabled={
                  submitting
                }
              >
                Cancel
              </Button>

              <Button
                type="submit"
                loading={
                  submitting
                }
                disabled={
                  tasks.length ===
                  0
                }
              >
                Generate plan
              </Button>
            </Group>
          </Stack>
        </form>
      )}
    </Modal>
  );
}