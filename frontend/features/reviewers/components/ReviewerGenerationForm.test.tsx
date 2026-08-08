// File: /frontend/features/reviewers/components/ReviewerGenerationForm.test.tsx
// Purpose: Tests reviewer scope, subject/file selection,
// length options, generation requests, and safe errors.

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
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const apiMocks = vi.hoisted(
  () => ({
    generateReviewer:
      vi.fn(),
  }),
);

vi.mock(
  "@/features/reviewers/api",
  () => {
    class ReviewerApiError
      extends Error {
      readonly status:
        number | null;

      readonly code:
        string | null;

      constructor(
        message: string,
        status:
          number | null = null,
        code:
          string | null = null,
      ) {
        super(message);

        this.name =
          "ReviewerApiError";

        this.status =
          status;

        this.code =
          code;
      }
    }

    return {
      generateReviewer:
        apiMocks.generateReviewer,

      ReviewerApiError,
    };
  },
);

import {
  ReviewerApiError,
} from "@/features/reviewers/api";
import type {
  ReviewerFilterOptions,
} from "@/features/reviewers/types";

import {
  ReviewerGenerationForm,
} from "./ReviewerGenerationForm";

const FILTER_OPTIONS:
ReviewerFilterOptions = {
  subjects: [
    {
      id:
        "biology-subject",

      name:
        "Biology",
    },
    {
      id:
        "history-subject",

      name:
        "History",
    },
  ],

  studyFiles: [
    {
      id:
        "biology-file",

      subjectId:
        "biology-subject",

      originalFilename:
        "Biology Notes.pdf",
    },
    {
      id:
        "history-file",

      subjectId:
        "history-subject",

      originalFilename:
        "History Reviewer.pdf",
    },
  ],

  loadError: null,
};

const SUBJECT_REVIEWER_RESPONSE = {
  id:
    "reviewer-id",

  subject_id:
    "biology-subject",

  study_file_id:
    null,

  scope_type:
    "subject" as const,

  title:
    "Biology Reviewer",

  reviewer_length:
    "medium" as const,

  content: {
    overview:
      "A biology reviewer.",

    topics: [
      {
        title:
          "Photosynthesis",

        summary:
          "Plants convert light energy into chemical energy.",

        key_points: [
          "Photosynthesis occurs in chloroplasts.",
        ],

        definitions: [],
      },
    ],
  },

  sources: [
    {
      study_file_id:
        "biology-file",

      source_name:
        "Biology Notes.pdf",

      chunk_index: 0,

      locator_type:
        "page" as const,

      locator_label:
        "Page 1",
    },
  ],

  generation_model:
    "gemini-test-model",

  generation_count: 1,

  generated_at:
    "2026-08-08T08:00:00Z",

  created_at:
    "2026-08-08T08:00:00Z",

  updated_at:
    "2026-08-08T08:00:00Z",
};

function renderForm(
  filterOptions:
    ReviewerFilterOptions =
      FILTER_OPTIONS,
  onGenerated = vi.fn(),
) {
  render(
    <MantineProvider>
      <ReviewerGenerationForm
        filterOptions={
          filterOptions
        }
        onGenerated={
          onGenerated
        }
      />
    </MantineProvider>,
  );

  return {
    onGenerated,
  };
}

async function selectOption(
  user: ReturnType<
    typeof userEvent.setup
  >,
  comboboxName: string,
  optionName: string,
): Promise<void> {
  const combobox =
    screen.getByRole(
      "combobox",
      {
        name:
          comboboxName,
      },
    );

  await user.click(
    combobox,
  );

  /*
   * Mantine Select renders its menu in a
   * portal. jsdom may mark those options
   * hidden even while they are available.
   */
  const option =
    screen.getByRole(
      "option",
      {
        name:
          optionName,

        hidden: true,
      },
    );

  fireEvent.click(
    option,
  );

  await waitFor(() => {
    expect(
      combobox,
    ).toHaveValue(
      optionName,
    );
  });
}

describe(
  "ReviewerGenerationForm",
  () => {
    beforeEach(() => {
      apiMocks
        .generateReviewer
        .mockReset();

      apiMocks
        .generateReviewer
        .mockResolvedValue(
          SUBJECT_REVIEWER_RESPONSE,
        );
    });

    it(
      "starts with subject scope and medium length",
      () => {
        renderForm();

        expect(
          screen.getByRole(
            "combobox",
            {
              name:
                "Generation scope",
            },
          ),
        ).toHaveValue(
          "Whole subject",
        );

        expect(
          screen.getByRole(
            "combobox",
            {
              name:
                "Reviewer length",
            },
          ),
        ).toHaveValue(
          "Medium",
        );

        expect(
          screen.queryByRole(
            "combobox",
            {
              name:
                "Study material",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Generate reviewer",
            },
          ),
        ).toBeDisabled();
      },
    );

    it(
      "generates a subject reviewer with the selected length",
      async () => {
        const user =
          userEvent.setup();

        const {
          onGenerated,
        } = renderForm();

        await selectOption(
          user,
          "Subject",
          "Biology",
        );

        await selectOption(
          user,
          "Reviewer length",
          "Long",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Generate reviewer",
            },
          ),
        );

        await waitFor(() => {
          expect(
            apiMocks
              .generateReviewer,
          ).toHaveBeenCalledWith(
            {
              scope_type:
                "subject",

              subject_id:
                "biology-subject",

              reviewer_length:
                "long",
            },
            {
              signal:
                expect.any(
                  AbortSignal,
                ),
            },
          );
        });

        expect(
          onGenerated,
        ).toHaveBeenCalledWith(
          SUBJECT_REVIEWER_RESPONSE,
        );

        expect(
          await screen.findByText(
            "Reviewer generated",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "generates from one ready study material",
      async () => {
        const user =
          userEvent.setup();

        renderForm();

        await selectOption(
          user,
          "Generation scope",
          "Single study material",
        );

        await selectOption(
          user,
          "Subject",
          "Biology",
        );

        expect(
          screen.queryByRole(
            "option",
            {
              name:
                "History Reviewer.pdf",

              hidden: true,
            },
          ),
        ).not.toBeInTheDocument();

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
                "Generate reviewer",
            },
          ),
        );

        await waitFor(() => {
          expect(
            apiMocks
              .generateReviewer,
          ).toHaveBeenCalledWith(
            {
              scope_type:
                "file",

              subject_id:
                "biology-subject",

              study_file_id:
                "biology-file",

              reviewer_length:
                "medium",
            },
            {
              signal:
                expect.any(
                  AbortSignal,
                ),
            },
          );
        });
      },
    );

    it(
      "clears the selected file when the subject changes",
      async () => {
        const user =
          userEvent.setup();

        renderForm();

        await selectOption(
          user,
          "Generation scope",
          "Single study material",
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

        await selectOption(
          user,
          "Subject",
          "History",
        );

        expect(
          screen.getByRole(
            "combobox",
            {
              name:
                "Study material",
            },
          ),
        ).toHaveValue("");

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Generate reviewer",
            },
          ),
        ).toBeDisabled();
      },
    );

    it(
      "shows a safe reviewer API error",
      async () => {
        apiMocks
          .generateReviewer
          .mockRejectedValue(
            new ReviewerApiError(
              "The selected study material is not ready for reviewer generation.",
              409,
              "REVIEWER_SOURCE_UNAVAILABLE",
            ),
          );

        const user =
          userEvent.setup();

        renderForm();

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
                "Generate reviewer",
            },
          ),
        );

        expect(
          await screen.findByText(
            "The selected study material is not ready for reviewer generation.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Reviewer could not be generated",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "disables generation when filter loading failed",
      () => {
        renderForm({
          subjects: [],
          studyFiles: [],

          loadError:
            "Your subjects and ready study materials could not be loaded. Reviewer generation is temporarily unavailable.",
        });

        expect(
          screen.getByText(
            "Study materials unavailable",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Generate reviewer",
            },
          ),
        ).toBeDisabled();

        expect(
          apiMocks
            .generateReviewer,
        ).not.toHaveBeenCalled();
      },
    );
  },
);