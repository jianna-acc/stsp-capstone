// File: /frontend/features/study-assistant/components/StudyAssistantWorkspace.test.tsx
// Purpose: Tests saved-conversation loading, retry,
// selection, and new-conversation behavior.

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

const conversationApiMocks =
  vi.hoisted(
    () => ({
      listStudyConversations:
        vi.fn(),
      getStudyConversation:
        vi.fn(),
    }),
  );

vi.mock(
  "@/features/study-assistant/conversations-api",
  () => {
    class StudyConversationApiError
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
          "StudyConversationApiError";

        this.status = status;
        this.code = code;
      }
    }

    return {
      listStudyConversations:
        conversationApiMocks
          .listStudyConversations,

      getStudyConversation:
        conversationApiMocks
          .getStudyConversation,

      StudyConversationApiError,
    };
  },
);

vi.mock(
  "./StudyAssistantPanel",
  () => ({
    StudyAssistantPanel: ({
      conversationDetail,
      conversationStatus,
      onAnswerCompleted,
    }: {
      conversationDetail?: {
        messages: Array<{
          id: string;
          content: string;
        }>;
      } | null;
      conversationStatus?: string;
      onAnswerCompleted?: (
        result: {
          conversation_id:
            string;
          outcome:
            "answered";
          answer:
            string;
          sources: [];
          retrieved_count:
            number;
          source_count:
            number;
          context_available:
            boolean;
        },
      ) => void;
    }) => (
      <div>
        <div>
          Study Assistant question workspace
        </div>

        <div>
          Conversation status:{" "}
          {conversationStatus}
        </div>

        {conversationDetail?.messages.map(
          (message) => (
            <div key={message.id}>
              {message.content}
            </div>
          ),
        )}

        <button
          type="button"
          onClick={() => {
            onAnswerCompleted?.({
              conversation_id:
                "new-conversation",
              outcome:
                "answered",
              answer:
                "New saved answer.",
              sources: [],
              retrieved_count: 1,
              source_count: 0,
              context_available:
                true,
            });
          }}
        >
          Complete mock answer
        </button>
      </div>
    ),
  }),
);

import {
  StudyConversationApiError,
} from "@/features/study-assistant/conversations-api";
import type {
  StudyAssistantFilterOptions,
} from "@/types/rag";

import {
  StudyAssistantWorkspace,
} from "./StudyAssistantWorkspace";

const FILTER_OPTIONS:
StudyAssistantFilterOptions = {
  subjects: [],
  studyFiles: [],
  loadError: null,
};

const CONVERSATIONS = [
  {
    id:
      "biology-conversation",

    title:
      "Biology exam review",

    subject_id:
      "biology-subject",

    study_file_id:
      "biology-file",

    created_at:
      "2026-08-05T10:00:00Z",

    updated_at:
      "2026-08-06T10:00:00Z",

    last_message_at:
      "2026-08-06T10:00:00Z",
  },
  {
    id:
      "history-conversation",

    title:
      "History chapter summary",

    subject_id:
      "history-subject",

    study_file_id:
      "history-file",

    created_at:
      "2026-08-04T10:00:00Z",

    updated_at:
      "2026-08-05T10:00:00Z",

    last_message_at:
      "2026-08-05T10:00:00Z",
  },
];

function renderWorkspace() {
  return render(
    <MantineProvider>
      <StudyAssistantWorkspace
        filterOptions={
          FILTER_OPTIONS
        }
      />
    </MantineProvider>,
  );
}

describe(
  "StudyAssistantWorkspace",
  () => {
    beforeEach(() => {
      conversationApiMocks
        .listStudyConversations
        .mockReset();

      conversationApiMocks
        .getStudyConversation
        .mockReset()
        .mockResolvedValue({
          conversation:
            CONVERSATIONS[0],

          messages: [
            {
              id:
                "saved-user-message",
              conversation_id:
                "biology-conversation",
              role: "user",
              content:
                "Explain photosynthesis.",
              outcome: null,
              sources: [],
              created_at:
                "2026-08-06T10:01:00Z",
            },
          ],
        });
    });

    it(
      "loads and displays saved conversations beside the assistant",
      async () => {
        conversationApiMocks
          .listStudyConversations
          .mockResolvedValue({
            items:
              CONVERSATIONS,
          });

        renderWorkspace();

        expect(
          screen.getByLabelText(
            "Loading saved conversations",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Biology exam review",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "History chapter summary",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Study Assistant question workspace",
          ),
        ).toBeInTheDocument();

        expect(
          conversationApiMocks
            .listStudyConversations,
        ).toHaveBeenCalledWith({
          limit: 50,
          signal:
            expect.any(
              AbortSignal,
            ),
        });
      },
    );

    it(
      "selects a saved conversation and clears it for a new conversation",
      async () => {
        const user =
          userEvent.setup();

        conversationApiMocks
          .listStudyConversations
          .mockResolvedValue({
            items:
              CONVERSATIONS,
          });

        renderWorkspace();

        const conversationButton =
          await screen.findByRole(
            "button",
            {
              name:
                /Biology exam review/i,
            },
          );

        await user.click(
          conversationButton,
        );

        expect(
          conversationButton,
        ).toHaveAttribute(
          "aria-current",
          "page",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "New conversation",
            },
          ),
        );

        expect(
          conversationButton,
        ).not.toHaveAttribute(
          "aria-current",
        );
      },
    );

    it(
      "loads the selected conversation messages",
      async () => {
        const user =
          userEvent.setup();

        conversationApiMocks
          .listStudyConversations
          .mockResolvedValue({
            items:
              CONVERSATIONS,
          });

        renderWorkspace();

        const conversationButton =
          await screen.findByRole(
            "button",
            {
              name:
                /Biology exam review/i,
            },
          );

        await user.click(
          conversationButton,
        );

        expect(
          await screen.findByText(
            "Explain photosynthesis.",
          ),
        ).toBeInTheDocument();

        expect(
          conversationApiMocks
            .getStudyConversation,
        ).toHaveBeenCalledWith(
          "biology-conversation",
          {
            messageLimit: 500,
            signal:
              expect.any(
                AbortSignal,
              ),
          },
        );

        expect(
          screen.getByText(
            "Conversation status: ready",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "refreshes history and loads the conversation returned by an answer",
      async () => {
        const user =
          userEvent.setup();

        const newConversation = {
          ...CONVERSATIONS[0],

          id:
            "new-conversation",

          title:
            "New saved conversation",

          updated_at:
            "2026-08-06T11:00:00Z",

          last_message_at:
            "2026-08-06T11:00:00Z",
        };

        conversationApiMocks
          .listStudyConversations
          .mockResolvedValueOnce({
            items:
              CONVERSATIONS,
          })
          .mockResolvedValueOnce({
            items: [
              newConversation,
              ...CONVERSATIONS,
            ],
          });

        conversationApiMocks
          .getStudyConversation
          .mockResolvedValue({
            conversation:
              newConversation,

            messages: [
              {
                id:
                  "new-user-message",
                conversation_id:
                  "new-conversation",
                role: "user",
                content:
                  "New question.",
                outcome: null,
                sources: [],
                created_at:
                  "2026-08-06T11:00:00Z",
              },
            ],
          });

        renderWorkspace();

        await screen.findByText(
          "Biology exam review",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Complete mock answer",
            },
          ),
        );

        await waitFor(() => {
          expect(
            conversationApiMocks
              .getStudyConversation,
          ).toHaveBeenCalledWith(
            "new-conversation",
            {
              messageLimit: 500,
              signal:
                expect.any(
                  AbortSignal,
                ),
            },
          );
        });

        expect(
          await screen.findByText(
            "New saved conversation",
          ),
        ).toBeInTheDocument();

        expect(
          conversationApiMocks
            .listStudyConversations,
        ).toHaveBeenCalledTimes(
          2,
        );
      },
    );

    it(
      "displays an error and retries loading conversation history",
      async () => {
        const user =
          userEvent.setup();

        conversationApiMocks
          .listStudyConversations
          .mockRejectedValueOnce(
            new StudyConversationApiError(
              "Conversation storage is temporarily unavailable.",
              503,
              "STUDY_CONVERSATION_PERSISTENCE_FAILED",
            ),
          )
          .mockResolvedValueOnce({
            items:
              CONVERSATIONS,
          });

        renderWorkspace();

        expect(
          await screen.findByText(
            "History unavailable",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Conversation storage is temporarily unavailable.",
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Retry",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Biology exam review",
          ),
        ).toBeInTheDocument();

        await waitFor(() => {
          expect(
            conversationApiMocks
              .listStudyConversations,
          ).toHaveBeenCalledTimes(
            2,
          );
        });
      },
    );

    it(
      "displays the saved-conversation empty state",
      async () => {
        conversationApiMocks
          .listStudyConversations
          .mockResolvedValue({
            items: [],
          });

        renderWorkspace();

        expect(
          await screen.findByText(
            "No saved conversations yet",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
