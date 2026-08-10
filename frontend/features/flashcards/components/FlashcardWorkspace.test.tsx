// File: /frontend/features/flashcards/components/FlashcardWorkspace.test.tsx
// Purpose: Tests Flashcard generation, saved-deck loading,
// reopening, refresh behavior, and safe saved-list errors.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  FlashcardDeckResponse,
  FlashcardDeckSummary,
  FlashcardFilterOptions,
} from "@/features/flashcards/types";


const apiMocks = vi.hoisted(
  () => ({
    listFlashcardDecks:
      vi.fn(),

    getFlashcardDeck:
      vi.fn(),

    deleteFlashcardDeck:
      vi.fn(),
  }),
);


vi.mock(
  "@/features/flashcards/api",
  () => ({
    listFlashcardDecks:
      apiMocks.listFlashcardDecks,

    getFlashcardDeck:
      apiMocks.getFlashcardDeck,

    deleteFlashcardDeck:
      apiMocks.deleteFlashcardDeck,
  }),
);


const GENERATED_DECK:
FlashcardDeckResponse = {
  id: "deck-generated",

  subject_id:
    "subject-1",

  study_file_id: null,

  scope_type:
    "subject",

  title:
    "Generated Biology Flashcards",

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


const SAVED_DECK:
FlashcardDeckResponse = {
  ...GENERATED_DECK,

  id:
    "deck-saved",

  title:
    "Saved Cell Biology Deck",

  generated_at:
    "2026-08-09T00:00:00Z",

  created_at:
    "2026-08-09T00:00:00Z",

  updated_at:
    "2026-08-09T00:00:00Z",
};


const SAVED_SUMMARY:
FlashcardDeckSummary = {
  id:
    SAVED_DECK.id,

  subject_id:
    SAVED_DECK.subject_id,

  study_file_id:
    SAVED_DECK.study_file_id,

  scope_type:
    SAVED_DECK.scope_type,

  title:
    SAVED_DECK.title,

  requested_card_count:
    SAVED_DECK
      .requested_card_count,

  generation_model:
    SAVED_DECK
      .generation_model,

  generation_count:
    SAVED_DECK
      .generation_count,

  generated_at:
    SAVED_DECK.generated_at,

  created_at:
    SAVED_DECK.created_at,

  updated_at:
    SAVED_DECK.updated_at,
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
        Study viewer:{" "}
        {deck.title}
      </div>
    ),
  }),
);


vi.mock(
  "./SavedFlashcardList",
  () => ({
    SavedFlashcardList: ({
      decks,
      loadError,
      onOpenDeck,
      onDeleteDeck,
    }: {
      decks:
        FlashcardDeckSummary[];

      loadError:
        string | null;

      onOpenDeck: (
        deckId: string,
      ) => void;

      onDeleteDeck: (
        deckId: string,
      ) => void;
    }) => (
      <div>
        <div>
          Saved count:{" "}
          {decks.length}
        </div>

        {loadError ? (
          <div>
            Saved error:{" "}
            {loadError}
          </div>
        ) : null}

        {decks.map(
          (
            deck,
          ) => (
            <div
              key={
                deck.id
              }
            >
              <button
                type="button"
                onClick={() => {
                  onOpenDeck(
                    deck.id,
                  );
                }}
              >
                Open saved{" "}
                {deck.title}
              </button>

              <button
                type="button"
                onClick={() => {
                  onDeleteDeck(
                    deck.id,
                  );
                }}
              >
                Delete saved{" "}
                {deck.title}
              </button>
            </div>
          ),
        )}
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
    beforeEach(
      () => {
        vi.clearAllMocks();

        apiMocks
          .listFlashcardDecks
          .mockResolvedValue({
            items: [
              SAVED_SUMMARY,
            ],
          });

        apiMocks
          .getFlashcardDeck
          .mockResolvedValue(
            SAVED_DECK,
          );

        apiMocks
          .deleteFlashcardDeck
          .mockResolvedValue(
            undefined,
          );
      },
    );

    it(
      "loads saved Flashcard decks when the workspace opens",
      async () => {
        renderWorkspace();

        await waitFor(
          () => {
            expect(
              apiMocks
                .listFlashcardDecks,
            ).toHaveBeenCalledTimes(
              1,
            );
          },
        );

        expect(
          await screen.findByText(
            "Saved count: 1",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "opens a selected saved deck in the study viewer",
      async () => {
        const user =
          userEvent.setup();

        renderWorkspace();

        const openButton =
          await screen.findByRole(
            "button",
            {
              name:
                "Open saved Saved Cell Biology Deck",
            },
          );

        await user.click(
          openButton,
        );

        await waitFor(
          () => {
            expect(
              apiMocks
                .getFlashcardDeck,
            ).toHaveBeenCalledWith(
              "deck-saved",
            );
          },
        );

        expect(
          await screen.findByText(
            "Study viewer: Saved Cell Biology Deck",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "refreshes saved decks after generation completes",
      async () => {
        const user =
          userEvent.setup();

        renderWorkspace();

        await waitFor(
          () => {
            expect(
              apiMocks
                .listFlashcardDecks,
            ).toHaveBeenCalledTimes(
              1,
            );
          },
        );

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
            "Study viewer: Generated Biology Flashcards",
          ),
        ).toBeInTheDocument();

        await waitFor(
          () => {
            expect(
              apiMocks
                .listFlashcardDecks,
            ).toHaveBeenCalledTimes(
              2,
            );
          },
        );
      },
    );

    it(
      "shows a safe error when saved decks cannot load",
      async () => {
        apiMocks
          .listFlashcardDecks
          .mockRejectedValueOnce(
            new Error(
              "database details",
            ),
          );

        renderWorkspace();

        expect(
          await screen.findByText(
            "Saved error: Saved Flashcards could not be loaded.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "database details",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "still shows a newly generated deck",
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
            "Study viewer: Generated Biology Flashcards",
          ),
        ).toBeInTheDocument();
      },
    );
it(
  "deletes an open saved deck and refreshes the saved list",
  async () => {
    const user =
      userEvent.setup();

    vi.spyOn(
      window,
      "confirm",
    ).mockReturnValue(
      true,
    );

    renderWorkspace();

    await user.click(
      await screen.findByRole(
        "button",
        {
          name:
            "Open saved Saved Cell Biology Deck",
        },
      ),
    );

    expect(
      await screen.findByText(
        "Study viewer: Saved Cell Biology Deck",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole(
        "button",
        {
          name:
            "Delete saved Saved Cell Biology Deck",
        },
      ),
    );

    await waitFor(
      () => {
        expect(
          apiMocks
            .deleteFlashcardDeck,
        ).toHaveBeenCalledWith(
          "deck-saved",
        );
      },
    );

    await waitFor(
      () => {
        expect(
          apiMocks
            .listFlashcardDecks,
        ).toHaveBeenCalledTimes(
          2,
        );
      },
    );

    expect(
      screen.queryByText(
        "Study viewer: Saved Cell Biology Deck",
      ),
    ).not.toBeInTheDocument();
  },
);


it(
  "does not delete a saved deck when confirmation is cancelled",
  async () => {
    const user =
      userEvent.setup();

    vi.spyOn(
      window,
      "confirm",
    ).mockReturnValue(
      false,
    );

    renderWorkspace();

    await user.click(
      await screen.findByRole(
        "button",
        {
          name:
            "Delete saved Saved Cell Biology Deck",
        },
      ),
    );

    expect(
      apiMocks
        .deleteFlashcardDeck,
    ).not.toHaveBeenCalled();
  },
);


it(
  "shows a safe error when a saved deck cannot be deleted",
  async () => {
    const user =
      userEvent.setup();

    vi.spyOn(
      window,
      "confirm",
    ).mockReturnValue(
      true,
    );

    apiMocks
      .deleteFlashcardDeck
      .mockRejectedValueOnce(
        new Error(
          "database delete details",
        ),
      );

    renderWorkspace();

    await user.click(
      await screen.findByRole(
        "button",
        {
          name:
            "Delete saved Saved Cell Biology Deck",
        },
      ),
    );

    expect(
      await screen.findByText(
        "Saved Flashcard deck could not be deleted.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "database delete details",
      ),
    ).not.toBeInTheDocument();
  },
);
  },
);