// File: /frontend/features/quizzes/components/QuizHistoryPanel.test.tsx
// Purpose: Tests saved Quiz cards, review/retake controls,
// empty history, and delete confirmation behavior.

import {
  MantineProvider,
} from "@mantine/core";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  QuizSummaryResponse,
} from "@/features/quizzes/types";

const mocks =
  vi.hoisted(
    () => ({
      deleteSavedQuiz:
        vi.fn(),

      listQuizAttempts:
        vi.fn(),

      getQuizAttemptReview:
        vi.fn(),
    }),
  );

vi.mock(
  "@/features/quizzes/history-api",
  () => ({
    deleteSavedQuiz:
      mocks.deleteSavedQuiz,

    listQuizAttempts:
      mocks.listQuizAttempts,

    getQuizAttemptReview:
      mocks.getQuizAttemptReview,
  }),
);

import {
  QuizHistoryPanel,
} from "./QuizHistoryPanel";


const QUIZ_ID =
  "11111111-1111-4111-8111-111111111111";

const ATTEMPT_ID =
  "22222222-2222-4222-8222-222222222222";


const QUIZ:
  QuizSummaryResponse = {
    id:
      QUIZ_ID,

    subject_id:
      "33333333-3333-4333-8333-333333333333",

    study_file_id:
      null,

    scope_type:
      "subject",

    title:
      "Biology Practice Quiz",

    quiz_type:
      "mixed",

    difficulty:
      "medium",

    question_count:
      10,

    attempt_count:
      2,

    latest_attempt: {
      id:
        ATTEMPT_ID,

      quiz_id:
        QUIZ_ID,

      status:
        "completed",

      current_position:
        11,

      correct_count:
        8,

      question_count:
        10,

      score_percentage:
        80,

      started_at:
        "2026-08-10T10:00:00Z",

      completed_at:
        "2026-08-10T10:10:00Z",

      created_at:
        "2026-08-10T10:00:00Z",

      updated_at:
        "2026-08-10T10:10:00Z",
    },

    generated_at:
      "2026-08-10T09:50:00Z",

    created_at:
      "2026-08-10T09:50:00Z",

    updated_at:
      "2026-08-10T09:50:00Z",
  };


function renderPanel(
  overrides?: {
    quizzes?:
      QuizSummaryResponse[];

    loading?:
      boolean;

    error?:
      string | null;
  },
) {
  const onRefresh =
    vi.fn(
      async () => {},
    );

  const onTakeQuiz =
    vi.fn(
      async () => {},
    );

  render(
    <MantineProvider>
      <QuizHistoryPanel
        quizzes={
          overrides?.quizzes ??
          [
            QUIZ,
          ]
        }
        loading={
          overrides?.loading ??
          false
        }
        error={
          overrides?.error ??
          null
        }
        onRefresh={
          onRefresh
        }
        onTakeQuiz={
          onTakeQuiz
        }
      />
    </MantineProvider>,
  );

  return {
    onRefresh,
    onTakeQuiz,
  };
}


describe(
  "QuizHistoryPanel",
  () => {
    beforeEach(
      () => {
        mocks.deleteSavedQuiz
          .mockReset();

        mocks.listQuizAttempts
          .mockReset();

        mocks.getQuizAttemptReview
          .mockReset();
      },
    );

    it(
      "displays saved Quiz metadata and latest score",
      () => {
        renderPanel();

        expect(
          screen.getByText(
            "Biology Practice Quiz",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "10 questions",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "80%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                /retake/i,
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                /review latest/i,
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "opens a saved Quiz for retaking",
      async () => {
        const {
          onTakeQuiz,
        } =
          renderPanel();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /retake/i,
            },
          ),
        );

        await waitFor(
          () => {
            expect(
              onTakeQuiz,
            ).toHaveBeenCalledWith(
              QUIZ_ID,
            );
          },
        );
      },
    );

    it(
  "requires confirmation before deleting a Quiz",
  async () => {
    mocks.deleteSavedQuiz
      .mockResolvedValue(
        undefined,
      );

    const {
      onRefresh,
    } =
      renderPanel();

    fireEvent.click(
      screen.getByRole(
        "button",
        {
          name:
            /^delete$/i,
        },
      ),
    );

    const dialog =
      await screen.findByRole(
        "dialog",
        {
          name:
            /delete quiz\?/i,
        },
      );

    expect(
      dialog,
    ).toBeInTheDocument();

    expect(
      mocks.deleteSavedQuiz,
    ).not.toHaveBeenCalled();

    fireEvent.click(
      within(
        dialog,
      ).getByRole(
        "button",
        {
          name:
            /delete quiz/i,
        },
      ),
    );

    await waitFor(
      () => {
        expect(
          mocks.deleteSavedQuiz,
        ).toHaveBeenCalledWith(
          QUIZ_ID,
        );

        expect(
          onRefresh,
        ).toHaveBeenCalled();
      },
    );
  },
);

    it(
      "shows an empty-state message when no saved Quizzes exist",
      () => {
        renderPanel({
          quizzes:
            [],
        });

        expect(
          screen.getByText(
            "No saved Quizzes yet",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /generate a quiz first/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);