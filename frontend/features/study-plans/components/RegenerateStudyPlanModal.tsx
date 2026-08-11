// File: /frontend/features/study-plans/components/RegenerateStudyPlanModal.tsx
// Purpose: Confirms and performs regeneration of an existing
// generated study plan while preserving manually added sessions.

"use client";

import {
  Alert,
  Button,
  Group,
  Modal,
  Stack,
  Text,
} from "@mantine/core";
import {
  useState,
} from "react";

import {
  regenerateStudyPlan,
} from "../api";
import type {
  SchedulableTask,
  StudyPlan,
  StudyPlanGenerationResponse,
} from "../types";


interface RegenerateStudyPlanModalProps {
  opened: boolean;
  onClose: () => void;
  studyPlan: StudyPlan | null;
  tasks: SchedulableTask[];
  onRegenerated: (
    result: StudyPlanGenerationResponse,
  ) => void;
}


export function RegenerateStudyPlanModal({
  opened,
  onClose,
  studyPlan,
  tasks,
  onRegenerated,
}: RegenerateStudyPlanModalProps) {
  const [
    submitting,
    setSubmitting,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    result,
    setResult,
  ] = useState<
    StudyPlanGenerationResponse | null
  >(null);


  function reset(): void {
    setSubmitting(
      false,
    );

    setError(
      null,
    );

    setResult(
      null,
    );
  }


  function handleClose(): void {
    if (submitting) {
      return;
    }

    reset();
    onClose();
  }


  async function handleRegenerate():
    Promise<void> {
    if (
      !studyPlan ||
      studyPlan.generation_mode !==
        "generated"
    ) {
      setError(
        "Only generated study plans can be regenerated.",
      );
      return;
    }

    if (
      tasks.length ===
      0
    ) {
      setError(
        "No schedulable academic tasks are available.",
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
      const regeneratedResult =
        await regenerateStudyPlan(
          studyPlan.id,
          {
            tasks,
          },
        );

      setResult(
        regeneratedResult,
      );

      onRegenerated(
        regeneratedResult,
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "The study plan could not be regenerated.",
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
      opened={
        opened &&
        studyPlan !== null
      }
      onClose={
        handleClose
      }
      title="Regenerate study plan"
      centered
    >
      {result ? (
        <Stack>
          <Text fw={700}>
            Study plan regenerated
          </Text>

          <Text size="sm">
            {result.sessions.length ===
            1
              ? "1 study session is now in the refreshed plan."
              : `${result.sessions.length} study sessions are now in the refreshed plan.`}
          </Text>

          <Text
            size="sm"
            c="dimmed"
          >
            Manually added sessions
            were preserved.
          </Text>

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
              available future
              study schedule.
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
        <Stack>
          <Text size="sm">
            Regenerate{" "}
            <strong>
              {studyPlan?.title}
            </strong>
            {" "}using your latest
            academic tasks, study
            availability, and
            preferences?
          </Text>

          <Alert color="blue">
            Existing generated
            sessions will be
            replaced. Manually
            added sessions will
            stay in the plan and
            will be treated as
            unavailable study time.
          </Alert>

          <Text
            size="sm"
            c="dimmed"
          >
            {tasks.length}{" "}
            eligible{" "}
            {tasks.length ===
            1
              ? "task is"
              : "tasks are"}{" "}
            currently available
            for scheduling.
          </Text>

          {tasks.length ===
          0 ? (
            <Alert color="yellow">
              No schedulable
              academic tasks are
              available.
            </Alert>
          ) : null}

          {error ? (
            <Alert color="red">
              {error}
            </Alert>
          ) : null}

          <Group
            justify="flex-end"
          >
            <Button
              variant="default"
              disabled={
                submitting
              }
              onClick={
                handleClose
              }
            >
              Cancel
            </Button>

            <Button
              loading={
                submitting
              }
              disabled={
                tasks.length ===
                0
              }
              onClick={() => {
                void handleRegenerate();
              }}
            >
              Regenerate plan
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}