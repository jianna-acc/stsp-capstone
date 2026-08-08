// File: /frontend/features/reviewers/components/ReviewerResult.test.tsx
// Purpose: Tests generated reviewer overview, topics,
// definitions, metadata, and source presentation.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  ReviewerResponse,
} from "@/features/reviewers/types";

import {
  ReviewerResult,
} from "./ReviewerResult";

const REVIEWER:
ReviewerResponse = {
  id:
    "reviewer-id",

  subject_id:
    "biology-subject",

  study_file_id:
    "biology-file",

  scope_type:
    "file",

  title:
    "Biology Reviewer",

  reviewer_length:
    "medium",

  content: {
    overview:
      "This reviewer summarizes the important biology concepts.",

    topics: [
      {
        title:
          "Photosynthesis",

        summary:
          "Photosynthesis converts light energy into stored chemical energy.",

        key_points: [
          "Photosynthesis occurs mainly in chloroplasts.",
          "Plants use carbon dioxide and water during the process.",
        ],

        definitions: [
          {
            term:
              "Chloroplast",

            definition:
              "An organelle where photosynthesis occurs.",
          },
        ],
      },
      {
        title:
          "Cellular Respiration",

        summary:
          "Cells release usable energy from nutrients.",

        key_points: [
          "ATP stores usable cellular energy.",
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

      chunk_index: 2,

      locator_type:
        "page",

      locator_label:
        "Page 3",
    },
    {
      study_file_id:
        "biology-file",

      source_name:
        "Biology Notes.pdf",

      chunk_index: 5,

      locator_type:
        null,

      locator_label:
        null,
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

function renderReviewer(
  reviewer:
    ReviewerResponse =
      REVIEWER,
): void {
    render(
    <MantineProvider>
        <ReviewerResult
        reviewer={reviewer}
        onRegenerate={
            async () => {}
        }
        isRegenerating
        />
    </MantineProvider>,
    );
}

describe(
  "ReviewerResult",
  () => {
    it(
      "displays the reviewer title, overview, scope, and length",
      () => {
        renderReviewer();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Biology Reviewer",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "This reviewer summarizes the important biology concepts.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Medium",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Single material",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "displays topics and their key points",
      () => {
        renderReviewer();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Photosynthesis",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Cellular Respiration",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Photosynthesis occurs mainly in chloroplasts.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "ATP stores usable cellular energy.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "displays definitions when the topic has important terms",
      () => {
        renderReviewer();

        expect(
          screen.getByText(
            "Chloroplast",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "An organelle where photosynthesis occurs.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Important terms",
          ),
        ).toHaveLength(1);
      },
    );

    it(
      "displays provided and fallback source locations",
      () => {
        renderReviewer();

        expect(
          screen.getAllByText(
            "Biology Notes.pdf",
          ),
        ).toHaveLength(2);

        expect(
          screen.getByText(
            "Page 3",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Material section 6",
          ),
        ).toBeInTheDocument();
      },
    );
    it(
        "displays reviewer regeneration controls",
        () => {
            render(
            <MantineProvider>
                <ReviewerResult
                reviewer={REVIEWER}
                onRegenerate={
                    async () => {}
                }
                isRegenerating
                />
            </MantineProvider>,
            );

            expect(
            screen.getByRole(
                "button",
                {
                name:
                    "Regenerate Reviewer",
                },
            ),
            ).toBeDisabled();

            expect(
            screen.getByText(
                "Generation 1",
            ),
            ).toBeInTheDocument();
        },
        );
  },
);