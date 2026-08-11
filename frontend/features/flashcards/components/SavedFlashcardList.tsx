// File: /frontend/features/flashcards/components/SavedFlashcardList.tsx
// Purpose: Displays saved Flashcard decks and lets students reopen
// or delete previously generated decks.

"use client";

import {
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCards,
  IconChevronRight,
  IconTrash,
} from "@tabler/icons-react";

import type {
  FlashcardDeckSummary,
} from "../types";

import classes from "./SavedFlashcardList.module.css";


type SavedFlashcardListProps = {
  decks: FlashcardDeckSummary[];
  loadError: string | null;

  onOpenDeck: (
    deckId: string,
  ) => void;

  onDeleteDeck: (
    deckId: string,
  ) => void;
};


function scopeLabel(
  scopeType:
    FlashcardDeckSummary[
      "scope_type"
    ],
): string {
  if (
    scopeType
    === "file"
  ) {
    return "Study material";
  }

  return "Whole subject";
}


function formatGeneratedDate(
  value: string,
): string {
  const date = new Date(
    value,
  );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Saved";
  }

  return new Intl.DateTimeFormat(
    "en",
    {
      dateStyle: "medium",
    },
  ).format(
    date,
  );
}


export function SavedFlashcardList({
  decks,
  loadError,
  onOpenDeck,
  onDeleteDeck,
}: SavedFlashcardListProps) {
  return (
    <Paper
      component="section"
      aria-labelledby="saved-flashcards-title"
      withBorder
      radius="lg"
      p="lg"
      className={
        classes.container
      }
    >
      <Stack gap="lg">
        <Group
          gap="sm"
          align="flex-start"
          wrap="nowrap"
        >
          <IconCards
            aria-hidden="true"
            size={24}
          />

          <div>
            <Title
              id="saved-flashcards-title"
              order={2}
              size="h3"
            >
              Saved Flashcards
            </Title>

            <Text
              c="dimmed"
              size="sm"
              mt={4}
            >
              Reopen a previous deck
              and continue studying.
            </Text>
          </div>
        </Group>

        {loadError ? (
          <Alert
            icon={
              <IconAlertCircle
                size={18}
              />
            }
            color="red"
            variant="light"
          >
            {loadError}
          </Alert>
        ) : null}

        {!loadError
        && decks.length === 0 ? (
          <div
            className={
              classes.emptyState
            }
          >
            <Text fw={600}>
              No saved Flashcards yet.
            </Text>

            <Text
              c="dimmed"
              size="sm"
            >
              Generate a deck and it
              will appear here for
              future access.
            </Text>
          </div>
        ) : null}

        {!loadError
        && decks.length > 0 ? (
          <Stack gap="sm">
            {decks.map(
              (
                deck,
              ) => (
                <Paper
                  key={deck.id}
                  withBorder
                  radius="md"
                  p="md"
                  className={
                    classes.deck
                  }
                >
                  <Group
                    justify="space-between"
                    align="center"
                    wrap="nowrap"
                  >
                    <Stack
                      gap={6}
                      className={
                        classes.deckDetails
                      }
                    >
                      <Text
                        fw={600}
                        className={
                          classes.title
                        }
                      >
                        {deck.title}
                      </Text>

                      <Group
                        gap="xs"
                        wrap="wrap"
                      >
                        <Badge
                          variant="light"
                        >
                          {
                            deck
                              .requested_card_count
                          }{" "}
                          cards
                        </Badge>

                        <Badge
                          variant="outline"
                        >
                          {scopeLabel(
                            deck.scope_type,
                          )}
                        </Badge>
                      </Group>

                      <Text
                        size="xs"
                        c="dimmed"
                      >
                        Generated{" "}
                        {formatGeneratedDate(
                          deck.generated_at,
                        )}
                      </Text>
                    </Stack>

                    <Group
                      gap="xs"
                      wrap="nowrap"
                    >
                      <Button
                        type="button"
                        variant="subtle"
                        color="red"
                        leftSection={
                          <IconTrash
                            size={16}
                          />
                        }
                        aria-label={
                          `Delete ${deck.title}`
                        }
                        onClick={() => {
                          onDeleteDeck(
                            deck.id,
                          );
                        }}
                      >
                        Delete
                      </Button>

                      <Button
                        type="button"
                        variant="subtle"
                        rightSection={
                          <IconChevronRight
                            size={16}
                          />
                        }
                        aria-label={
                          `Open ${deck.title}`
                        }
                        onClick={() => {
                          onOpenDeck(
                            deck.id,
                          );
                        }}
                      >
                        Open
                      </Button>
                    </Group>
                  </Group>
                </Paper>
              ),
            )}
          </Stack>
        ) : null}
      </Stack>
    </Paper>
  );
}