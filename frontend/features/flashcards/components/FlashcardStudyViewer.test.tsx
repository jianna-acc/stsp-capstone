// File: /frontend/features/flashcards/components/FlashcardStudyViewer.test.tsx
// Purpose: Tests Flashcard question/answer flipping and
// previous/next study navigation.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type {
  ComponentProps,
} from "react";
import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  FlashcardDeckResponse,
} from "@/features/flashcards/types";

import {
  FlashcardStudyViewer,
} from "./FlashcardStudyViewer";

const DECK:
  FlashcardDeckResponse = {
    id: "deck-1",

    subject_id:
      "subject-1",

    study_file_id: null,

    scope_type:
      "subject",

    title:
      "Biology Flashcards",

    requested_card_count: 3,

    cards: [
      {
        question:
          "What is the basic unit of life?",

        answer:
          "The cell.",
      },
      {
        question:
          "What organelle produces most cellular ATP?",

        answer:
          "The mitochondrion.",
      },
      {
        question:
          "What molecule carries genetic information?",

        answer:
          "DNA.",
      },
    ],

    sources: [
      {
        study_file_id:
          "file-1",

        source_name:
          "Biology Notes.pdf",

        chunk_index: 0,

        locator_type:
          "page",

        locator_label:
          "Page 1",
      },
    ],

    generation_model:
      "gemini-test-model",

    generation_count: 1,

    generated_at:
      "2026-08-09T15:00:00Z",

    created_at:
      "2026-08-09T15:00:00Z",

    updated_at:
      "2026-08-09T15:00:00Z",
  };

function renderViewer(
  props?: Partial<
    ComponentProps<
      typeof FlashcardStudyViewer
    >
  >,
) {
  return render(
    <MantineProvider>
      <FlashcardStudyViewer
        deck={DECK}
        {...props}
      />
    </MantineProvider>,
  );
}

describe(
  "FlashcardStudyViewer",
  () => {
    it(
      "starts on the first card showing only its question",
      () => {
        renderViewer();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Biology Flashcards",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Card 1 of 3",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "What is the basic unit of life?",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "The cell.",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Show answer",
            },
          ),
        ).toBeEnabled();
      },
    );

    it(
      "flips between the question and answer",
      async () => {
        const user =
          userEvent.setup();

        renderViewer();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Show answer",
            },
          ),
        );

        expect(
          screen.getByText(
            "The cell.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "What is the basic unit of life?",
          ),
        ).not.toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Show question",
            },
          ),
        );

        expect(
          screen.getByText(
            "What is the basic unit of life?",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "moves to the next card and resets to its question",
      async () => {
        const user =
          userEvent.setup();

        renderViewer();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Show answer",
            },
          ),
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Next card",
            },
          ),
        );

        expect(
          screen.getByText(
            "Card 2 of 3",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "What organelle produces most cellular ATP?",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "The mitochondrion.",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Show answer",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "supports previous navigation and disables boundary buttons",
      async () => {
        const user =
          userEvent.setup();

        renderViewer();

        const previousButton =
          screen.getByRole(
            "button",
            {
              name:
                "Previous card",
            },
          );

        expect(
          previousButton,
        ).toBeDisabled();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Next card",
            },
          ),
        );

        expect(
          previousButton,
        ).toBeEnabled();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Next card",
            },
          ),
        );

        expect(
          screen.getByText(
            "Card 3 of 3",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Next card",
            },
          ),
        ).toBeDisabled();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Previous card",
            },
          ),
        );

        expect(
          screen.getByText(
            "Card 2 of 3",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "resets to the first question when a different deck is loaded",
      async () => {
        const user =
          userEvent.setup();

        const {
          rerender,
        } = renderViewer();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Next card",
            },
          ),
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Show answer",
            },
          ),
        );

        const replacementDeck:
          FlashcardDeckResponse = {
            ...DECK,

            id:
              "deck-2",

            title:
              "Chemistry Flashcards",

            cards: [
              {
                question:
                  "What is an atom?",

                answer:
                  "The smallest unit of an element that retains its chemical properties.",
              },
            ],

            requested_card_count: 1,
          };

        rerender(
          <MantineProvider>
            <FlashcardStudyViewer
              deck={
                replacementDeck
              }
            />
          </MantineProvider>,
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Chemistry Flashcards",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Card 1 of 1",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "What is an atom?",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "The smallest unit of an element that retains its chemical properties.",
          ),
        ).not.toBeInTheDocument();
      },
    );
  },
);