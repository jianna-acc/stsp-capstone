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

  function handleGenerated(
    reviewer: ReviewerResponse,
  ): void {
    setGeneratedReviewer(
      reviewer,
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