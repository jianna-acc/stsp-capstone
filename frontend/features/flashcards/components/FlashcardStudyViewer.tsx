// File: /frontend/features/flashcards/components/FlashcardStudyViewer.tsx
// Purpose: Displays generated Flashcards with question/answer
// flipping and previous/next study navigation.

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

import type {
  FlashcardDeckResponse,
} from "@/features/flashcards/types";

import classes from "./FlashcardStudyViewer.module.css";

interface FlashcardStudyViewerProps {
  deck:
    FlashcardDeckResponse;
}

export function FlashcardStudyViewer({
  deck,
}: Readonly<FlashcardStudyViewerProps>) {
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
}: Readonly<FlashcardStudyViewerProps>) {
  const [
    currentIndex,
    setCurrentIndex,
  ] = useState(0);

  const [
    showingAnswer,
    setShowingAnswer,
  ] = useState(false);

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

  function showPreviousCard():
    void {
    if (
      isFirstCard
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
  }

  function showNextCard():
    void {
    if (
      isLastCard
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
  }

  function toggleCardSide():
    void {
    setShowingAnswer(
      (
        current,
      ) => !current,
    );
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
          gap="md"
        >
          <div>
            <Title
              order={2}
              size="h3"
              id="flashcard-deck-title"
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
              continue to the next card.
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
            classes.flashcard
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
              isFirstCard
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
              isLastCard
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