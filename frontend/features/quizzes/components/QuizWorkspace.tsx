// File: /frontend/features/quizzes/components/QuizWorkspace.tsx
// Purpose: Combines Quiz generation, Quiz taking, and saved
// Quiz history inside one protected student workspace.

"use client";

import {
  Alert,
  Badge,
  Container,
  Group,
  Stack,
  Tabs,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconHistory,
  IconListCheck,
  IconPlus,
  IconSparkles,
} from "@tabler/icons-react";
import {
  useState,
} from "react";

import {
  QuizApiError,
} from "@/features/quizzes/api";
import {
  getSavedQuiz,
  listSavedQuizzes,
} from "@/features/quizzes/history-api";
import type {
  QuizFilterOptions,
  QuizResponse,
  QuizSummaryResponse,
} from "@/features/quizzes/types";

import {
  QuizGenerationForm,
} from "./QuizGenerationForm";
import {
  QuizHistoryPanel,
} from "./QuizHistoryPanel";
import {
  QuizPlayer,
} from "./QuizPlayer";

import classes from "./QuizWorkspace.module.css";


interface QuizWorkspaceProps {
  filterOptions:
    QuizFilterOptions;
}


type WorkspaceTab =
  | "create"
  | "history";


export function QuizWorkspace({
  filterOptions,
}: Readonly<
  QuizWorkspaceProps
>) {
  const [
    activeTab,
    setActiveTab,
  ] = useState<
    WorkspaceTab
  >(
    "create",
  );

  const [
    generatedQuiz,
    setGeneratedQuiz,
  ] = useState<
    QuizResponse | null
  >(
    null,
  );

  const [
    savedQuizzes,
    setSavedQuizzes,
  ] = useState<
    QuizSummaryResponse[]
  >(
    [],
  );

  const [
    historyLoading,
    setHistoryLoading,
  ] = useState(
    false,
  );

  const [
    historyLoaded,
    setHistoryLoaded,
  ] = useState(
    false,
  );

  const [
    historyError,
    setHistoryError,
  ] = useState<
    string | null
  >(
    null,
  );

  const [
    savedQuizOpenError,
    setSavedQuizOpenError,
  ] = useState<
    string | null
  >(
    null,
  );


  function handleGenerated(
    quiz: QuizResponse,
  ): void {
    setGeneratedQuiz(
      quiz,
    );

    setHistoryLoaded(
      false,
    );

    setSavedQuizOpenError(
      null,
    );
  }


  async function loadHistory():
  Promise<void> {
    if (historyLoading) {
      return;
    }

    setHistoryLoading(
      true,
    );

    setHistoryError(
      null,
    );

    try {
      const response =
        await listSavedQuizzes();

      setSavedQuizzes(
        response.items,
      );

      setHistoryLoaded(
        true,
      );
    } catch (error) {
      setHistoryError(
        error instanceof
          QuizApiError
          ? error.message
          : "Your saved Quizzes could not be loaded.",
      );
    } finally {
      setHistoryLoading(
        false,
      );
    }
  }


  async function handleTabChange(
    value: string | null,
  ): Promise<void> {
    if (
      value !== "create" &&
      value !== "history"
    ) {
      return;
    }

    setActiveTab(
      value,
    );

    if (
      value === "history" &&
      !historyLoaded
    ) {
      await loadHistory();
    }
  }


  async function handleOpenSavedQuiz(
    quizId: string,
  ): Promise<void> {
    setSavedQuizOpenError(
      null,
    );

    try {
      const quiz =
        await getSavedQuiz(
          quizId,
        );

      setGeneratedQuiz(
        quiz,
      );

      setActiveTab(
        "create",
      );
    } catch (error) {
      const message =
        error instanceof
          QuizApiError
          ? error.message
          : "The saved Quiz could not be opened.";

      setSavedQuizOpenError(
        message,
      );

      throw new Error(
        message,
      );
    }
  }


  return (
    <main
      className={
        classes.page
      }
    >
      <Container
        size="xl"
        className={
          classes.container
        }
      >
        <Stack
          gap="xl"
        >
          <header
            className={
              classes.header
            }
          >
            <Group
              gap="md"
              align="flex-start"
              wrap="nowrap"
            >
              <ThemeIcon
                size={52}
                radius="lg"
                variant="gradient"
                gradient={{
                  from:
                    "violet",
                  to:
                    "grape",
                }}
              >
                <IconListCheck
                  size={27}
                />
              </ThemeIcon>

              <div>
                <Group
                  gap="sm"
                >
                  <Title
                    order={1}
                  >
                    Quizzes
                  </Title>

                  <Badge
                    variant="light"
                    color="violet"
                    leftSection={
                      <IconSparkles
                        size={13}
                      />
                    }
                  >
                    AI-powered
                  </Badge>
                </Group>

                <Text
                  c="dimmed"
                  mt={5}
                  maw={720}
                >
                  Generate grounded
                  practice questions,
                  take Quizzes one
                  question at a time,
                  and revisit your
                  previous attempts.
                </Text>
              </div>
            </Group>
          </header>

          <Tabs
            value={
              activeTab
            }
            onChange={
              handleTabChange
            }
            keepMounted={
              false
            }
          >
            <Tabs.List>
              <Tabs.Tab
                value="create"
                leftSection={
                  <IconPlus
                    size={16}
                  />
                }
              >
                Create Quiz
              </Tabs.Tab>

              <Tabs.Tab
                value="history"
                leftSection={
                  <IconHistory
                    size={16}
                  />
                }
              >
                My Quizzes
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel
              value="create"
              pt="xl"
            >
              <Stack
                gap="xl"
              >
                {savedQuizOpenError && (
                  <Alert
                    color="red"
                    title="Saved Quiz unavailable"
                    icon={
                      <IconAlertCircle
                        size={18}
                      />
                    }
                  >
                    {
                      savedQuizOpenError
                    }
                  </Alert>
                )}

                <QuizGenerationForm
                  filterOptions={
                    filterOptions
                  }
                  onGenerated={
                    handleGenerated
                  }
                />

                {generatedQuiz && (
                  <section
                    className={
                      classes.resultRegion
                    }
                    aria-label="Generated Quiz"
                    aria-live="polite"
                  >
                    <QuizPlayer
                      key={
                        generatedQuiz.id
                      }
                      quiz={
                        generatedQuiz
                      }
                    />
                  </section>
                )}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel
              value="history"
              pt="xl"
            >
              <QuizHistoryPanel
                quizzes={
                  savedQuizzes
                }
                loading={
                  historyLoading
                }
                error={
                  historyError
                }
                onRefresh={
                  loadHistory
                }
                onTakeQuiz={
                  handleOpenSavedQuiz
                }
              />
            </Tabs.Panel>
          </Tabs>
        </Stack>
      </Container>
    </main>
  );
}