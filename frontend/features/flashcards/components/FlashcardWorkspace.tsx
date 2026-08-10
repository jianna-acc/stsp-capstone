// File: /frontend/features/flashcards/components/FlashcardWorkspace.tsx
// Purpose: Connects Flashcard generation, saved-deck access,
// and the interactive study viewer.

"use client";

import {
  Alert,
  Badge,
  Group,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCards,
} from "@tabler/icons-react";
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  deleteFlashcardDeck,
  getFlashcardDeck,
  listFlashcardDecks,
} from "@/features/flashcards/api";
import type {
  FlashcardDeckResponse,
  FlashcardDeckSummary,
  FlashcardFilterOptions,
} from "@/features/flashcards/types";

import {
  FlashcardGenerationForm,
} from "./FlashcardGenerationForm";
import {
  FlashcardStudyViewer,
} from "./FlashcardStudyViewer";
import {
  SavedFlashcardList,
} from "./SavedFlashcardList";

import classes from "./FlashcardWorkspace.module.css";


interface FlashcardWorkspaceProps {
  filterOptions:
    FlashcardFilterOptions;
}


const SAVED_DECK_LOAD_ERROR =
  "Saved Flashcards could not be loaded.";

const SAVED_DECK_OPEN_ERROR =
  "The saved Flashcard deck could not be opened.";

const SAVED_DECK_DELETE_ERROR =
  "Saved Flashcard deck could not be deleted.";


export function FlashcardWorkspace({
  filterOptions,
}: Readonly<
  FlashcardWorkspaceProps
>) {
  const [
    activeDeck,
    setActiveDeck,
  ] = useState<
    FlashcardDeckResponse | null
  >(
    null,
  );

  const [
    savedDecks,
    setSavedDecks,
  ] = useState<
    FlashcardDeckSummary[]
  >(
    [],
  );

  const [
    savedDeckLoadError,
    setSavedDeckLoadError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    savedDeckOpenError,
    setSavedDeckOpenError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    savedDeckDeleteError,
    setSavedDeckDeleteError,
  ] = useState<
    string | null
  >(
    null,
  );

  const loadSavedDecks =
    useCallback(
      async (
        signal?: AbortSignal,
      ): Promise<void> => {
        try {
          const response =
            await listFlashcardDecks(
              undefined,
              {
                signal,
              },
            );

          setSavedDecks(
            response.items,
          );

          setSavedDeckLoadError(
            null,
          );
        } catch (error) {
          if (
            error
              instanceof DOMException
            && error.name
              === "AbortError"
          ) {
            return;
          }

          setSavedDecks(
            [],
          );

          setSavedDeckLoadError(
            SAVED_DECK_LOAD_ERROR,
          );
        }
      },
      [],
    );

  useEffect(
    () => {
      const controller =
        new AbortController();

      listFlashcardDecks(
        undefined,
        {
          signal:
            controller.signal,
        },
      )
        .then(
          (
            response,
          ) => {
            setSavedDecks(
              response.items,
            );

            setSavedDeckLoadError(
              null,
            );
          },
        )
        .catch(
          (
            error: unknown,
          ) => {
            if (
              error
                instanceof DOMException
              && error.name
                === "AbortError"
            ) {
              return;
            }

            setSavedDecks(
              [],
            );

            setSavedDeckLoadError(
              SAVED_DECK_LOAD_ERROR,
            );
          },
        );

      return () => {
        controller.abort();
      };
    },
    [],
  );

  function handleGenerated(
    deck:
      FlashcardDeckResponse,
  ): void {
    setActiveDeck(
      deck,
    );

    setSavedDeckOpenError(
      null,
    );

    void loadSavedDecks();
  }

  async function handleOpenDeck(
    deckId: string,
  ): Promise<void> {
    setSavedDeckOpenError(
      null,
    );

    try {
      const deck =
        await getFlashcardDeck(
          deckId,
        );

      setActiveDeck(
        deck,
      );
    } catch {
      setSavedDeckOpenError(
        SAVED_DECK_OPEN_ERROR,
      );
    }
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
      >
        <Group
          gap="sm"
          align="flex-start"
          wrap="nowrap"
        >
          <ThemeIcon
            size="lg"
            radius="md"
            variant="light"
            color="violet"
          >
            <IconCards
              size={20}
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
              Generate study cards
              from your uploaded
              materials, then review
              them one at a time.
            </Text>
          </div>
        </Group>

        {activeDeck && (
          <Badge
            variant="light"
            color="violet"
            size="lg"
          >
            {
              activeDeck
                .cards
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

      {savedDeckOpenError && (
        <Alert
          icon={
            <IconAlertCircle
              size={18}
            />
          }
          color="red"
          variant="light"
        >
          {
            savedDeckOpenError
          }
        </Alert>
      )}

      {activeDeck && (
        <FlashcardStudyViewer
          deck={
            activeDeck
          }
        />
      )}

      {savedDeckDeleteError && (
        <Alert
          icon={
            <IconAlertCircle
              size={18}
            />
          }
          color="red"
          variant="light"
        >
          {
            savedDeckDeleteError
          }
        </Alert>
      )}

      <SavedFlashcardList
        decks={
          savedDecks
        }
        loadError={
          savedDeckLoadError
        }
        onOpenDeck={(
          deckId,
        ) => {
          void handleOpenDeck(
            deckId,
          );
        }}
        onDeleteDeck={(
          deckId,
        ) => {
          void handleDeleteDeck(
            deckId,
          );
        }}
      />
    </Stack>
  );

  async function handleDeleteDeck(
    deckId: string,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        "Delete this saved Flashcard deck?",
      );

    if (!confirmed) {
      return;
    }

    setSavedDeckDeleteError(
      null,
    );

    try {
      await deleteFlashcardDeck(
        deckId,
      );

      setActiveDeck(
        (
          currentDeck,
        ) => (
          currentDeck?.id
            === deckId
            ? null
            : currentDeck
        ),
      );

      await loadSavedDecks();
    } catch {
      setSavedDeckDeleteError(
        SAVED_DECK_DELETE_ERROR,
      );
    }
  }
}