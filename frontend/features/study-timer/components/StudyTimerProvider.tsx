// File: /frontend/features/study-timer/components/StudyTimerProvider.tsx
// Purpose: Owns durable Study Activity timer state across
// authenticated route navigation.

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type {
  ReactNode,
} from "react";

import {
  endStudyActivity,
  endStudyActivityBreak,
  getActiveStudyActivity,
  pauseStudyActivity,
  resumeStudyActivity,
  startStudyActivity,
  startStudyActivityBreak,
} from "../api";
import type {
  StudyActivity,
} from "../types";


type StudyTimerAction =
  | "starting"
  | "pausing"
  | "resuming"
  | "starting_break"
  | "ending_break"
  | "ending"
  | null;


interface StartFreeStudyInput {
  subjectId: string;
  title: string;
  studyPlanId?: string | null;
}


interface StudyTimerContextValue {
  activity:
    StudyActivity | null;

  initializing:
    boolean;

  pendingAction:
    StudyTimerAction;

  error:
    string | null;

  refreshActive:
    () => Promise<void>;

  startFromStudySession:
    (
      studySessionId: string,
    ) => Promise<StudyActivity>;

  startFreeStudy:
    (
      input:
        StartFreeStudyInput,
    ) => Promise<StudyActivity>;

  pause:
    () => Promise<void>;

  resume:
    () => Promise<void>;

  startBreak:
    () => Promise<void>;

  endBreak:
    () => Promise<void>;

  endSession:
    () => Promise<void>;

  clearError:
    () => void;
}


const StudyTimerContext =
  createContext<
    StudyTimerContextValue | null
  >(
    null,
  );


function getErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (
    error instanceof Error &&
    error.message.trim()
  ) {
    return error.message;
  }

  return fallback;
}


function isAbortError(
  error: unknown,
): boolean {
  return (
    error instanceof DOMException &&
    error.name === "AbortError"
  );
}


interface StudyTimerProviderProps {
  children: ReactNode;
}


export function StudyTimerProvider({
  children,
}: StudyTimerProviderProps) {
  const [
    activity,
    setActivity,
  ] = useState<
    StudyActivity | null
  >(
    null,
  );

  const [
    initializing,
    setInitializing,
  ] = useState(
    true,
  );

  const [
    pendingAction,
    setPendingAction,
  ] = useState<
    StudyTimerAction
  >(
    null,
  );

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(
    null,
  );


  const refreshActive =
    useCallback(
      async () => {
        setError(
          null,
        );

        try {
          const current =
            await getActiveStudyActivity();

          setActivity(
            current,
          );
        } catch (
          loadError
        ) {
          setError(
            getErrorMessage(
              loadError,
              "Your active study timer could not be loaded.",
            ),
          );
        }
      },
      [],
    );


  useEffect(
    () => {
      const controller =
        new AbortController();

      async function loadInitialTimer() {
        setInitializing(
          true,
        );

        setError(
          null,
        );

        try {
          const current =
            await getActiveStudyActivity(
              {
                signal:
                  controller.signal,
              },
            );

          setActivity(
            current,
          );
        } catch (
          loadError
        ) {
          if (
            isAbortError(
              loadError,
            )
          ) {
            return;
          }

          setError(
            getErrorMessage(
              loadError,
              "Your active study timer could not be loaded.",
            ),
          );
        } finally {
          if (
            !controller.signal.aborted
          ) {
            setInitializing(
              false,
            );
          }
        }
      }

      void loadInitialTimer();

      return () => {
        controller.abort();
      };
    },
    [],
  );


  const startFromStudySession =
    useCallback(
      async (
        studySessionId: string,
      ): Promise<StudyActivity> => {
        setPendingAction(
          "starting",
        );

        setError(
          null,
        );

        try {
          const started =
            await startStudyActivity(
              {
                study_session_id:
                  studySessionId,
              },
            );

          setActivity(
            started,
          );

          return started;
        } catch (
          startError
        ) {
          const message =
            getErrorMessage(
              startError,
              "The study timer could not be started.",
            );

          setError(
            message,
          );

          throw startError;
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [],
    );


  const startFreeStudy =
    useCallback(
      async (
        input:
          StartFreeStudyInput,
      ): Promise<StudyActivity> => {
        setPendingAction(
          "starting",
        );

        setError(
          null,
        );

        try {
          const started =
            await startStudyActivity(
              {
                subject_id:
                  input.subjectId,
                title:
                  input.title,
                study_plan_id:
                  input.studyPlanId ??
                  null,
              },
            );

          setActivity(
            started,
          );

          return started;
        } catch (
          startError
        ) {
          const message =
            getErrorMessage(
              startError,
              "The study timer could not be started.",
            );

          setError(
            message,
          );

          throw startError;
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [],
    );


  const pause =
    useCallback(
      async () => {
        if (
          !activity
        ) {
          return;
        }

        setPendingAction(
          "pausing",
        );

        setError(
          null,
        );

        try {
          const updated =
            await pauseStudyActivity(
              activity.id,
            );

          setActivity(
            updated,
          );
        } catch (
          actionError
        ) {
          setError(
            getErrorMessage(
              actionError,
              "The study timer could not be paused.",
            ),
          );
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [
        activity,
      ],
    );


  const resume =
    useCallback(
      async () => {
        if (
          !activity
        ) {
          return;
        }

        setPendingAction(
          "resuming",
        );

        setError(
          null,
        );

        try {
          const updated =
            await resumeStudyActivity(
              activity.id,
            );

          setActivity(
            updated,
          );
        } catch (
          actionError
        ) {
          setError(
            getErrorMessage(
              actionError,
              "The study timer could not be resumed.",
            ),
          );
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [
        activity,
      ],
    );


  const startBreak =
    useCallback(
      async () => {
        if (
          !activity
        ) {
          return;
        }

        setPendingAction(
          "starting_break",
        );

        setError(
          null,
        );

        try {
          const updated =
            await startStudyActivityBreak(
              activity.id,
            );

          setActivity(
            updated,
          );
        } catch (
          actionError
        ) {
          setError(
            getErrorMessage(
              actionError,
              "The study break could not be started.",
            ),
          );
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [
        activity,
      ],
    );


  const endBreak =
    useCallback(
      async () => {
        if (
          !activity
        ) {
          return;
        }

        setPendingAction(
          "ending_break",
        );

        setError(
          null,
        );

        try {
          const updated =
            await endStudyActivityBreak(
              activity.id,
            );

          setActivity(
            updated,
          );
        } catch (
          actionError
        ) {
          setError(
            getErrorMessage(
              actionError,
              "The study break could not be ended.",
            ),
          );
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [
        activity,
      ],
    );


  const endSession =
    useCallback(
      async () => {
        if (
          !activity
        ) {
          return;
        }

        setPendingAction(
          "ending",
        );

        setError(
          null,
        );

        try {
          const completed =
            await endStudyActivity(
              activity.id,
            );

          if (
            completed.status ===
            "completed"
          ) {
            setActivity(
              null,
            );
          } else {
            setActivity(
              completed,
            );
          }
        } catch (
          actionError
        ) {
          setError(
            getErrorMessage(
              actionError,
              "The study session could not be ended.",
            ),
          );
        } finally {
          setPendingAction(
            null,
          );
        }
      },
      [
        activity,
      ],
    );


  const clearError =
    useCallback(
      () => {
        setError(
          null,
        );
      },
      [],
    );


  const value =
    useMemo<
      StudyTimerContextValue
    >(
      () => ({
        activity,
        initializing,
        pendingAction,
        error,
        refreshActive,
        startFromStudySession,
        startFreeStudy,
        pause,
        resume,
        startBreak,
        endBreak,
        endSession,
        clearError,
      }),
      [
        activity,
        initializing,
        pendingAction,
        error,
        refreshActive,
        startFromStudySession,
        startFreeStudy,
        pause,
        resume,
        startBreak,
        endBreak,
        endSession,
        clearError,
      ],
    );


  return (
    <StudyTimerContext.Provider
      value={
        value
      }
    >
      {children}
    </StudyTimerContext.Provider>
  );
}


export function useStudyTimer():
  StudyTimerContextValue {
  const context =
    useContext(
      StudyTimerContext,
    );

  if (
    context === null
  ) {
    throw new Error(
      "useStudyTimer must be used inside StudyTimerProvider.",
    );
  }

  return context;
}