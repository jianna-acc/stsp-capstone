// File: /frontend/features/study-assistant/components/StudyAssistantWorkspace.tsx
// Purpose: Loads saved Study Assistant conversations,
// selected conversation messages, and the question workspace.

"use client";

import {
  Container,
} from "@mantine/core";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getStudyConversation,
  listStudyConversations,
  StudyConversationApiError,
} from "@/features/study-assistant/conversations-api";
import type {
  RagAnswerResponse,
  StudyAssistantFilterOptions,
} from "@/types/rag";
import type {
  StudyConversationDetailResponse,
  StudyConversationResponse,
} from "@/types/study-conversation";

import {
  ConversationHistoryPanel,
  type ConversationHistoryStatus,
} from "./ConversationHistoryPanel";
import {
  StudyAssistantPanel,
  type SelectedConversationStatus,
} from "./StudyAssistantPanel";
import classes from "./StudyAssistantWorkspace.module.css";

interface StudyAssistantWorkspaceProps {
  filterOptions: StudyAssistantFilterOptions;
}

const HISTORY_LOAD_ERROR =
  "Your saved conversations could not be loaded.";

const CONVERSATION_LOAD_ERROR =
  "The selected conversation could not be loaded.";

export function StudyAssistantWorkspace({
  filterOptions,
}: StudyAssistantWorkspaceProps) {
  const [
    conversations,
    setConversations,
  ] = useState<
    StudyConversationResponse[]
  >([]);

  const [
    selectedConversationId,
    setSelectedConversationId,
  ] = useState<string | null>(null);

  const [
    selectedConversation,
    setSelectedConversation,
  ] = useState<
    StudyConversationDetailResponse | null
  >(null);

  const [
    selectedConversationStatus,
    setSelectedConversationStatus,
  ] = useState<
    SelectedConversationStatus
  >("idle");

  const [
    selectedConversationError,
    setSelectedConversationError,
  ] = useState<string | null>(null);

  const [
    historyStatus,
    setHistoryStatus,
  ] = useState<
    ConversationHistoryStatus
  >("loading");

  const [
    historyError,
    setHistoryError,
  ] = useState<string | null>(null);

  const historyRequestRef =
    useRef<AbortController | null>(
      null,
    );

  const detailRequestRef =
    useRef<AbortController | null>(
      null,
    );

  const completeConversationHistoryRequest =
    useCallback(
      async (
        controller:
          AbortController,
      ): Promise<void> => {
        try {
          const response =
            await listStudyConversations({
              limit: 50,
              signal:
                controller.signal,
            });

          if (
            controller.signal.aborted
          ) {
            return;
          }

          setConversations(
            response.items,
          );

          setSelectedConversationId(
            (
              currentConversationId,
            ) => {
              if (
                !currentConversationId
              ) {
                return null;
              }

              const stillExists =
                response.items.some(
                  (conversation) =>
                    conversation.id ===
                    currentConversationId,
                );

              return stillExists
                ? currentConversationId
                : null;
            },
          );

          setHistoryError(null);
          setHistoryStatus("ready");
        } catch (error) {
          if (
            controller.signal.aborted ||
            (
              error instanceof
                DOMException &&
              error.name ===
                "AbortError"
            )
          ) {
            return;
          }

          const message =
            error instanceof
            StudyConversationApiError
              ? error.message
              : HISTORY_LOAD_ERROR;

          setConversations([]);
          setHistoryError(message);
          setHistoryStatus("error");
        } finally {
          if (
            historyRequestRef.current ===
            controller
          ) {
            historyRequestRef.current =
              null;
          }
        }
      },
      [],
    );

  const loadConversationHistory =
    useCallback((): void => {
      historyRequestRef.current?.abort();

      const controller =
        new AbortController();

      historyRequestRef.current =
        controller;

      setHistoryStatus("loading");
      setHistoryError(null);

      void completeConversationHistoryRequest(
        controller,
      );
    }, [
      completeConversationHistoryRequest,
    ]);

  const completeConversationDetailRequest =
    useCallback(
      async (
        conversationId: string,
        controller:
          AbortController,
      ): Promise<void> => {
        try {
          const response =
            await getStudyConversation(
              conversationId,
              {
                messageLimit: 500,
                signal:
                  controller.signal,
              },
            );

          if (
            controller.signal.aborted
          ) {
            return;
          }

          setSelectedConversation(
            response,
          );

          setSelectedConversationError(
            null,
          );

          setSelectedConversationStatus(
            "ready",
          );

          setConversations(
            (currentConversations) =>
              currentConversations.map(
                (conversation) =>
                  conversation.id ===
                  response.conversation.id
                    ? response.conversation
                    : conversation,
              ),
          );
        } catch (error) {
          if (
            controller.signal.aborted ||
            (
              error instanceof
                DOMException &&
              error.name ===
                "AbortError"
            )
          ) {
            return;
          }

          const message =
            error instanceof
            StudyConversationApiError
              ? error.message
              : CONVERSATION_LOAD_ERROR;

          setSelectedConversation(
            null,
          );

          setSelectedConversationError(
            message,
          );

          setSelectedConversationStatus(
            "error",
          );
        } finally {
          if (
            detailRequestRef.current ===
            controller
          ) {
            detailRequestRef.current =
              null;
          }
        }
      },
      [],
    );

  const loadSelectedConversation =
    useCallback(
      (
        conversationId: string,
      ): void => {
        detailRequestRef.current?.abort();

        const controller =
          new AbortController();

        detailRequestRef.current =
          controller;

        setSelectedConversationId(
          conversationId,
        );

        setSelectedConversation(
          null,
        );

        setSelectedConversationError(
          null,
        );

        setSelectedConversationStatus(
          "loading",
        );

        void completeConversationDetailRequest(
          conversationId,
          controller,
        );
      },
      [
        completeConversationDetailRequest,
      ],
    );

  useEffect(() => {
    const controller =
      new AbortController();

    historyRequestRef.current =
      controller;

    const requestTimer =
      window.setTimeout(() => {
        void completeConversationHistoryRequest(
          controller,
        );
      }, 0);

    return () => {
      window.clearTimeout(
        requestTimer,
      );

      controller.abort();
      detailRequestRef.current?.abort();

      if (
        historyRequestRef.current ===
        controller
      ) {
        historyRequestRef.current =
          null;
      }
    };
  }, [
    completeConversationHistoryRequest,
  ]);

  function handleStartNewConversation():
    void {
    detailRequestRef.current?.abort();
    detailRequestRef.current = null;

    setSelectedConversationId(null);
    setSelectedConversation(null);
    setSelectedConversationError(null);

    setSelectedConversationStatus(
      "idle",
    );
  }

  function handleRetrySelectedConversation():
    void {
    if (!selectedConversationId) {
      return;
    }

    loadSelectedConversation(
      selectedConversationId,
    );
  }

  const handleAnswerCompleted =
    useCallback(
      (
        result:
          RagAnswerResponse,
      ): void => {
        loadSelectedConversation(
          result.conversation_id,
        );

        loadConversationHistory();
      },
      [
        loadConversationHistory,
        loadSelectedConversation,
      ],
    );

  const assistantPanelKey = [
    selectedConversationId ??
      "new-conversation",

    selectedConversationStatus,

    selectedConversation
      ?.conversation.updated_at ??
      "no-detail",
  ].join(":");

  return (
    <div className={classes.page}>
      <Container
        size="xl"
        className={classes.container}
      >
        <div
          className={classes.workspace}
        >
          <div
            className={
              classes.historyColumn
            }
          >
            <ConversationHistoryPanel
              conversations={
                conversations
              }
              selectedConversationId={
                selectedConversationId
              }
              status={
                historyStatus
              }
              errorMessage={
                historyError
              }
              disabled={
                selectedConversationStatus ===
                "loading"
              }
              onSelectConversation={
                loadSelectedConversation
              }
              onStartNewConversation={
                handleStartNewConversation
              }
              onRetry={
                loadConversationHistory
              }
            />
          </div>

          <div
            className={
              classes.assistantColumn
            }
          >
            <StudyAssistantPanel
              key={assistantPanelKey}
              filterOptions={
                filterOptions
              }
              conversationDetail={
                selectedConversation
              }
              conversationStatus={
                selectedConversationStatus
              }
              conversationError={
                selectedConversationError
              }
              onRetryConversation={
                handleRetrySelectedConversation
              }
              onAnswerCompleted={
                handleAnswerCompleted
              }
            />
          </div>
        </div>
      </Container>
    </div>
  );
}
