// File: /frontend/features/study-assistant/components/ConversationHistoryPanel.tsx
// Purpose: Displays loading, empty, error, selected, and
// available states for saved Study Assistant conversations.

"use client";

import {
  Alert,
  Button,
  Group,
  Paper,
  ScrollArea,
  Skeleton,
  Stack,
  Text,
  ThemeIcon,
  UnstyledButton,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconMessage,
  IconMessages,
  IconPlus,
  IconRefresh,
} from "@tabler/icons-react";

import type {
  StudyConversationResponse,
} from "@/types/study-conversation";

import classes from "./ConversationHistoryPanel.module.css";

export type ConversationHistoryStatus =
  | "loading"
  | "ready"
  | "error";

interface ConversationHistoryPanelProps {
  conversations: StudyConversationResponse[];
  selectedConversationId: string | null;
  status: ConversationHistoryStatus;
  errorMessage?: string | null;
  disabled?: boolean;
  onSelectConversation: (
    conversationId: string,
  ) => void;
  onStartNewConversation: () => void;
  onRetry: () => void;
}

function formatConversationDate(
  timestamp: string,
): string {
  const parsedTimestamp =
    Date.parse(timestamp);

  if (!Number.isFinite(parsedTimestamp)) {
    return "Recently updated";
  }

  return new Intl.DateTimeFormat(
    "en",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    },
  ).format(
    new Date(parsedTimestamp),
  );
}

export function ConversationHistoryPanel({
  conversations,
  selectedConversationId,
  status,
  errorMessage,
  disabled = false,
  onSelectConversation,
  onStartNewConversation,
  onRetry,
}: ConversationHistoryPanelProps) {
  return (
    <Paper
      component="aside"
      withBorder
      radius="lg"
      p="md"
      className={classes.panel}
      aria-label="Saved conversations"
    >
      <Stack
        gap="md"
        h="100%"
      >
        <Group
          justify="space-between"
          align="center"
          wrap="nowrap"
          className={classes.header}
        >
          <Group
            gap="xs"
            wrap="nowrap"
          >
            <ThemeIcon
              variant="light"
              color="violet"
              radius="md"
            >
              <IconMessages
                size={19}
                stroke={1.8}
              />
            </ThemeIcon>

            <div>
              <Text
                fw={750}
                size="sm"
              >
                Saved conversations
              </Text>

              <Text
                size="xs"
                c="dimmed"
              >
                Continue an earlier discussion
              </Text>
            </div>
          </Group>
        </Group>

        <Button
          variant="light"
          color="violet"
          leftSection={
            <IconPlus size={17} />
          }
          onClick={
            onStartNewConversation
          }
          disabled={disabled}
          fullWidth
        >
          New conversation
        </Button>

        {status === "loading" && (
          <Stack
            gap="sm"
            aria-label="Loading saved conversations"
          >
            <Skeleton
              height={64}
              radius="md"
            />

            <Skeleton
              height={64}
              radius="md"
            />

            <Skeleton
              height={64}
              radius="md"
            />
          </Stack>
        )}

        {status === "error" && (
          <Alert
            color="red"
            variant="light"
            title="History unavailable"
            icon={
              <IconAlertCircle
                size={18}
              />
            }
          >
            <Stack gap="sm">
              <Text size="sm">
                {errorMessage ??
                  "Your saved conversations could not be loaded."}
              </Text>

              <Button
                variant="subtle"
                color="red"
                size="compact-sm"
                leftSection={
                  <IconRefresh
                    size={16}
                  />
                }
                onClick={onRetry}
                disabled={disabled}
                className={
                  classes.retryButton
                }
              >
                Retry
              </Button>
            </Stack>
          </Alert>
        )}

        {status === "ready" &&
          conversations.length === 0 && (
            <Paper
              withBorder
              radius="md"
              p="lg"
              className={
                classes.emptyState
              }
            >
              <Stack
                gap="xs"
                align="center"
                ta="center"
              >
                <ThemeIcon
                  variant="light"
                  color="gray"
                  size="lg"
                  radius="xl"
                >
                  <IconMessage
                    size={20}
                  />
                </ThemeIcon>

                <Text
                  fw={700}
                  size="sm"
                >
                  No saved conversations yet
                </Text>

                <Text
                  size="xs"
                  c="dimmed"
                >
                  Your first question will
                  automatically create a saved
                  conversation.
                </Text>
              </Stack>
            </Paper>
          )}

        {status === "ready" &&
          conversations.length > 0 && (
            <ScrollArea
              type="auto"
              scrollbarSize={7}
              className={
                classes.scrollArea
              }
            >
              <Stack
                gap="xs"
                className={
                  classes.conversationList
                }
              >
                {conversations.map(
                  (conversation) => {
                    const isSelected =
                      conversation.id ===
                      selectedConversationId;

                    return (
                      <UnstyledButton
                        key={
                          conversation.id
                        }
                        type="button"
                        className={[
                          classes.conversationItem,
                          isSelected
                            ? classes.selectedConversation
                            : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        onClick={() => {
                          onSelectConversation(
                            conversation.id,
                          );
                        }}
                        disabled={disabled}
                        aria-current={
                          isSelected
                            ? "page"
                            : undefined
                        }
                      >
                        <Group
                          align="flex-start"
                          wrap="nowrap"
                          gap="sm"
                        >
                          <ThemeIcon
                            size="sm"
                            radius="xl"
                            variant={
                              isSelected
                                ? "filled"
                                : "light"
                            }
                            color="violet"
                            className={
                              classes.itemIcon
                            }
                          >
                            <IconMessage
                              size={14}
                            />
                          </ThemeIcon>

                          <div
                            className={
                              classes.itemContent
                            }
                          >
                            <Text
                              fw={650}
                              size="sm"
                              lineClamp={2}
                              className={
                                classes.conversationTitle
                              }
                            >
                              {
                                conversation.title
                              }
                            </Text>

                            <Text
                              component="time"
                              dateTime={
                                conversation.last_message_at
                              }
                              size="xs"
                              c="dimmed"
                              mt={3}
                            >
                              Updated{" "}
                              {formatConversationDate(
                                conversation.last_message_at,
                              )}
                            </Text>
                          </div>
                        </Group>
                      </UnstyledButton>
                    );
                  },
                )}
              </Stack>
            </ScrollArea>
          )}
      </Stack>
    </Paper>
  );
}
