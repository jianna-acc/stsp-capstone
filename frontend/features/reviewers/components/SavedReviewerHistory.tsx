// File: /frontend/features/reviewers/components/SavedReviewerHistory.tsx
// Purpose: Displays saved reviewers and lets the student
// reopen or delete previously generated reviewers.

"use client";

import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconBook2,
  IconTrash,
} from "@tabler/icons-react";

import type {
  ReviewerResponse,
} from "@/features/reviewers/types";

interface SavedReviewerHistoryProps {
  reviewers: ReviewerResponse[];
  isLoading: boolean;
  error: string | null;
  selectedReviewerId: string | null;
  deletingReviewerId: string | null;
  onOpen: (
    reviewerId: string,
  ) => void | Promise<void>;
  onDelete: (
    reviewerId: string,
  ) => void | Promise<void>;
}

function formatReviewerDate(
  value: string,
): string {
  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-PH",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

export function SavedReviewerHistory({
  reviewers,
  isLoading,
  error,
  selectedReviewerId,
  deletingReviewerId,
  onOpen,
  onDelete,
}: Readonly<SavedReviewerHistoryProps>) {
  return (
    <section
      aria-labelledby="saved-reviewers-title"
    >
      <Stack gap="md">
        <div>
          <Title
            order={2}
            id="saved-reviewers-title"
          >
            Saved Reviewers
          </Title>

          <Text
            c="dimmed"
            size="sm"
            mt={4}
          >
            Reopen reviewers you generated
            previously.
          </Text>
        </div>

        {isLoading && (
          <Group gap="sm">
            <Loader size="sm" />

            <Text
              size="sm"
              c="dimmed"
            >
              Loading saved reviewers...
            </Text>
          </Group>
        )}

        {error && (
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
        )}

        {!isLoading &&
          !error &&
          reviewers.length === 0 && (
            <Card
              withBorder
              radius="md"
              padding="lg"
            >
              <Text c="dimmed">
                You do not have any saved
                reviewers yet.
              </Text>
            </Card>
          )}

        {!isLoading &&
          reviewers.length > 0 && (
            <Stack gap="sm">
              {reviewers.map(
                (reviewer) => {
                  const isSelected =
                    reviewer.id ===
                    selectedReviewerId;

                  const isDeleting =
                    reviewer.id ===
                    deletingReviewerId;

                  return (
                    <Card
                      key={reviewer.id}
                      withBorder
                      radius="md"
                      padding="md"
                    >
                      <Stack gap="sm">
                        <Group
                          justify="space-between"
                          align="flex-start"
                        >
                          <div>
                            <Group gap="xs">
                              <IconBook2
                                size={18}
                              />

                              <Text fw={600}>
                                {
                                  reviewer.title
                                }
                              </Text>
                            </Group>

                            <Text
                              size="xs"
                              c="dimmed"
                              mt={4}
                            >
                              {formatReviewerDate(
                                reviewer.updated_at,
                              )}
                            </Text>
                          </div>

                          <Group gap="xs">
                            <Badge
                              variant="light"
                            >
                              {
                                reviewer.reviewer_length
                              }
                            </Badge>

                            <Badge
                              variant="outline"
                            >
                              Generation{" "}
                              {
                                reviewer.generation_count
                              }
                            </Badge>
                          </Group>
                        </Group>

                        <Group
                          justify="flex-end"
                        >
                          <Button
                            variant={
                              isSelected
                                ? "filled"
                                : "light"
                            }
                            onClick={() => {
                              void onOpen(
                                reviewer.id,
                              );
                            }}
                            disabled={
                              isDeleting
                            }
                          >
                            {isSelected
                              ? "Opened"
                              : "Open"}
                          </Button>

                          <Button
                            color="red"
                            variant="subtle"
                            leftSection={
                              <IconTrash
                                size={16}
                              />
                            }
                            loading={
                              isDeleting
                            }
                            onClick={() => {
                              void onDelete(
                                reviewer.id,
                              );
                            }}
                          >
                            Delete
                          </Button>
                        </Group>
                      </Stack>
                    </Card>
                  );
                },
              )}
            </Stack>
          )}
      </Stack>
    </section>
  );
}