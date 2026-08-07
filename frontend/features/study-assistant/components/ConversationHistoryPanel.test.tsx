// File: /frontend/features/study-assistant/components/ConversationHistoryPanel.test.tsx
// Purpose: Tests loading, empty, error, list, selection,
// retry, and new-conversation states.

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

import type {
  StudyConversationResponse,
} from "@/types/study-conversation";

import {
  ConversationHistoryPanel,
  type ConversationHistoryStatus,
} from "./ConversationHistoryPanel";

const CONVERSATIONS:
StudyConversationResponse[] = [
  {
    id: "biology-conversation",
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
    id: "history-conversation",
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

interface RenderHistoryOptions {
  status?: ConversationHistoryStatus;
  conversations?: StudyConversationResponse[];
  selectedConversationId?: string | null;
  errorMessage?: string | null;
}

function renderHistory({
  status = "ready",
  conversations = CONVERSATIONS,
  selectedConversationId = null,
  errorMessage = null,
}: RenderHistoryOptions = {}) {
  const onSelectConversation =
    vi.fn();

  const onStartNewConversation =
    vi.fn();

  const onRetry =
    vi.fn();

  render(
    <MantineProvider>
      <ConversationHistoryPanel
        status={status}
        conversations={
          conversations
        }
        selectedConversationId={
          selectedConversationId
        }
        errorMessage={
          errorMessage
        }
        onSelectConversation={
          onSelectConversation
        }
        onStartNewConversation={
          onStartNewConversation
        }
        onRetry={onRetry}
      />
    </MantineProvider>,
  );

  return {
    onSelectConversation,
    onStartNewConversation,
    onRetry,
  };
}

describe(
  "ConversationHistoryPanel",
  () => {
    it(
      "displays the loading state",
      () => {
        renderHistory({
          status: "loading",
          conversations: [],
        });

        expect(
          screen.getByLabelText(
            "Loading saved conversations",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "No saved conversations yet",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "displays the empty state and starts a new conversation",
      async () => {
        const user =
          userEvent.setup();

        const {
          onStartNewConversation,
        } = renderHistory({
          conversations: [],
        });

        expect(
          screen.getByText(
            "No saved conversations yet",
          ),
        ).toBeInTheDocument();

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
          onStartNewConversation,
        ).toHaveBeenCalledTimes(1);
      },
    );

    it(
      "displays an error and retries loading",
      async () => {
        const user =
          userEvent.setup();

        const {
          onRetry,
        } = renderHistory({
          status: "error",
          conversations: [],
          errorMessage:
            "Conversation storage is temporarily unavailable.",
        });

        expect(
          screen.getByText(
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
          onRetry,
        ).toHaveBeenCalledTimes(1);
      },
    );

    it(
      "marks the selected conversation and allows switching",
      async () => {
        const user =
          userEvent.setup();

        const {
          onSelectConversation,
        } = renderHistory({
          selectedConversationId:
            "biology-conversation",
        });

        const selectedButton =
          screen.getByRole(
            "button",
            {
              name:
                /Biology exam review/i,
            },
          );

        expect(
          selectedButton,
        ).toHaveAttribute(
          "aria-current",
          "page",
        );

        const historyButton =
          screen.getByRole(
            "button",
            {
              name:
                /History chapter summary/i,
            },
          );

        expect(
          historyButton,
        ).not.toHaveAttribute(
          "aria-current",
        );

        await user.click(
          historyButton,
        );

        expect(
          onSelectConversation,
        ).toHaveBeenCalledWith(
          "history-conversation",
        );
      },
    );
  },
);
