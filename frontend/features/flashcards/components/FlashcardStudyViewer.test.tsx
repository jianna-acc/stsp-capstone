// File: /frontend/features/flashcards/components/FlashcardStudyViewer.test.tsx
// Purpose: Tests Flashcard flipping, navigation, and durable
// student self-assessment review behavior.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type {
  ComponentProps,
} from "react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks = vi.hoisted(
  () => ({
    recordFlashcardReview:
      vi.fn(),
  }),
);

vi.mock(
  "@/features/flashcards/api",
  async (
    importOriginal,
  ) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/features/flashcards/api"
        )
      >();

    return {
      ...actual,

      recordFlashcardReview:
        mocks.recordFlashcardReview,
    };
  },
);

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

function createReviewResponse(
  cardPosition: number,
  outcome:
    | "known"
    | "review_again",
) {
  return {
    id:
      `review-${cardPosition}`,

    deck_id:
      DECK.id,

    card_position:
      cardPosition,

    outcome,

    reviewed_at:
      "2026-08-11T08:00:00Z",
  };
}

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
    beforeEach(() => {
      vi.clearAllMocks();

      mocks.recordFlashcardReview
        .mockImplementation(
          (
            _deckId: string,
            request: {
              card_position: number;
              outcome:
                | "known"
                | "review_again";
            },
          ) => Promise.resolve(
            createReviewResponse(
              request.card_position,
              request.outcome,
            ),
          ),
        );
    });

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

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Review Again",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "I Know This",
            },
          ),
        ).not.toBeInTheDocument();
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

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Review Again",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "I Know This",
            },
          ),
        ).toBeInTheDocument();

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

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "I Know This",
            },
          ),
        ).not.toBeInTheDocument();
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
      "records known evidence and advances to the next card",
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
                "I Know This",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              mocks.recordFlashcardReview,
            ).toHaveBeenCalledWith(
              "deck-1",
              {
                card_position: 0,
                outcome: "known",
              },
            );
          },
        );

        await waitFor(
          () => {
            expect(
              screen.getByText(
                "Card 2 of 3",
              ),
            ).toBeInTheDocument();
          },
        );

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
      },
    );

    it(
      "records review-again evidence and advances to the next card",
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
                "Review Again",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              mocks.recordFlashcardReview,
            ).toHaveBeenCalledWith(
              "deck-1",
              {
                card_position: 0,
                outcome:
                  "review_again",
              },
            );
          },
        );

        await waitFor(
          () => {
            expect(
              screen.getByText(
                "Card 2 of 3",
              ),
            ).toBeInTheDocument();
          },
        );
      },
    );

    it(
      "keeps the final card visible after saving its review",
      async () => {
        const user =
          userEvent.setup();

        renderViewer();

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
                "Next card",
            },
          ),
        );

        expect(
          screen.getByText(
            "Card 3 of 3",
          ),
        ).toBeInTheDocument();

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
                "I Know This",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              mocks.recordFlashcardReview,
            ).toHaveBeenCalledWith(
              "deck-1",
              {
                card_position: 2,
                outcome: "known",
              },
            );
          },
        );

        expect(
          screen.getByText(
            "Card 3 of 3",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Review saved.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "I Know This",
            },
          ),
        ).toBeDisabled();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Review Again",
            },
          ),
        ).toBeDisabled();
      },
    );

    it(
      "shows a safe message when saving a review fails",
      async () => {
        const user =
          userEvent.setup();

        mocks.recordFlashcardReview
          .mockRejectedValueOnce(
            new Error(
              "Database details must not be shown.",
            ),
          );

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
                "I Know This",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Your Flashcard review could not be saved.",
        );

        expect(
          screen.getByText(
            "Card 1 of 3",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "The cell.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Database details must not be shown.",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "does not save a review until the answer has been revealed",
      () => {
        renderViewer();

        expect(
          mocks.recordFlashcardReview,
        ).not.toHaveBeenCalled();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "I Know This",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Review Again",
            },
          ),
        ).not.toBeInTheDocument();
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

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "I Know This",
            },
          ),
        ).not.toBeInTheDocument();
      },
    );
  },
);