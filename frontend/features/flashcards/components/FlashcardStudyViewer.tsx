// File: /frontend/features/flashcards/components/FlashcardStudyViewer.tsx
// Purpose: Displays Flashcards with question/answer flipping,
// navigation, and durable student self-assessment reviews.

"use client";

import {
  Badge,
  Button,
  Group,
  Paper,
  Progress,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconArrowLeft,
  IconArrowRight,
  IconRefresh,
} from "@tabler/icons-react";
import {
  useMemo,
  useState,
} from "react";

import {
  FlashcardApiError,
  recordFlashcardReview,
} from "@/features/flashcards/api";
import type {
  FlashcardDeckResponse,
  FlashcardReviewOutcome,
} from "@/features/flashcards/types";

import classes from "./FlashcardStudyViewer.module.css";


interface FlashcardStudyViewerProps {
  deck:
    FlashcardDeckResponse;
}


export function FlashcardStudyViewer({
  deck,
}: Readonly<
  FlashcardStudyViewerProps
>) {
  return (
    <FlashcardStudyViewerContent
      key={
        deck.id
      }
      deck={
        deck
      }
    />
  );
}


function FlashcardStudyViewerContent({
  deck,
}: Readonly<
  FlashcardStudyViewerProps
>) {
  const [
    currentIndex,
    setCurrentIndex,
  ] = useState(
    0,
  );

  const [
    showingAnswer,
    setShowingAnswer,
  ] = useState(
    false,
  );

  const [
    reviewSubmitting,
    setReviewSubmitting,
  ] = useState(
    false,
  );

  const [
    reviewError,
    setReviewError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    reviewedPositions,
    setReviewedPositions,
  ] = useState<
    Set<number>
  >(
    new Set<number>(),
  );

  const totalCards =
    deck.cards.length;

  const currentCard =
    deck.cards[
      currentIndex
    ];

  const progressValue =
    useMemo(
      () => {
        if (
          totalCards === 0
        ) {
          return 0;
        }

        return (
          (
            currentIndex +
            1
          ) /
          totalCards
        ) * 100;
      },
      [
        currentIndex,
        totalCards,
      ],
    );

  const isFirstCard =
    currentIndex === 0;

  const isLastCard =
    currentIndex ===
    totalCards - 1;

  const currentCardReviewed =
    reviewedPositions.has(
      currentIndex,
    );

  function showPreviousCard():
    void {
    if (
      isFirstCard ||
      reviewSubmitting
    ) {
      return;
    }

    setCurrentIndex(
      (
        index,
      ) => index - 1,
    );

    setShowingAnswer(
      false,
    );

    setReviewError(
      null,
    );
  }

  function showNextCard():
    void {
    if (
      isLastCard ||
      reviewSubmitting
    ) {
      return;
    }

    setCurrentIndex(
      (
        index,
      ) => index + 1,
    );

    setShowingAnswer(
      false,
    );

    setReviewError(
      null,
    );
  }

  function toggleCardSide():
    void {
    setShowingAnswer(
      (
        current,
      ) => !current,
    );
  }

  async function submitReview(
    outcome: FlashcardReviewOutcome,
  ): Promise<void> {
    if (
      reviewSubmitting ||
      currentCardReviewed ||
      !showingAnswer
    ) {
      return;
    }

    setReviewSubmitting(
      true,
    );

    setReviewError(
      null,
    );

    try {
      await recordFlashcardReview(
        deck.id,
        {
          card_position:
            currentIndex,
          outcome,
        },
      );

      setReviewedPositions(
        (
          current,
        ) => {
          const updated =
            new Set(
              current,
            );

          updated.add(
            currentIndex,
          );

          return updated;
        },
      );

      if (!isLastCard) {
        setCurrentIndex(
          (
            index,
          ) => index + 1,
        );

        setShowingAnswer(
          false,
        );
      }
    } catch (error) {
      setReviewError(
        error instanceof
          FlashcardApiError
          ? error.message
          : (
              "Your Flashcard review "
              + "could not be saved."
            ),
      );
    } finally {
      setReviewSubmitting(
        false,
      );
    }
  }

  if (
    !currentCard
  ) {
    return null;
  }

  return (
    <Paper
      component="section"
      withBorder
      radius="lg"
      p={{
        base: "md",
        sm: "xl",
      }}
      className={
        classes.viewer
      }
      aria-labelledby="flashcard-deck-title"
    >
      <Stack gap="lg">
        <Group
          justify="space-between"
          align="flex-start"
        >
          <div>
            <Title
              id="flashcard-deck-title"
              order={2}
              size="h3"
            >
              {deck.title}
            </Title>

            <Text
              size="sm"
              c="dimmed"
              mt={4}
            >
              Study each question,
              reveal the answer, then
              rate whether you know it
              or need to review it again.
            </Text>
          </div>

          <Badge
            variant="light"
            color="violet"
            size="lg"
          >
            Card{" "}
            {currentIndex + 1}{" "}
            of {totalCards}
          </Badge>
        </Group>

        <Progress
          value={
            progressValue
          }
          radius="xl"
          size="sm"
          aria-label="Flashcard study progress"
        />

        <button
          type="button"
          className={
            showingAnswer
              ? `${classes.flashcard} ${classes.answerCard}`
              : classes.flashcard
          }
          onClick={
            toggleCardSide
          }
          aria-label={
            showingAnswer
              ? "Show question"
              : "Show answer"
          }
        >
          <span
            className={
              classes.sideLabel
            }
          >
            {showingAnswer
              ? "Answer"
              : "Question"}
          </span>

          <span
            className={
              classes.cardContent
            }
          >
            {showingAnswer
              ? currentCard.answer
              : currentCard.question}
          </span>

          <span
            className={
              classes.flipHint
            }
          >
            <IconRefresh
              size={16}
              aria-hidden="true"
            />

            {showingAnswer
              ? "Show question"
              : "Show answer"}
          </span>
        </button>

        {showingAnswer && (
          <Stack gap="xs">
            <Group
              justify="center"
              gap="md"
            >
              <Button
                type="button"
                variant="default"
                disabled={
                  currentCardReviewed
                }
                loading={
                  reviewSubmitting
                }
                onClick={() => {
                  void submitReview(
                    "review_again",
                  );
                }}
              >
                Review Again
              </Button>

              <Button
                type="button"
                disabled={
                  currentCardReviewed
                }
                loading={
                  reviewSubmitting
                }
                onClick={() => {
                  void submitReview(
                    "known",
                  );
                }}
              >
                I Know This
              </Button>
            </Group>

            {currentCardReviewed && (
              <Text
                size="sm"
                c="dimmed"
                ta="center"
              >
                Review saved.
              </Text>
            )}

            {reviewError && (
              <Text
                size="sm"
                c="red"
                ta="center"
                role="alert"
              >
                {reviewError}
              </Text>
            )}
          </Stack>
        )}

        <Group
          justify="space-between"
          gap="md"
          wrap="nowrap"
        >
          <Button
            type="button"
            variant="default"
            leftSection={
              <IconArrowLeft
                size={18}
              />
            }
            disabled={
              isFirstCard ||
              reviewSubmitting
            }
            onClick={
              showPreviousCard
            }
            aria-label="Previous card"
          >
            Previous
          </Button>

          <Button
            type="button"
            rightSection={
              <IconArrowRight
                size={18}
              />
            }
            disabled={
              isLastCard ||
              reviewSubmitting
            }
            onClick={
              showNextCard
            }
            aria-label="Next card"
          >
            Next
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}