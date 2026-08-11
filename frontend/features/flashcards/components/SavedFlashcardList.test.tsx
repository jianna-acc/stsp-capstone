// File: /frontend/features/flashcards/components/SavedFlashcardList.test.tsx
// Purpose: Tests saved Flashcard deck listing, empty/error states,
// metadata display, and deck selection.

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

import {
  SavedFlashcardList,
} from "./SavedFlashcardList";


const SAVED_DECKS = [
  {
    id: "deck-1",
    subject_id: "subject-1",
    study_file_id: null,
    scope_type: "subject" as const,
    title: "Biology Flashcards",
    requested_card_count: 20,
    generation_model: "gemini-test-model",
    generation_count: 1,
    generated_at:
      "2026-08-10T06:00:00Z",
    created_at:
      "2026-08-10T06:00:00Z",
    updated_at:
      "2026-08-10T06:00:00Z",
  },
  {
    id: "deck-2",
    subject_id: "subject-1",
    study_file_id: "file-1",
    scope_type: "file" as const,
    title: "Cell Division Review",
    requested_card_count: 10,
    generation_model: "gemini-test-model",
    generation_count: 1,
    generated_at:
      "2026-08-09T06:00:00Z",
    created_at:
      "2026-08-09T06:00:00Z",
    updated_at:
      "2026-08-09T06:00:00Z",
  },
];


function renderList(
  props?: Partial<
    React.ComponentProps<
      typeof SavedFlashcardList
    >
  >,
) {
  return render(
    <MantineProvider>
      <SavedFlashcardList
        decks={SAVED_DECKS}
        loadError={null}
        onOpenDeck={vi.fn()}
        onDeleteDeck={vi.fn()}
        {...props}
      />
    </MantineProvider>,
  );
}


describe(
  "SavedFlashcardList",
  () => {
    it(
      "shows saved Flashcard decks",
      () => {
        renderList();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Saved Flashcards",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Biology Flashcards",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Cell Division Review",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows deck card counts and scopes",
      () => {
        renderList();

        expect(
          screen.getByText(
            "20 cards",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "10 cards",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Whole subject",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Study material",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "opens the selected saved deck",
      async () => {
        const user =
          userEvent.setup();

        const onOpenDeck =
          vi.fn();

        renderList({
          onOpenDeck,
        });

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Open Biology Flashcards",
            },
          ),
        );

        expect(
          onOpenDeck,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          onOpenDeck,
        ).toHaveBeenCalledWith(
          "deck-1",
        );
      },
    );

    it(
      "shows an empty state when there are no saved decks",
      () => {
        renderList({
          decks: [],
        });

        expect(
          screen.getByText(
            "No saved Flashcards yet.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /generate a deck/i,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows a safe error when saved decks cannot load",
      () => {
        renderList({
          decks: [],
          loadError:
            "Saved Flashcards could not be loaded.",
        });

        expect(
          screen.getByText(
            "Saved Flashcards could not be loaded.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "No saved Flashcards yet.",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
  "requests deletion of the selected saved deck",
  async () => {
    const user =
      userEvent.setup();

    const onDeleteDeck =
      vi.fn();

    renderList({
      onDeleteDeck,
    });

    await user.click(
      screen.getByRole(
        "button",
        {
          name:
            "Delete Biology Flashcards",
        },
      ),
    );

    expect(
      onDeleteDeck,
    ).toHaveBeenCalledTimes(
      1,
    );

    expect(
      onDeleteDeck,
    ).toHaveBeenCalledWith(
      "deck-1",
    );
  },
);

  },
);