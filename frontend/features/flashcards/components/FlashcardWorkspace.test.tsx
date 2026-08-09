// File: /frontend/features/flashcards/components/FlashcardWorkspace.test.tsx
// Purpose: Tests the Flashcard workspace connection between
// generation controls and the newly generated study viewer.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  FlashcardDeckResponse,
  FlashcardFilterOptions,
} from "@/features/flashcards/types";

const GENERATED_DECK:
  FlashcardDeckResponse = {
    id: "deck-1",

    subject_id:
      "subject-1",

    study_file_id: null,

    scope_type:
      "subject",

    title:
      "Biology Flashcards",

    requested_card_count: 1,

    cards: [
      {
        question:
          "What is a cell?",

        answer:
          "The basic unit of life.",
      },
    ],

    sources: [],

    generation_model:
      "gemini-test-model",

    generation_count: 1,

    generated_at:
      "2026-08-10T00:00:00Z",

    created_at:
      "2026-08-10T00:00:00Z",

    updated_at:
      "2026-08-10T00:00:00Z",
  };

const FILTER_OPTIONS:
  FlashcardFilterOptions = {
    subjects: [
      {
        id: "subject-1",
        name: "Biology",
      },
    ],

    studyFiles: [],

    loadError: null,
  };

vi.mock(
  "./FlashcardGenerationForm",
  () => ({
    FlashcardGenerationForm: ({
      onGenerated,
    }: {
      onGenerated: (
        deck:
          FlashcardDeckResponse,
      ) => void;
    }) => (
      <button
        type="button"
        onClick={() => {
          onGenerated(
            GENERATED_DECK,
          );
        }}
      >
        Generate test deck
      </button>
    ),
  }),
);

vi.mock(
  "./FlashcardStudyViewer",
  () => ({
    FlashcardStudyViewer: ({
      deck,
    }: {
      deck:
        FlashcardDeckResponse;
    }) => (
      <div>
        Study viewer:
        {" "}
        {deck.title}
      </div>
    ),
  }),
);

import {
  FlashcardWorkspace,
} from "./FlashcardWorkspace";

function renderWorkspace() {
  return render(
    <MantineProvider>
      <FlashcardWorkspace
        filterOptions={
          FILTER_OPTIONS
        }
      />
    </MantineProvider>,
  );
}

describe(
  "FlashcardWorkspace",
  () => {
    it(
      "shows the Flashcards workspace before generation",
      () => {
        renderWorkspace();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Flashcards",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Generate test deck",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            /Study viewer:/,
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "shows the generated deck after generation completes",
      async () => {
        const user =
          userEvent.setup();

        renderWorkspace();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Generate test deck",
            },
          ),
        );

        expect(
          screen.getByText(
            "Study viewer: Biology Flashcards",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);