// File: /frontend/features/study-plans/components/CreateStudySessionModal.tsx
// Purpose: Lets students add a manual study session
// to an existing study plan.

"use client";

import {
  Alert,
  Button,
  Group,
  Modal,
  Select,
  Stack,
  Textarea,
  TextInput,
} from "@mantine/core";
import {
  IconAlertCircle,
} from "@tabler/icons-react";
import {
  FormEvent,
  useState,
} from "react";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  createStudySession,
} from "../api";
import type {
  StudyPlan,
  StudySession,
} from "../types";


interface CreateStudySessionModalProps {
  opened: boolean;
  onClose: () => void;
  studyPlan: StudyPlan;
  subjects: SubjectSummary[];
  onCreated: (
    session: StudySession,
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

  return "The study session could not be created.";
}


export function CreateStudySessionModal({
  opened,
  onClose,
  studyPlan,
  subjects,
  onCreated,
}: CreateStudySessionModalProps) {
  const [
    subjectId,
    setSubjectId,
  ] = useState<
    string | null
  >(
    subjects[0]?.id ??
      null,
  );

  const [
    title,
    setTitle,
  ] = useState("");

  const [
    startsAt,
    setStartsAt,
  ] = useState("");

  const [
    endsAt,
    setEndsAt,
  ] = useState("");

  const [
    notes,
    setNotes,
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


  const subjectOptions =
    subjects.map(
      (subject) => ({
        value:
          subject.id,
        label:
          subject.name,
      }),
    );


  function resetForm() {
    setSubjectId(
      subjects[0]?.id ??
        null,
    );
    setTitle("");
    setStartsAt("");
    setEndsAt("");
    setNotes("");
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
      !subjectId
    ) {
      setError(
        "Choose a subject for the study session.",
      );

      return;
    }

    if (
      !normalizedTitle
    ) {
      setError(
        "Enter a title for the study session.",
      );

      return;
    }

    if (
      !startsAt ||
      !endsAt
    ) {
      setError(
        "Choose both a start time and an end time.",
      );

      return;
    }

    const startDate =
      new Date(
        startsAt,
      );

    const endDate =
      new Date(
        endsAt,
      );

    if (
      Number.isNaN(
        startDate.getTime(),
      ) ||
      Number.isNaN(
        endDate.getTime(),
      )
    ) {
      setError(
        "Enter valid study-session dates and times.",
      );

      return;
    }

    if (
      endDate.getTime() <=
      startDate.getTime()
    ) {
      setError(
        "The session must end after it starts.",
      );

      return;
    }

    const startDateOnly =
      startsAt.slice(
        0,
        10,
      );

    const endDateOnly =
      endsAt.slice(
        0,
        10,
      );

    if (
      startDateOnly <
        studyPlan.starts_on ||
      endDateOnly >
        studyPlan.ends_on
    ) {
      setError(
        "The study session must be scheduled within the plan date range.",
      );

      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const createdSession =
        await createStudySession(
          studyPlan.id,
          {
            subject_id:
              subjectId,
            title:
              normalizedTitle,
            starts_at:
              startDate.toISOString(),
            ends_at:
              endDate.toISOString(),
            notes:
              notes.trim() ||
              null,
          },
        );

      onCreated(
        createdSession,
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
      title="Add study session"
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

          <Select
            label="Subject"
            placeholder="Choose a subject"
            data={
              subjectOptions
            }
            value={
              subjectId
            }
            onChange={
              setSubjectId
            }
            searchable
            required
          />

          <TextInput
            label="Session title"
            placeholder="Example: Review cell division"
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
            label="Starts"
            type="datetime-local"
            value={
              startsAt
            }
            onChange={(
              event,
            ) =>
              setStartsAt(
                event.currentTarget
                  .value,
              )
            }
            required
          />

          <TextInput
            label="Ends"
            type="datetime-local"
            value={
              endsAt
            }
            onChange={(
              event,
            ) =>
              setEndsAt(
                event.currentTarget
                  .value,
              )
            }
            required
          />

          <Textarea
            label="Notes"
            placeholder="Optional notes"
            value={notes}
            onChange={(
              event,
            ) =>
              setNotes(
                event.currentTarget
                  .value,
              )
            }
            autosize
            minRows={2}
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
              Add session
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}