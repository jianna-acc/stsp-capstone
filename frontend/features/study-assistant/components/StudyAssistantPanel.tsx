// File: /frontend/features/study-assistant/components/StudyAssistantPanel.tsx
// Purpose: Provides the authenticated question-and-answer
// interface for the AI Study Assistant.

"use client";

import {
  Alert,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconBook2,
  IconBulb,
  IconFileText,
  IconRefresh,
  IconSend,
  IconSparkles,
  IconUser,
} from "@tabler/icons-react";
import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  askStudyAssistant,
  StudyAssistantApiError,
} from "@/features/study-assistant/api";
import type {
  RagAnswerResponse,
  StudyAssistantFilterOptions,
} from "@/types/rag";
import type {
  StudyConversationDetailResponse,
} from "@/types/study-conversation";

import classes from "./StudyAssistantPanel.module.css";

export type SelectedConversationStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";

interface StudyAssistantPanelProps {
  filterOptions: StudyAssistantFilterOptions;
  conversationDetail?:
    StudyConversationDetailResponse | null;
  conversationStatus?:
    SelectedConversationStatus;
  conversationError?: string | null;
  onRetryConversation?: () => void;
  onAnswerCompleted?: (
    result: RagAnswerResponse,
  ) => void;
}

type AssistantState =
  | {
      status: "idle";
    }
  | {
      status: "loading";
    }
  | {
      status: "success";
      result: RagAnswerResponse;
    }
  | {
      status: "error";
      message: string;
    };

const EMPTY_QUESTION_MESSAGE =
  "Enter a question before asking the Study Assistant.";

const UNEXPECTED_ERROR_MESSAGE =
  "An unexpected error occurred while asking the Study Assistant.";

function formatSimilarityScore(
  score: number,
): string {
  const normalizedScore = Math.min(
    1,
    Math.max(0, score),
  );

  return `${Math.round(
    normalizedScore * 100,
  )}% match`;
}

export function StudyAssistantPanel({
  filterOptions,
  conversationDetail = null,
  conversationStatus = "idle",
  conversationError = null,
  onRetryConversation,
  onAnswerCompleted,
}: StudyAssistantPanelProps) {
  const [question, setQuestion] =
    useState("");

  const [
    selectedSubjectId,
    setSelectedSubjectId,
  ] = useState<string | null>(
    conversationDetail
      ?.conversation.subject_id ??
      null,
  );

  const [
    selectedStudyFileId,
    setSelectedStudyFileId,
  ] = useState<string | null>(
    conversationDetail
      ?.conversation.study_file_id ??
      null,
  );

  const [state, setState] =
    useState<AssistantState>({
      status: "idle",
    });

  const activeRequestRef =
    useRef<AbortController | null>(
      null,
    );

  useEffect(() => {
    return () => {
      activeRequestRef.current?.abort();
    };
  }, []);

  const isLoading =
    state.status === "loading";

  const conversationInteractionBlocked =
    conversationStatus === "loading" ||
    conversationStatus === "error";

  const isInteractionDisabled =
    isLoading ||
    conversationInteractionBlocked;

  const activeConversationId =
    conversationDetail
      ?.conversation.id ??
      null;

  const subjectSelectData =
    filterOptions.subjects.map(
      (subject) => ({
        value: subject.id,
        label: subject.name,
      }),
    );

  const visibleStudyFiles =
    selectedSubjectId
      ? filterOptions.studyFiles.filter(
          (studyFile) =>
            studyFile.subjectId ===
            selectedSubjectId,
        )
      : filterOptions.studyFiles;

  const studyFileSelectData =
    visibleStudyFiles.map(
      (studyFile) => ({
        value: studyFile.id,
        label:
          studyFile.originalFilename,
      }),
    );

  function handleSubjectChange(
    subjectId: string | null,
  ): void {
    setSelectedSubjectId(subjectId);

    setSelectedStudyFileId(
      (currentStudyFileId) => {
        if (!currentStudyFileId) {
          return null;
        }

        if (!subjectId) {
          return currentStudyFileId;
        }

        const selectedStudyFile =
          filterOptions.studyFiles.find(
            (studyFile) =>
              studyFile.id ===
              currentStudyFileId,
          );

        if (
          selectedStudyFile?.subjectId ===
          subjectId
        ) {
          return currentStudyFileId;
        }

        return null;
      },
    );
  }

  function handleStudyFileChange(
    studyFileId: string | null,
  ): void {
    setSelectedStudyFileId(
      studyFileId,
    );

    if (!studyFileId) {
      return;
    }

    const selectedStudyFile =
      filterOptions.studyFiles.find(
        (studyFile) =>
          studyFile.id ===
          studyFileId,
      );

    if (selectedStudyFile) {
      setSelectedSubjectId(
        selectedStudyFile.subjectId,
      );
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    const normalizedQuestion =
      question.trim();

    if (!normalizedQuestion) {
      setState({
        status: "error",
        message: EMPTY_QUESTION_MESSAGE,
      });

      return;
    }

    activeRequestRef.current?.abort();

    const requestController =
      new AbortController();

    activeRequestRef.current =
      requestController;

    setState({
      status: "loading",
    });

    try {
      const result =
        await askStudyAssistant(
          {
            question:
              normalizedQuestion,

            ...(activeConversationId
              ? {
                  conversation_id:
                    activeConversationId,
                }
              : {}),

            ...(selectedSubjectId
              ? {
                  subject_id:
                    selectedSubjectId,
                }
              : {}),

            ...(selectedStudyFileId
              ? {
                  study_file_id:
                    selectedStudyFileId,
                }
              : {}),
          },
          {
            signal:
              requestController.signal,
          },
        );

      setQuestion("");

      setState({
        status: "success",
        result,
      });

      onAnswerCompleted?.(
        result,
      );
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      const message =
        error instanceof
        StudyAssistantApiError
          ? error.message
          : UNEXPECTED_ERROR_MESSAGE;

      setState({
        status: "error",
        message,
      });
    } finally {
      if (
        activeRequestRef.current ===
        requestController
      ) {
        activeRequestRef.current =
          null;
      }
    }
  }

  return (
    <main className={classes.page}>
      <Container
        size="lg"
        className={classes.container}
      >
        <Stack gap="xl">
          <header className={classes.header}>
            <Group
              align="flex-start"
              wrap="nowrap"
              gap="md"
            >
              <ThemeIcon
                size={52}
                radius="lg"
                variant="gradient"
                gradient={{
                  from: "violet",
                  to: "grape",
                }}
              >
                <IconSparkles
                  size={28}
                  stroke={1.8}
                />
              </ThemeIcon>

              <div>
                <Group gap="sm">
                  <Title order={1}>
                    Study Assistant
                  </Title>

                  <Badge
                    variant="light"
                    color="violet"
                  >
                    AI-powered
                  </Badge>
                </Group>

                <Text
                  c="dimmed"
                  mt={5}
                  maw={680}
                >
                  Ask questions about your
                  uploaded learning materials.
                  Answers are generated using
                  relevant content that belongs
                  to your account.
                </Text>
              </div>
            </Group>
          </header>

          {conversationStatus ===
            "loading" && (
            <Paper
              component="section"
              withBorder
              radius="lg"
              p="xl"
              className={
                classes.resultCard
              }
              aria-live="polite"
            >
              <Group
                align="flex-start"
                wrap="nowrap"
              >
                <ThemeIcon
                  variant="light"
                  color="violet"
                  radius="md"
                >
                  <IconBook2
                    size={20}
                  />
                </ThemeIcon>

                <div>
                  <Text fw={700}>
                    Loading saved conversation
                  </Text>

                  <Text
                    size="sm"
                    c="dimmed"
                    mt={4}
                  >
                    Retrieving the saved
                    messages and material
                    filters.
                  </Text>
                </div>
              </Group>
            </Paper>
          )}

          {conversationStatus ===
            "error" && (
            <Alert
              color="red"
              variant="light"
              title="Conversation unavailable"
              icon={
                <IconAlertCircle
                  size={19}
                />
              }
              aria-live="assertive"
            >
              <Stack gap="sm">
                <Text size="sm">
                  {conversationError ??
                    "The selected conversation could not be loaded."}
                </Text>

                {onRetryConversation && (
                  <Button
                    variant="subtle"
                    color="red"
                    size="compact-sm"
                    leftSection={
                      <IconRefresh
                        size={16}
                      />
                    }
                    onClick={
                      onRetryConversation
                    }
                  >
                    Retry conversation
                  </Button>
                )}
              </Stack>
            </Alert>
          )}

          {conversationStatus ===
            "ready" &&
            conversationDetail && (
            <Paper
              component="section"
              withBorder
              radius="lg"
              p={{
                base: "md",
                sm: "xl",
              }}
              className={
                classes.resultCard
              }
              aria-label="Saved conversation messages"
            >
              <Stack gap="lg">
                <div>
                  <Text
                    fw={750}
                    size="lg"
                  >
                    {
                      conversationDetail
                        .conversation.title
                    }
                  </Text>

                  <Text
                    size="sm"
                    c="dimmed"
                  >
                    {
                      conversationDetail
                        .messages.length
                    }{" "}
                    saved message
                    {conversationDetail
                      .messages.length ===
                    1
                      ? ""
                      : "s"}
                  </Text>
                </div>

                {conversationDetail
                  .messages.length ===
                0 ? (
                  <Text
                    size="sm"
                    c="dimmed"
                  >
                    This conversation does not
                    contain any saved messages
                    yet.
                  </Text>
                ) : (
                  <Stack
                    gap="sm"
                    className={
                      classes.transcript
                    }
                  >
                    {conversationDetail.messages.map(
                      (message) => (
                        <Paper
                          key={message.id}
                          withBorder
                          radius="md"
                          p="md"
                          className={[
                            classes.savedMessage,
                            message.role ===
                            "user"
                              ? classes.userMessage
                              : classes.assistantMessage,
                          ].join(" ")}
                        >
                          <Group
                            align="flex-start"
                            wrap="nowrap"
                            gap="sm"
                          >
                            <ThemeIcon
                              variant="light"
                              color={
                                message.role ===
                                "user"
                                  ? "blue"
                                  : "violet"
                              }
                              radius="xl"
                              className={
                                classes.messageIcon
                              }
                            >
                              {message.role ===
                              "user" ? (
                                <IconUser
                                  size={17}
                                />
                              ) : (
                                <IconSparkles
                                  size={17}
                                />
                              )}
                            </ThemeIcon>

                            <div
                              className={
                                classes.messageBody
                              }
                            >
                              <Text
                                size="xs"
                                fw={700}
                                c="dimmed"
                                tt="uppercase"
                              >
                                {message.role ===
                                "user"
                                  ? "You"
                                  : "Study Assistant"}
                              </Text>

                              <Text
                                mt={4}
                                className={
                                  classes.answer
                                }
                              >
                                {
                                  message.content
                                }
                              </Text>

                              {message.sources
                                .length >
                                0 && (
                                <Group
                                  gap="xs"
                                  mt="sm"
                                >
                                  {message.sources.map(
                                    (source) => (
                                      <Badge
                                        key={[
                                          message.id,
                                          source.source_number,
                                          source.source_name,
                                          source.chunk_index,
                                        ].join(
                                          "-",
                                        )}
                                        variant="light"
                                        color="violet"
                                      >
                                        Source{" "}
                                        {
                                          source.source_number
                                        }
                                        :{" "}
                                        {
                                          source.source_name
                                        }
                                      </Badge>
                                    ),
                                  )}
                                </Group>
                              )}
                            </div>
                          </Group>
                        </Paper>
                      ),
                    )}
                  </Stack>
                )}
              </Stack>
            </Paper>
          )}

          <Paper
            component="section"
            withBorder
            radius="lg"
            p={{
              base: "md",
              sm: "xl",
            }}
            className={
              classes.questionCard
            }
          >
            <form onSubmit={handleSubmit}>
              <Stack gap="md">
                <div>
                  <Group
                    gap="xs"
                    mb={6}
                  >
                    <IconBulb
                      size={19}
                      stroke={1.8}
                    />

                    <Text fw={700}>
                      What would you like to
                      understand?
                    </Text>
                  </Group>

                  <Text
                    size="sm"
                    c="dimmed"
                  >
                    Ask a clear and specific
                    question for a more focused
                    answer.
                  </Text>
                </div>

                {filterOptions.loadError && (
                  <Alert
                    color="yellow"
                    variant="light"
                    title="Filters unavailable"
                    icon={
                      <IconAlertCircle
                        size={18}
                      />
                    }
                  >
                    {
                      filterOptions
                        .loadError
                    }
                  </Alert>
                )}

                <div>
                  <Text
                    fw={700}
                    size="sm"
                    mb={6}
                  >
                    Optional material scope
                  </Text>

                  <Text
                    size="sm"
                    c="dimmed"
                    mb="sm"
                  >
                    Leave both fields empty to
                    search across all ready
                    materials in your account.
                  </Text>

                  <SimpleGrid
                    cols={{
                      base: 1,
                      sm: 2,
                    }}
                    spacing="md"
                  >
                    <Select
                      label="Subject"
                      placeholder="All subjects"
                      data={
                        subjectSelectData
                      }
                      value={
                        selectedSubjectId
                      }
                      onChange={
                        handleSubjectChange
                      }
                      searchable
                      clearable
                      disabled={
                        isInteractionDisabled ||
                        subjectSelectData
                          .length === 0
                      }
                      nothingFoundMessage="No subjects found"
                    />

                    <Select
                      label="Study material"
                      placeholder="All ready materials"
                      data={
                        studyFileSelectData
                      }
                      value={
                        selectedStudyFileId
                      }
                      onChange={
                        handleStudyFileChange
                      }
                      searchable
                      clearable
                      disabled={
                        isInteractionDisabled ||
                        studyFileSelectData
                          .length === 0
                      }
                      nothingFoundMessage="No ready study materials found"
                    />
                  </SimpleGrid>

                  <Text
                    size="xs"
                    c="dimmed"
                    mt="xs"
                  >
                    Only study materials that
                    completed processing and
                    indexing are available.
                  </Text>
                </div>

                <Textarea
                  label="Your question"
                  placeholder="For example: What are the main ideas discussed in my uploaded notes?"
                  value={question}
                  onChange={(event) => {
                    setQuestion(
                      event.currentTarget
                        .value,
                    );
                  }}
                  disabled={
                    isInteractionDisabled
                  }
                  autosize
                  minRows={5}
                  maxRows={10}
                  required
                  aria-describedby="study-assistant-question-help"
                />

                <Text
                  id="study-assistant-question-help"
                  size="xs"
                  c="dimmed"
                >
                  The assistant will search only
                  the study materials available
                  to your authenticated account.
                </Text>

                <Group justify="flex-end">
                  <Button
                    type="submit"
                    loading={isLoading}
                    disabled={
                      isInteractionDisabled ||
                      !question.trim()
                    }
                    leftSection={
                      <IconSend size={18} />
                    }
                  >
                    Ask Study Assistant
                  </Button>
                </Group>
              </Stack>
            </form>
          </Paper>

          {state.status === "loading" && (
            <Paper
              component="section"
              withBorder
              radius="lg"
              p="xl"
              className={
                classes.resultCard
              }
              aria-live="polite"
            >
              <Group
                align="flex-start"
                wrap="nowrap"
              >
                <ThemeIcon
                  variant="light"
                  color="violet"
                  radius="md"
                >
                  <IconBook2 size={20} />
                </ThemeIcon>

                <div>
                  <Text fw={700}>
                    Searching your materials
                  </Text>

                  <Text
                    size="sm"
                    c="dimmed"
                    mt={4}
                  >
                    The Study Assistant is
                    finding relevant context and
                    preparing a grounded answer.
                  </Text>
                </div>
              </Group>
            </Paper>
          )}

          {state.status === "error" && (
            <Alert
              color="red"
              variant="light"
              title="The question could not be answered"
              icon={
                <IconAlertCircle
                  size={19}
                />
              }
              aria-live="assertive"
            >
              {state.message}
            </Alert>
          )}

          {state.status === "success" && (
            <Paper
              component="section"
              withBorder
              radius="lg"
              p={{
                base: "md",
                sm: "xl",
              }}
              className={
                classes.resultCard
              }
              aria-live="polite"
            >
              <Stack gap="lg">
                <Group
                  justify="space-between"
                  align="flex-start"
                >
                  <Group gap="sm">
                    <ThemeIcon
                      variant="light"
                      color={
                        state.result.outcome ===
                        "answered"
                          ? "violet"
                          : "yellow"
                      }
                      radius="md"
                    >
                      {state.result.outcome ===
                      "answered" ? (
                        <IconSparkles
                          size={20}
                        />
                      ) : (
                        <IconAlertCircle
                          size={20}
                        />
                      )}
                    </ThemeIcon>

                    <div>
                      <Text fw={750}>
                        {state.result.outcome ===
                        "answered"
                          ? "Grounded answer"
                          : "Not enough context"}
                      </Text>

                      <Text
                        size="xs"
                        c="dimmed"
                      >
                        {state.result
                          .context_available
                          ? `${state.result.retrieved_count} relevant section${
                              state.result
                                .retrieved_count ===
                              1
                                ? ""
                                : "s"
                            } retrieved`
                          : "No relevant uploaded context was found"}
                      </Text>
                    </div>
                  </Group>

                  <Badge
                    variant="light"
                    color={
                      state.result.outcome ===
                      "answered"
                        ? "green"
                        : "yellow"
                    }
                  >
                    {state.result.outcome ===
                    "answered"
                      ? "Answered"
                      : "No context"}
                  </Badge>
                </Group>

                <Text
                  className={
                    classes.answer
                  }
                >
                  {state.result.answer}
                </Text>

                {state.result.sources.length >
                  0 && (
                  <>
                    <Divider />

                    <section
                      aria-labelledby="study-assistant-sources-title"
                    >
                      <Group
                        justify="space-between"
                        align="flex-end"
                        mb="sm"
                      >
                        <div>
                          <Text
                            id="study-assistant-sources-title"
                            fw={700}
                          >
                            Sources used
                          </Text>

                          <Text
                            size="sm"
                            c="dimmed"
                          >
                            Relevant sections
                            retrieved from your
                            uploaded materials.
                          </Text>
                        </div>

                        <Badge
                          variant="light"
                          color="gray"
                        >
                          {
                            state.result
                              .source_count
                          }{" "}
                          source
                          {state.result
                            .source_count ===
                          1
                            ? ""
                            : "s"}
                        </Badge>
                      </Group>

                      <ol
                        className={
                          classes.sourceList
                        }
                      >
                        {state.result.sources.map(
                          (source) => (
                            <Paper
                              component="li"
                              key={[
                                source.source_number,
                                source.source_name,
                                source.chunk_index,
                              ].join("-")}
                              withBorder
                              radius="md"
                              p="md"
                              className={
                                classes.sourceCard
                              }
                            >
                              <Group
                                align="flex-start"
                                wrap="nowrap"
                              >
                                <ThemeIcon
                                  variant="light"
                                  color="violet"
                                  radius="md"
                                  className={
                                    classes.sourceIcon
                                  }
                                >
                                  <IconFileText
                                    size={19}
                                    stroke={1.8}
                                  />
                                </ThemeIcon>

                                <div
                                  className={
                                    classes.sourceDetails
                                  }
                                >
                                  <Group
                                    justify="space-between"
                                    align="flex-start"
                                    wrap="nowrap"
                                  >
                                    <div>
                                      <Text
                                        size="xs"
                                        c="dimmed"
                                        fw={700}
                                      >
                                        SOURCE{" "}
                                        {
                                          source.source_number
                                        }
                                      </Text>

                                      <Text
                                        fw={650}
                                        className={
                                          classes.sourceName
                                        }
                                      >
                                        {
                                          source.source_name
                                        }
                                      </Text>
                                    </div>

                                    <Badge
                                      size="sm"
                                      variant="light"
                                      color="violet"
                                    >
                                      {formatSimilarityScore(
                                        source.similarity_score,
                                      )}
                                    </Badge>
                                  </Group>

                                  <Text
                                    size="xs"
                                    c="dimmed"
                                    mt={5}
                                  >
                                    Material section{" "}
                                    {source.chunk_index +
                                      1}
                                  </Text>
                                </div>
                              </Group>
                            </Paper>
                          ),
                        )}
                      </ol>
                    </section>
                  </>
                )}
              </Stack>
            </Paper>
          )}
        </Stack>
      </Container>
    </main>
  );
}