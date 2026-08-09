// File: /frontend/features/reviewers/components/ReviewerWorkspace.test.tsx
// Purpose: Tests the Reviewer workspace header, generation
// controls, and newly generated reviewer presentation.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
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
  ReviewerFilterOptions,
  ReviewerResponse,
} from "@/features/reviewers/types";

const REVIEWER:
ReviewerResponse = {
  id:
    "reviewer-id",

  subject_id:
    "biology-subject",

  study_file_id:
    null,

  scope_type:
    "subject",

  title:
    "Biology Reviewer",

  reviewer_length:
    "medium",

  content: {
    overview:
      "Biology overview.",

    topics: [
      {
        title:
          "Cells",

        summary:
          "Cells are basic units of life.",

        key_points: [
          "Cells perform essential functions.",
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
        "page",

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

const mocks = vi.hoisted(
  () => ({
    deleteReviewer:
      vi.fn(),
    getReviewer:
      vi.fn(),
    listReviewers:
      vi.fn(),
    regenerateReviewer:
      vi.fn(),
  }),
);

vi.mock(
  "@/features/reviewers/api",
  () => ({
    deleteReviewer:
      mocks.deleteReviewer,
    getReviewer:
      mocks.getReviewer,
    listReviewers:
      mocks.listReviewers,
    regenerateReviewer:
      mocks.regenerateReviewer,
  }),
);

vi.mock(
  "@/features/reviewers/components/ReviewerGenerationForm",
  () => ({
    ReviewerGenerationForm: ({
      onGenerated,
    }: {
      onGenerated?: (
        reviewer:
          ReviewerResponse,
      ) => void;
    }) => (
      <button
        type="button"
        onClick={() =>
          onGenerated?.(
            REVIEWER,
          )
        }
      >
        Mock generate reviewer
      </button>
    ),
  }),
);

vi.mock(
  "@/features/reviewers/components/ReviewerResult",
  () => ({
    ReviewerResult: ({
      reviewer,
      onRegenerate,
    }: {
      reviewer:
        ReviewerResponse;
      onRegenerate?:
        () => Promise<void>;
    }) => (
      <div>
        <div>
          Result:{" "}
          {reviewer.title}
        </div>

        <div>
          Generation{" "}
          {reviewer.generation_count}
        </div>

        <button
          type="button"
          onClick={() => {
            void onRegenerate?.();
          }}
        >
          Mock regenerate reviewer
        </button>
      </div>
    ),
  }),
);

import {
  ReviewerWorkspace,
} from "./ReviewerWorkspace";

const FILTER_OPTIONS:
ReviewerFilterOptions = {
  subjects: [
    {
      id:
        "biology-subject",

      name:
        "Biology",
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
  ],

  loadError: null,
};

function renderWorkspace():
  void {
  render(
    <MantineProvider>
      <ReviewerWorkspace
        filterOptions={
          FILTER_OPTIONS
        }
      />
    </MantineProvider>,
  );
}

describe(
  "ReviewerWorkspace",
  () => {
    beforeEach(() => {
        mocks.listReviewers
            .mockResolvedValue({
            items: [],
            });
        });
    it(
      "renders the Reviewer workspace and generation controls",
      () => {
        renderWorkspace();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Reviewers",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Mock generate reviewer",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Result: Biology Reviewer",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "shows the newly generated reviewer",
      async () => {
        const user =
          userEvent.setup();

        renderWorkspace();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Mock generate reviewer",
            },
          ),
        );

        expect(
          screen.getByText(
            "Result: Biology Reviewer",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "region",
            {
              name:
                "Generated reviewer",
            },
          ),
        ).toBeInTheDocument();
      },
    );
    it(
    "opens a saved reviewer from history",
    async () => {
        const user =
        userEvent.setup();

        mocks.listReviewers
        .mockResolvedValue({
            items: [
            REVIEWER,
            ],
        });

        mocks.getReviewer
        .mockResolvedValue(
            REVIEWER,
        );

        renderWorkspace();

        await user.click(
        await screen.findByRole(
            "button",
            {
            name: "Open",
            },
        ),
        );

        expect(
        mocks.getReviewer,
        ).toHaveBeenCalledWith(
        "reviewer-id",
        );

        expect(
        await screen.findByText(
            "Result: Biology Reviewer",
        ),
        ).toBeInTheDocument();
    },
    );
    it(
  "deletes a saved reviewer from history",
  async () => {
    const user =
      userEvent.setup();

    mocks.listReviewers
      .mockResolvedValue({
        items: [
          REVIEWER,
        ],
      });

    mocks.deleteReviewer
      .mockResolvedValue(
        undefined,
      );

    vi.spyOn(
      window,
      "confirm",
    ).mockReturnValue(true);

    renderWorkspace();

    await user.click(
      await screen.findByRole(
        "button",
        {
          name: "Delete",
        },
      ),
    );

    expect(
      mocks.deleteReviewer,
    ).toHaveBeenCalledWith(
      "reviewer-id",
    );

    expect(
      screen.queryByText(
        "Biology Reviewer",
      ),
    ).not.toBeInTheDocument();
  },
);

    it(
        "regenerates the displayed reviewer",
        async () => {
            const user =
            userEvent.setup();

            const regeneratedReviewer = {
            ...REVIEWER,
            generation_count: 2,
            updated_at:
                "2026-08-08T09:00:00Z",
            };

            mocks.regenerateReviewer
            .mockResolvedValue(
                regeneratedReviewer,
            );

            renderWorkspace();

            await user.click(
            screen.getByRole(
                "button",
                {
                name:
                    "Mock generate reviewer",
                },
            ),
            );

            expect(
            screen.getAllByText(
                "Generation 1",
            ),
            ).toHaveLength(2);

            await user.click(
            screen.getByRole(
                "button",
                {
                name:
                    "Mock regenerate reviewer",
                },
            ),
            );

            expect(
            await screen.findAllByText(
                "Generation 2",
            ),
            ).toHaveLength(2);

            expect(
            mocks.regenerateReviewer,
            ).toHaveBeenCalledWith(
            "reviewer-id",
            );
        },
        );
  },
);