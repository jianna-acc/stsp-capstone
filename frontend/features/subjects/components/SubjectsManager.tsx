// File: /frontend/features/subjects/components/SubjectsManager.tsx
// Purpose: Displays and manages authenticated student subjects
// and opens each subject's learning-material workspace.

"use client";

import {
  ActionIcon,
  Badge,
  Button,
  Card,
  ColorSwatch,
  Group,
  Menu,
  Modal,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import {
  IconArrowRight,
  IconBook2,
  IconDotsVertical,
  IconEdit,
  IconFolderOpen,
  IconPlus,
  IconTrash,
} from "@tabler/icons-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  type FormEvent,
  useMemo,
  useState,
} from "react";

import {
  createSubjectAction,
  deleteSubjectAction,
  updateSubjectAction,
} from "../actions";
import {
  DEFAULT_SUBJECT_COLOR,
  SUBJECT_COLOR_OPTIONS,
} from "../constants";
import type {
  SubjectFieldErrors,
  SubjectInput,
  SubjectSummary,
} from "../types";

import classes from "./SubjectsManager.module.css";

interface SubjectsManagerProps {
  initialSubjects: SubjectSummary[];
}

const EMPTY_FORM: SubjectInput = {
  name: "",
  color: DEFAULT_SUBJECT_COLOR,
};

function sortSubjects(
  subjects: SubjectSummary[],
): SubjectSummary[] {
  return [...subjects].sort(
    (first, second) =>
      first.name.localeCompare(
        second.name,
        undefined,
        {
          sensitivity: "base",
        },
      ),
  );
}

export function SubjectsManager({
  initialSubjects,
}: SubjectsManagerProps) {
  const router = useRouter();

  const [
    modalOpened,
    {
      open: openModal,
      close: closeModal,
    },
  ] = useDisclosure(false);

  const [
    subjects,
    setSubjects,
  ] = useState(
    sortSubjects(initialSubjects),
  );

  const [
    editingSubject,
    setEditingSubject,
  ] =
    useState<SubjectSummary | null>(
      null,
    );

  const [form, setForm] =
    useState<SubjectInput>(
      EMPTY_FORM,
    );

  const [
    fieldErrors,
    setFieldErrors,
  ] =
    useState<SubjectFieldErrors>({});

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const [
    deletingId,
    setDeletingId,
  ] =
    useState<string | null>(null);

  const modalTitle = useMemo(
    () =>
      editingSubject
        ? "Edit subject"
        : "Create subject",
    [editingSubject],
  );

  function openCreateModal() {
    setEditingSubject(null);
    setForm(EMPTY_FORM);
    setFieldErrors({});
    openModal();
  }

  function openEditModal(
    subject: SubjectSummary,
  ) {
    setEditingSubject(subject);

    setForm({
      name: subject.name,
      color: subject.color,
    });

    setFieldErrors({});
    openModal();
  }

  function handleModalClose() {
    if (isSubmitting) {
      return;
    }

    closeModal();
    setEditingSubject(null);
    setForm(EMPTY_FORM);
    setFieldErrors({});
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setIsSubmitting(true);
    setFieldErrors({});

    const result = editingSubject
      ? await updateSubjectAction(
          editingSubject.id,
          form,
        )
      : await createSubjectAction(form);

    if (!result.success) {
      setFieldErrors(
        result.fieldErrors ?? {},
      );

      notifications.show({
        title: "Subject not saved",
        message: result.message,
        color: "red",
      });

      setIsSubmitting(false);
      return;
    }

    setSubjects(
      (currentSubjects) => {
        const remainingSubjects =
          currentSubjects.filter(
            (subject) =>
              subject.id !==
              result.subject.id,
          );

        return sortSubjects([
          ...remainingSubjects,
          result.subject,
        ]);
      },
    );

    notifications.show({
      title: editingSubject
        ? "Subject updated"
        : "Subject created",
      message: result.message,
      color: "green",
    });

    setIsSubmitting(false);
    closeModal();
    setEditingSubject(null);
    setForm(EMPTY_FORM);
    setFieldErrors({});

    router.refresh();
  }

  async function executeDelete(
    subject: SubjectSummary,
  ) {
    setDeletingId(subject.id);

    const result =
      await deleteSubjectAction(
        subject.id,
      );

    if (!result.success) {
      notifications.show({
        title:
          "Subject not deleted",
        message: result.message,
        color: "red",
      });

      setDeletingId(null);
      return;
    }

    setSubjects(
      (currentSubjects) =>
        currentSubjects.filter(
          (currentSubject) =>
            currentSubject.id !==
            result.deletedId,
        ),
    );

    notifications.show({
      title: "Subject deleted",
      message: result.message,
      color: "green",
    });

    setDeletingId(null);
    router.refresh();
  }

  function confirmDelete(
    subject: SubjectSummary,
  ) {
    modals.openConfirmModal({
      title: "Delete subject?",
      centered: true,
      children: (
        <Text size="sm">
          Delete{" "}
          <strong>
            {subject.name}
          </strong>
          ? This is only allowed when
          the subject has no uploaded
          files.
        </Text>
      ),
      labels: {
        confirm: "Delete subject",
        cancel: "Keep subject",
      },
      confirmProps: {
        color: "red",
      },
      onConfirm: () => {
        void executeDelete(subject);
      },
    });
  }

  return (
    <main className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text
            className={classes.eyebrow}
            fw={700}
          >
            SUBJECT MANAGEMENT
          </Text>

          <Title order={1}>
            Your subjects
          </Title>

          <Text
            c="dimmed"
            maw={650}
            mt="xs"
          >
            Choose a subject to upload
            materials, manage files, and
            prepare future reviewers and
            quizzes.
          </Text>
        </div>

        <Button
          leftSection={
            <IconPlus size={18} />
          }
          onClick={openCreateModal}
        >
          Create subject
        </Button>
      </div>

      {subjects.length === 0 ? (
        <Card
          withBorder
          radius="lg"
          padding="xl"
          className={
            classes.emptyState
          }
        >
          <ThemeIcon
            size={58}
            radius="xl"
            variant="light"
          >
            <IconFolderOpen
              size={30}
            />
          </ThemeIcon>

          <Stack
            gap={6}
            align="center"
          >
            <Title order={3}>
              No subjects yet
            </Title>

            <Text
              c="dimmed"
              ta="center"
              maw={430}
            >
              Create your first
              subject before uploading
              learning materials.
            </Text>
          </Stack>

          <Button
            leftSection={
              <IconPlus size={18} />
            }
            onClick={
              openCreateModal
            }
          >
            Create first subject
          </Button>
        </Card>
      ) : (
        <SimpleGrid
          cols={{
            base: 1,
            sm: 2,
            lg: 3,
          }}
          spacing="lg"
        >
          {subjects.map(
            (subject) => (
              <Card
                key={subject.id}
                withBorder
                radius="lg"
                padding="lg"
                className={
                  classes.card
                }
              >
                <Group
                  justify="space-between"
                  align="flex-start"
                  wrap="nowrap"
                >
                  <Group
                    align="flex-start"
                    wrap="nowrap"
                  >
                    <ThemeIcon
                      color={
                        subject.color
                      }
                      size={44}
                      radius="md"
                      variant="light"
                    >
                      <IconBook2
                        size={23}
                      />
                    </ThemeIcon>

                    <div>
                      <Text
                        fw={700}
                        size="lg"
                        className={
                          classes.subjectName
                        }
                      >
                        {subject.name}
                      </Text>

                      <Group
                        gap={7}
                        mt={5}
                      >
                        <ColorSwatch
                          size={12}
                          color={`var(--mantine-color-${subject.color}-6)`}
                        />

                        <Text
                          size="xs"
                          c="dimmed"
                          tt="capitalize"
                        >
                          {
                            subject.color
                          }
                        </Text>
                      </Group>
                    </div>
                  </Group>

                  <Menu
                    position="bottom-end"
                    withinPortal
                  >
                    <Menu.Target>
                      <ActionIcon
                        variant="subtle"
                        color="gray"
                        aria-label={`Manage ${subject.name}`}
                        disabled={
                          deletingId ===
                          subject.id
                        }
                      >
                        <IconDotsVertical
                          size={18}
                        />
                      </ActionIcon>
                    </Menu.Target>

                    <Menu.Dropdown>
                      <Menu.Item
                        leftSection={
                          <IconEdit
                            size={16}
                          />
                        }
                        onClick={() =>
                          openEditModal(
                            subject,
                          )
                        }
                      >
                        Edit subject
                      </Menu.Item>

                      <Menu.Item
                        color="red"
                        leftSection={
                          <IconTrash
                            size={16}
                          />
                        }
                        onClick={() =>
                          confirmDelete(
                            subject,
                          )
                        }
                      >
                        Delete subject
                      </Menu.Item>
                    </Menu.Dropdown>
                  </Menu>
                </Group>

                <Group
                  justify="space-between"
                  mt="xl"
                >
                  <Badge
                    variant="light"
                    color={
                      subject.color
                    }
                  >
                    Ready for files
                  </Badge>

                  <Text
                    size="xs"
                    c="dimmed"
                  >
                    Created{" "}
                    {new Intl.DateTimeFormat(
                      undefined,
                      {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      },
                    ).format(
                      new Date(
                        subject.created_at,
                      ),
                    )}
                  </Text>
                </Group>

                <Button
                  component={Link}
                  href={`/subjects/${subject.id}`}
                  color={
                    subject.color
                  }
                  variant="light"
                  fullWidth
                  mt="lg"
                  rightSection={
                    <IconArrowRight
                      size={17}
                    />
                  }
                >
                  Open subject
                </Button>
              </Card>
            ),
          )}
        </SimpleGrid>
      )}

      <Modal
        opened={modalOpened}
        onClose={handleModalClose}
        title={modalTitle}
        centered
        radius="lg"
        closeOnClickOutside={
          !isSubmitting
        }
        closeOnEscape={
          !isSubmitting
        }
      >
        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput
              label="Subject name"
              description="For example: Mathematics, Biology, or GESTSOC"
              placeholder="Enter a subject name"
              value={form.name}
              error={
                fieldErrors.name
              }
              maxLength={80}
              required
              autoFocus
              onChange={(event) => {
                const nextName =
                  event.currentTarget
                    .value;

                setForm(
                  (currentForm) => ({
                    ...currentForm,
                    name: nextName,
                  }),
                );
              }}
            />

            <Select
              label="Subject color"
              description="Used to identify the subject throughout the application"
              data={[
                ...SUBJECT_COLOR_OPTIONS,
              ]}
              value={form.color}
              error={
                fieldErrors.color
              }
              allowDeselect={false}
              required
              renderOption={({
                option,
              }) => (
                <Group gap="sm">
                  <ColorSwatch
                    size={16}
                    color={`var(--mantine-color-${option.value}-6)`}
                  />

                  <Text size="sm">
                    {option.label}
                  </Text>
                </Group>
              )}
              onChange={(value) =>
                setForm(
                  (currentForm) => ({
                    ...currentForm,
                    color:
                      value ??
                      DEFAULT_SUBJECT_COLOR,
                  }),
                )
              }
            />

            <Group
              justify="flex-end"
              mt="sm"
            >
              <Button
                variant="default"
                onClick={
                  handleModalClose
                }
                disabled={
                  isSubmitting
                }
              >
                Cancel
              </Button>

              <Button
                type="submit"
                loading={
                  isSubmitting
                }
              >
                {editingSubject
                  ? "Save changes"
                  : "Create subject"}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </main>
  );
}