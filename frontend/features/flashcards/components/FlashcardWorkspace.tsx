// File: /frontend/features/flashcards/components/FlashcardWorkspace.tsx
// Purpose: Connects Flashcard generation controls to the
// newly generated interactive study viewer.

"use client";

import {
  Badge,
  Group,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconCards,
} from "@tabler/icons-react";
import {
  useState,
} from "react";

import type {
  FlashcardDeckResponse,
  FlashcardFilterOptions,
} from "@/features/flashcards/types";

import {
  FlashcardGenerationForm,
} from "./FlashcardGenerationForm";
import {
  FlashcardStudyViewer,
} from "./FlashcardStudyViewer";

import classes from "./FlashcardWorkspace.module.css";

interface FlashcardWorkspaceProps {
  filterOptions:
    FlashcardFilterOptions;
}

export function FlashcardWorkspace({
  filterOptions,
}: Readonly<FlashcardWorkspaceProps>) {
  const [
    generatedDeck,
    setGeneratedDeck,
  ] = useState<
    FlashcardDeckResponse | null
  >(
    null,
  );

  function handleGenerated(
    deck:
      FlashcardDeckResponse,
  ): void {
    setGeneratedDeck(
      deck,
    );
  }

  return (
    <Stack
      gap="xl"
      className={
        classes.workspace
      }
    >
      <Group
        justify="space-between"
        align="flex-start"
        gap="md"
      >
        <Group
          align="flex-start"
          wrap="nowrap"
          gap="sm"
        >
          <ThemeIcon
            size={48}
            radius="md"
            variant="light"
            color="violet"
          >
            <IconCards
              size={26}
              stroke={1.8}
            />
          </ThemeIcon>

          <div>
            <Title
              order={1}
              size="h2"
            >
              Flashcards
            </Title>

            <Text
              c="dimmed"
              mt={4}
            >
              Generate study cards from
              your uploaded materials,
              then review them one at a
              time.
            </Text>
          </div>
        </Group>

        {generatedDeck && (
          <Badge
            variant="light"
            color="violet"
            size="lg"
          >
            {
              generatedDeck.cards
                .length
            }{" "}
            cards
          </Badge>
        )}
      </Group>

      <FlashcardGenerationForm
        filterOptions={
          filterOptions
        }
        onGenerated={
          handleGenerated
        }
      />

      {generatedDeck && (
        <FlashcardStudyViewer
          deck={
            generatedDeck
          }
        />
      )}
    </Stack>
  );
}