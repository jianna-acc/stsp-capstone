// File: /frontend/features/flashcards/components/FlashcardGenerationForm.test.tsx
// Purpose: Tests Flashcard scope, subject/file selection,
// card count, generation, and safe error states.

import {
  MantineProvider,
} from "@mantine/core";
import {
  fireEvent,
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

import {
  FlashcardApiError,
} from "@/features/flashcards/api";
import type {
  FlashcardDeckResponse,
  FlashcardFilterOptions,
} from "@/features/flashcards/types";

const mocks = vi.hoisted(
  () => ({
    generateFlashcards:
      vi.fn(),
  }),
);

vi.mock(
  "@/features/flashcards/api",
  async () => {
    const actual =
      await vi.importActual<
        typeof import(
          "@/features/flashcards/api"
        )
      >(
        "@/features/flashcards/api",
      );

    return {
      ...actual,

      generateFlashcards:
        mocks.generateFlashcards,
    };
  },
);

import {
  FlashcardGenerationForm,
} from "./FlashcardGenerationForm";

const FILTER_OPTIONS:
  FlashcardFilterOptions = {
    subjects: [
      {
        id: "subject-1",
        name: "Biology",
      },
      {
        id: "subject-2",
        name: "Chemistry",
      },
    ],

    studyFiles: [
      {
        id: "file-1",
        subjectId:
          "subject-1",
        originalFilename:
          "Biology Notes.pdf",
      },
      {
        id: "file-2",
        subjectId:
          "subject-1",
        originalFilename:
          "Biology Slides.pptx",
      },
      {
        id: "file-3",
        subjectId:
          "subject-2",
        originalFilename:
          "Chemistry Notes.pdf",
      },
    ],

    loadError: null,
  };

const GENERATED_DECK:
  FlashcardDeckResponse = {
    id: "deck-1",

    subject_id:
      "subject-1",

    study_file_id: null,

    scope_type:
      "subject",

    title:
      "Study Flashcards",

    requested_card_count: 20,

    cards: [
      {
        question:
          "Question 1",

        answer:
          "Answer 1",
      },
      {
        question:
          "Question 2",

        answer:
          "Answer 2",
      },
      {
        question:
          "Question 3",

        answer:
          "Answer 3",
      },
      {
        question:
          "Question 4",

        answer:
          "Answer 4",
      },
      {
        question:
          "Question 5",

        answer:
          "Answer 5",
      },
    ],

    sources: [],

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

async function selectOption(
  user:
    ReturnType<
      typeof userEvent.setup
    >,
  label: string,
  option: string,
): Promise<void> {
  const combobox =
    screen.getByRole(
      "combobox",
      {
        name: label,
      },
    );

  await user.click(
    combobox,
  );

  const optionElement =
    screen.getByRole(
      "option",
      {
        name: option,
        hidden: true,
      },
    );

  fireEvent.click(
    optionElement,
  );

  await waitFor(
    () => {
      expect(
        combobox,
      ).toHaveValue(
        option,
      );
    },
  );
}

function renderForm(
  props: ComponentProps<
    typeof FlashcardGenerationForm
  >,
) {
  return render(
    <MantineProvider>
      <FlashcardGenerationForm
        {...props}
      />
    </MantineProvider>,
  );
}

describe(
  "FlashcardGenerationForm",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mocks.generateFlashcards
        .mockResolvedValue(
          GENERATED_DECK,
        );
    });

    it(
      "starts with whole-subject scope and 20 cards",
      () => {
        renderForm({
          filterOptions:
            FILTER_OPTIONS,

          onGenerated:
            vi.fn(),
        });

        expect(
          screen.getByRole(
            "radio",
            {
              name:
                "Whole subject",
            },
          ),
        ).toBeChecked();

        expect(
          screen.getByLabelText(
            "Number of cards",
          ),
        ).toHaveValue(
          "20",
        );

        expect(
          screen.queryByLabelText(
            "Study material",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "generates Flashcards from the selected subject",
      async () => {
        const user =
          userEvent.setup();

        const onGenerated =
          vi.fn();

        renderForm({
          filterOptions:
            FILTER_OPTIONS,

          onGenerated,
        });

        await selectOption(
          user,
          "Subject",
          "Biology",
        );

        const cardCountInput =
          screen.getByLabelText(
            "Number of cards",
          );

        fireEvent.change(
          cardCountInput,
          {
            target: {
              value: "10",
            },
          },
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Generate Flashcards",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              mocks.generateFlashcards,
            ).toHaveBeenCalledWith(
              {
                scope_type:
                  "subject",

                subject_id:
                  "subject-1",

                card_count: 10,
              },
            );
          },
        );

        expect(
          onGenerated,
        ).toHaveBeenCalledWith(
          GENERATED_DECK,
        );
      },
    );

    it(
      "generates Flashcards from one ready study material",
      async () => {
        const user =
          userEvent.setup();

        renderForm({
          filterOptions:
            FILTER_OPTIONS,

          onGenerated:
            vi.fn(),
        });

        await user.click(
          screen.getByRole(
            "radio",
            {
              name:
                "Single study material",
            },
          ),
        );

        await selectOption(
          user,
          "Subject",
          "Biology",
        );

        await selectOption(
          user,
          "Study material",
          "Biology Notes.pdf",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Generate Flashcards",
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              mocks.generateFlashcards,
            ).toHaveBeenCalledWith(
              {
                scope_type:
                  "file",

                subject_id:
                  "subject-1",

                study_file_id:
                  "file-1",

                card_count: 20,
              },
            );
          },
        );
      },
    );

    it(
      "clears the selected study material when the subject changes",
      async () => {
        const user =
          userEvent.setup();

        renderForm({
          filterOptions:
            FILTER_OPTIONS,

          onGenerated:
            vi.fn(),
        });

        await user.click(
          screen.getByRole(
            "radio",
            {
              name:
                "Single study material",
            },
          ),
        );

        await selectOption(
          user,
          "Subject",
          "Biology",
        );

        await selectOption(
          user,
          "Study material",
          "Biology Notes.pdf",
        );

        expect(
          screen.getByLabelText(
            "Study material",
          ),
        ).toHaveValue(
          "Biology Notes.pdf",
        );

        await selectOption(
          user,
          "Subject",
          "Chemistry",
        );

        expect(
          screen.getByLabelText(
            "Study material",
          ),
        ).toHaveValue("");
      },
    );

    it(
      "shows a safe Flashcard API error",
      async () => {
        const user =
          userEvent.setup();

        mocks.generateFlashcards
          .mockRejectedValue(
            new FlashcardApiError(
              "The selected study material is not ready for Flashcard generation.",
              409,
              "FLASHCARD_SOURCE_UNAVAILABLE",
            ),
          );

        renderForm({
          filterOptions:
            FILTER_OPTIONS,

          onGenerated:
            vi.fn(),
        });

        await selectOption(
          user,
          "Subject",
          "Biology",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Generate Flashcards",
            },
          ),
        );

        expect(
          await screen.findByText(
            "The selected study material is not ready for Flashcard generation.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "disables generation when filter loading failed",
      () => {
        renderForm({
          filterOptions: {
            subjects: [],
            studyFiles: [],

            loadError:
              "Your subjects and ready study materials could not be loaded. Flashcard generation is temporarily unavailable.",
          },

          onGenerated:
            vi.fn(),
        });

        expect(
          screen.getByText(
            "Your subjects and ready study materials could not be loaded. Flashcard generation is temporarily unavailable.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Generate Flashcards",
            },
          ),
        ).toBeDisabled();
      },
    );
  },
);