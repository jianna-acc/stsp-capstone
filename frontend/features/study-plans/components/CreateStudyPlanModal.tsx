// File: /frontend/features/study-plans/components/CreateStudyPlanModal.tsx
// Purpose: Lets students create a manual study plan.

"use client";

import {
  Alert,
  Button,
  Group,
  Modal,
  Stack,
  TextInput,
} from "@mantine/core";
import {
  IconAlertCircle,
} from "@tabler/icons-react";
import {
  FormEvent,
  useState,
} from "react";

import {
  createStudyPlan,
} from "../api";
import type {
  StudyPlan,
} from "../types";


interface CreateStudyPlanModalProps {
  opened: boolean;
  onClose: () => void;
  onCreated: (
    plan: StudyPlan,
  ) => void;
}


function getErrorMessage(
  error: unknown,
): string {
  if (
    error instanceof Error &&
    error.message.trim()
  ) {
    return error.message;
  }

  return "The study plan could not be created.";
}


export function CreateStudyPlanModal({
  opened,
  onClose,
  onCreated,
}: CreateStudyPlanModalProps) {
  const [
    title,
    setTitle,
  ] = useState("");

  const [
    startsOn,
    setStartsOn,
  ] = useState("");

  const [
    endsOn,
    setEndsOn,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    submitting,
    setSubmitting,
  ] = useState(false);


  function resetForm() {
    setTitle("");
    setStartsOn("");
    setEndsOn("");
    setError(null);
    setSubmitting(false);
  }


  function closeModal() {
    if (
      submitting
    ) {
      return;
    }

    resetForm();
    onClose();
  }


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const normalizedTitle =
      title.trim();

    if (
      !normalizedTitle
    ) {
      setError(
        "Enter a title for the study plan.",
      );

      return;
    }

    if (
      !startsOn ||
      !endsOn
    ) {
      setError(
        "Choose both a start date and an end date.",
      );

      return;
    }

    if (
      endsOn < startsOn
    ) {
      setError(
        "The end date cannot be earlier than the start date.",
      );

      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const createdPlan =
        await createStudyPlan({
          title:
            normalizedTitle,
          starts_on:
            startsOn,
          ends_on:
            endsOn,
        });

      onCreated(
        createdPlan,
      );

      resetForm();
      onClose();
    } catch (
      submitError
    ) {
      setError(
        getErrorMessage(
          submitError,
        ),
      );

      setSubmitting(false);
    }
  }


  return (
    <Modal
      opened={opened}
      onClose={
        closeModal
      }
      title="Create study plan"
      centered
    >
      <form
        onSubmit={
          handleSubmit
        }
      >
        <Stack>
          {error ? (
            <Alert
              color="red"
              icon={
                <IconAlertCircle
                  size={18}
                />
              }
            >
              {error}
            </Alert>
          ) : null}

          <TextInput
            label="Plan title"
            placeholder="Example: Finals review"
            value={title}
            onChange={(
              event,
            ) =>
              setTitle(
                event.currentTarget
                  .value,
              )
            }
            required
          />

          <TextInput
            label="Start date"
            type="date"
            value={startsOn}
            onChange={(
              event,
            ) =>
              setStartsOn(
                event.currentTarget
                  .value,
              )
            }
            required
          />

          <TextInput
            label="End date"
            type="date"
            value={endsOn}
            onChange={(
              event,
            ) =>
              setEndsOn(
                event.currentTarget
                  .value,
              )
            }
            required
          />

          <Group
            justify="flex-end"
            mt="sm"
          >
            <Button
              variant="default"
              onClick={
                closeModal
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
            >
              Create plan
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}