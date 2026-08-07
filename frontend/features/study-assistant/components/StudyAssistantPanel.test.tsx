// File: /frontend/features/study-assistant/components/StudyAssistantPanel.test.tsx
// Purpose: Tests Study Assistant questions, filters, answers,
// sources, no-context results, and safe error states.

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
    askStudyAssistant: vi.fn(),
  }),
);

vi.mock(
  "@/features/study-assistant/api",
  () => {
    class StudyAssistantApiError
      extends Error {
      readonly status:
        number | null;

      readonly code:
        string | null;

      constructor(
        message: string,
        status: number | null = null,
        code: string | null = null,
      ) {
        super(message);

        this.name =
          "StudyAssistantApiError";

        this.status = status;
        this.code = code;
      }
    }

    return {
      askStudyAssistant:
        apiMocks.askStudyAssistant,
      StudyAssistantApiError,
    };
  },
);

import {
  StudyAssistantApiError,
} from "@/features/study-assistant/api";
import type {
  StudyAssistantFilterOptions,
} from "@/types/rag";

import {
  StudyAssistantPanel,
} from "./StudyAssistantPanel";

const FILTER_OPTIONS:
StudyAssistantFilterOptions = {
  subjects: [
    {
      id: "biology-subject",
      name: "Biology",
    },
    {
      id: "history-subject",
      name: "History",
    },
  ],

  studyFiles: [
    {
      id: "biology-file",
      subjectId:
        "biology-subject",
      originalFilename:
        "Biology Notes.pdf",
    },
    {
      id: "history-file",
      subjectId:
        "history-subject",
      originalFilename:
        "History Reviewer.pdf",
    },
  ],

  loadError: null,
};

const ANSWER_RESPONSE = {
  conversation_id:
    "conversation-id",

  outcome: "answered" as const,

  answer:
    "Photosynthesis converts light energy into chemical energy. [Source 1]",

  sources: [
    {
      source_number: 1,
      source_name:
        "Biology Notes.pdf",
      chunk_index: 2,
      similarity_score: 0.91,
    },
  ],

  retrieved_count: 3,
  source_count: 1,
  context_available: true,
};

function renderPanel(
  filterOptions:
    StudyAssistantFilterOptions =
      FILTER_OPTIONS,
) {
  return render(
    <MantineProvider>
      <StudyAssistantPanel
        filterOptions={
          filterOptions
        }
      />
    </MantineProvider>,
  );
}

function getQuestionInput():
HTMLTextAreaElement {
  return screen.getByPlaceholderText(
    "For example: What are the main ideas discussed in my uploaded notes?",
  ) as HTMLTextAreaElement;
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
        name: comboboxName,
      },
    );

  await user.click(combobox);

  /*
   * Mantine renders Select options in a portal. In jsdom,
   * the dropdown can remain marked as visually hidden even
   * though its option elements are available in the DOM.
   */
  const option =
    screen.getByRole(
      "option",
      {
        name: optionName,
        hidden: true,
      },
    );

  fireEvent.click(option);

  await waitFor(() => {
    expect(
      combobox,
    ).toHaveValue(optionName);
  });
}

describe(
  "StudyAssistantPanel",
  () => {
    beforeEach(() => {
      apiMocks
        .askStudyAssistant
        .mockResolvedValue(
          ANSWER_RESPONSE,
        );
    });

    it(
      "submits a question and displays its grounded sources",
      async () => {
        const user =
          userEvent.setup();

        renderPanel();

        await user.type(
          getQuestionInput(),
          "Explain photosynthesis.",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask Study Assistant",
            },
          ),
        );

        await waitFor(() => {
          expect(
            apiMocks
              .askStudyAssistant,
          ).toHaveBeenCalledWith(
            {
              question:
                "Explain photosynthesis.",
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
          await screen.findByText(
            "Grounded answer",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            ANSWER_RESPONSE.answer,
          ),
        ).toBeInTheDocument();

        const sourceNumber =
          await screen.findByText(
            "SOURCE 1",
          );

        const sourceCard =
          sourceNumber.closest("li");

        expect(
          sourceCard,
        ).not.toBeNull();

        const sourceCardQueries =
          within(
            sourceCard as HTMLElement,
          );

        expect(
          sourceCardQueries.getByText(
            "Biology Notes.pdf",
          ),
        ).toBeInTheDocument();

        expect(
          sourceCardQueries.getByText(
            "91% match",
          ),
        ).toBeInTheDocument();

        expect(
          sourceCardQueries.getByText(
            "Material section 3",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "submits selected subject and study-file filters",
      async () => {
        const user =
          userEvent.setup();

        renderPanel();

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

        await user.type(
          getQuestionInput(),
          "Explain this material.",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask Study Assistant",
            },
          ),
        );

        await waitFor(() => {
          expect(
            apiMocks
              .askStudyAssistant,
          ).toHaveBeenCalledWith(
            {
              question:
                "Explain this material.",

              subject_id:
                "biology-subject",

              study_file_id:
                "biology-file",
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
      "continues a selected saved conversation",
      async () => {
        const user =
          userEvent.setup();

        const onAnswerCompleted =
          vi.fn();

        render(
          <MantineProvider>
            <StudyAssistantPanel
              filterOptions={
                FILTER_OPTIONS
              }
              conversationStatus="ready"
              conversationDetail={{
                conversation: {
                  id:
                    "conversation-id",
                  title:
                    "Biology review",
                  subject_id:
                    "biology-subject",
                  study_file_id:
                    "biology-file",
                  created_at:
                    "2026-08-06T10:00:00Z",
                  updated_at:
                    "2026-08-06T10:05:00Z",
                  last_message_at:
                    "2026-08-06T10:05:00Z",
                },
                messages: [],
              }}
              onAnswerCompleted={
                onAnswerCompleted
              }
            />
          </MantineProvider>,
        );

        await user.type(
          getQuestionInput(),
          "What happens next?",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask Study Assistant",
            },
          ),
        );

        await waitFor(() => {
          expect(
            apiMocks
              .askStudyAssistant,
          ).toHaveBeenCalledWith(
            {
              question:
                "What happens next?",

              conversation_id:
                "conversation-id",

              subject_id:
                "biology-subject",

              study_file_id:
                "biology-file",
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
          onAnswerCompleted,
        ).toHaveBeenCalledWith(
          ANSWER_RESPONSE,
        );

        expect(
          getQuestionInput(),
        ).toHaveValue("");
      },
    );

    it(
      "displays a normal no-context result",
      async () => {
        apiMocks
          .askStudyAssistant
          .mockResolvedValue({
            conversation_id:
              "conversation-id",

            outcome:
              "no_context",

            answer:
              "I could not find enough relevant information in your uploaded study materials to answer this question.",

            sources: [],
            retrieved_count: 0,
            source_count: 0,

            context_available:
              false,
          });

        const user =
          userEvent.setup();

        renderPanel();

        await user.type(
          getQuestionInput(),
          "What is not covered?",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask Study Assistant",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Not enough context",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "No context",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Sources used",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "displays a safe authenticated API error",
      async () => {
        apiMocks
          .askStudyAssistant
          .mockRejectedValue(
            new StudyAssistantApiError(
              "Your session has expired. Sign in again.",
              401,
              "AUTHENTICATION_REQUIRED",
            ),
          );

        const user =
          userEvent.setup();

        renderPanel();

        await user.type(
          getQuestionInput(),
          "Explain my notes.",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask Study Assistant",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Your session has expired. Sign in again.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "The question could not be answered",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);