// File: /frontend/features/reviewers/components/ReviewerWorkspace.tsx
// Purpose: Combines reviewer generation controls with the
// newly generated reviewer result in one protected workspace.

"use client";

import {
  Badge,
  Container,
  Group,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconBook2,
  IconSparkles,
} from "@tabler/icons-react";
import {
  useEffect,
  useState,
} from "react";

import type {
  ReviewerFilterOptions,
  ReviewerResponse,
} from "@/features/reviewers/types";

import {
  ReviewerGenerationForm,
} from "./ReviewerGenerationForm";
import {
  ReviewerResult,
} from "./ReviewerResult";
import classes from "./ReviewerWorkspace.module.css";

import {
  SavedReviewerHistory,
} from "./SavedReviewerHistory";

import {
  deleteReviewer,
  getReviewer,
  listReviewers,
  regenerateReviewer,
} from "@/features/reviewers/api";

interface ReviewerWorkspaceProps {
  filterOptions:
    ReviewerFilterOptions;
}

export function ReviewerWorkspace({
  filterOptions,
}: Readonly<ReviewerWorkspaceProps>) {
  const [
    generatedReviewer,
    setGeneratedReviewer,
  ] = useState<
    ReviewerResponse | null
  >(null);

    const [
    isRegenerating,
    setIsRegenerating,
  ] = useState(false);

  const [
    regenerationError,
    setRegenerationError,
  ] = useState<string | null>(
    null,
  );

  const [
  savedReviewers,
  setSavedReviewers,
] = useState<ReviewerResponse[]>([]);

const [
  isLoadingHistory,
  setIsLoadingHistory,
] = useState(true);

const [
  historyError,
  setHistoryError,
] = useState<string | null>(
  null,
);

const [
  deletingReviewerId,
  setDeletingReviewerId,
] = useState<string | null>(
  null,
);

useEffect(() => {
  const controller =
    new AbortController();

  async function loadSavedReviewers():
    Promise<void> {
    setIsLoadingHistory(true);
    setHistoryError(null);

    try {
      const response =
        await listReviewers({
          limit: 50,
          signal:
            controller.signal,
        });

      setSavedReviewers(
        response.items,
      );
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      setHistoryError(
        error instanceof Error
          ? error.message
          : "Saved reviewers could not be loaded.",
      );
    } finally {
      if (
        !controller.signal.aborted
      ) {
        setIsLoadingHistory(false);
      }
    }
  }

  void loadSavedReviewers();

  return () => {
    controller.abort();
  };
}, []);

async function handleOpenReviewer(
  reviewerId: string,
): Promise<void> {
  setHistoryError(null);
  setRegenerationError(null);

  try {
    const reviewer =
      await getReviewer(
        reviewerId,
      );

    setGeneratedReviewer(
      reviewer,
    );
  } catch (error) {
    setHistoryError(
      error instanceof Error
        ? error.message
        : "The saved reviewer could not be opened.",
    );
  }
}

async function handleDeleteReviewer(
  reviewerId: string,
): Promise<void> {
  const reviewer =
    savedReviewers.find(
      (item) =>
        item.id === reviewerId,
    );

  const confirmed =
    window.confirm(
      reviewer
        ? `Delete "${reviewer.title}"? This cannot be undone.`
        : "Delete this reviewer? This cannot be undone.",
    );

  if (!confirmed) {
    return;
  }

  setDeletingReviewerId(
    reviewerId,
  );
  setHistoryError(null);

  try {
    await deleteReviewer(
      reviewerId,
    );

    setSavedReviewers(
      (current) =>
        current.filter(
          (item) =>
            item.id !==
            reviewerId,
        ),
    );

    setGeneratedReviewer(
      (current) =>
        current?.id ===
        reviewerId
          ? null
          : current,
    );
  } catch (error) {
    setHistoryError(
      error instanceof Error
        ? error.message
        : "The reviewer could not be deleted.",
    );
  } finally {
    setDeletingReviewerId(
      null,
    );
  }
}

  function handleGenerated(
    reviewer: ReviewerResponse,
    ): void {
    setGeneratedReviewer(
        reviewer,
    );

    setSavedReviewers(
        (current) => [
        reviewer,
        ...current.filter(
            (item) =>
            item.id !== reviewer.id,
        ),
        ],
    );

    setRegenerationError(null);
    }
  async function handleRegenerate():
    Promise<void> {
    if (
      !generatedReviewer ||
      isRegenerating
    ) {
      return;
    }

    setIsRegenerating(true);
    setRegenerationError(null);

    try {
      const regeneratedReviewer =
        await regenerateReviewer(
          generatedReviewer.id,
        );

      setGeneratedReviewer(
        regeneratedReviewer,
      );
      setSavedReviewers(
        (current) =>
            current.map(
            (item) =>
                item.id ===
                regeneratedReviewer.id
                ? regeneratedReviewer
                : item,
            ),
        );
    } catch (error) {
      setRegenerationError(
        error instanceof Error
          ? error.message
          : "The reviewer could not be regenerated.",
      );
    } finally {
      setIsRegenerating(false);
    }
  }
  return (
    <main
      className={
        classes.page
      }
    >
      <Container
        size="xl"
        className={
          classes.container
        }
      >
        <Stack gap="xl">
          <header
            className={
              classes.header
            }
          >
            <Group
              align="flex-start"
              wrap="nowrap"
              gap="md"
            >
              <ThemeIcon
                size={52}
                radius="lg"
                variant="gradient"
                gradient={{
                  from: "violet",
                  to: "grape",
                }}
              >
                <IconBook2
                  size={28}
                  stroke={1.8}
                />
              </ThemeIcon>

              <div>
                <Group gap="sm">
                  <Title order={1}>
                    Reviewers
                  </Title>

                  <Badge
                    variant="light"
                    color="violet"
                    leftSection={
                      <IconSparkles
                        size={13}
                      />
                    }
                  >
                    AI-powered
                  </Badge>
                </Group>

                <Text
                  c="dimmed"
                  mt={5}
                  maw={700}
                >
                  Turn your uploaded study
                  materials into structured
                  reviewers with summaries,
                  key points, important
                  terms, and source
                  references.
                </Text>
              </div>
            </Group>
          </header>

        <SavedReviewerHistory
            reviewers={
                savedReviewers
            }
            isLoading={
                isLoadingHistory
            }
            error={
                historyError
            }
            selectedReviewerId={
                generatedReviewer?.id ??
                null
            }
            deletingReviewerId={
                deletingReviewerId
            }
            onOpen={
                handleOpenReviewer
            }
            onDelete={
                handleDeleteReviewer
            }
            />

          <ReviewerGenerationForm
            filterOptions={
              filterOptions
            }
            onGenerated={
              handleGenerated
            }
          />

          {generatedReviewer && (
            <section
              className={
                classes.resultRegion
              }
              aria-label="Generated reviewer"
              aria-live="polite"
            >
              <ReviewerResult
                reviewer={
                    generatedReviewer
                }
                onRegenerate={
                    handleRegenerate
                }
                isRegenerating={
                    isRegenerating
                }
                regenerationError={
                    regenerationError
                }
                />
            </section>
          )}
        </Stack>
      </Container>
    </main>
  );
}