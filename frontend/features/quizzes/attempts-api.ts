// File: /frontend/features/quizzes/attempts-api.ts
// Purpose: Sends authenticated Quiz-attempt requests for
// starting attempts, submitting answers, and loading results.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import {
  QuizApiError,
} from "./api";
import type {
  QuizAnswerFeedbackResponse,
  QuizAnswerSubmissionResponse,
  QuizAttemptResponse,
  QuizAttemptResultResponse,
  QuizAttemptStatus,
  QuizTopicResult,
} from "./types";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

interface RequestOptions {
  signal?: AbortSignal;
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function isNonEmptyString(
  value: unknown,
): value is string {
  return (
    typeof value === "string" &&
    value.trim().length > 0
  );
}

function isNullableString(
  value: unknown,
): value is string | null {
  return (
    value === null ||
    typeof value === "string"
  );
}

function isIntegerAtLeast(
  value: unknown,
  minimum: number,
): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= minimum
  );
}

function isPercentage(
  value: unknown,
): value is number {
  return (
    typeof value === "number" &&
    value >= 0 &&
    value <= 100
  );
}

function isAttemptStatus(
  value: unknown,
): value is QuizAttemptStatus {
  return (
    value === "in_progress" ||
    value === "completed"
  );
}

function getApiBaseUrl(): string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (!configuredUrl) {
    throw new QuizApiError(
      "The backend API address is not configured.",
      null,
      "API_BASE_URL_NOT_CONFIGURED",
    );
  }

  return configuredUrl.replace(
    /\/+$/,
    "",
  );
}

function buildApiUrl(
  path: string,
): string {
  const apiBaseUrl =
    getApiBaseUrl();

  if (
    apiBaseUrl.endsWith(
      "/api",
    )
  ) {
    return [
      apiBaseUrl,
      path,
    ].join("");
  }

  return [
    apiBaseUrl,
    "/api",
    path,
  ].join("");
}

async function getAccessToken():
Promise<string> {
  const supabase =
    createClient();

  const {
    data: {
      session,
    },
    error,
  } = await supabase.auth.getSession();

  if (
    error ||
    !session?.access_token
  ) {
    throw new QuizApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  return session.access_token;
}

async function readJsonResponse(
  response: Response,
): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function getErrorCode(
  payload: unknown,
): string | null {
  if (!isRecord(payload)) {
    return null;
  }

  if (
    typeof payload.error_code ===
    "string"
  ) {
    return payload.error_code;
  }

  if (
    isRecord(payload.detail) &&
    typeof payload.detail.error_code ===
      "string"
  ) {
    return payload.detail.error_code;
  }

  return null;
}

function getErrorMessage(
  payload: unknown,
  status: number,
): string {
  if (
    isRecord(payload)
  ) {
    if (
      isNonEmptyString(
        payload.message,
      )
    ) {
      return payload.message;
    }

    if (
      typeof payload.detail ===
        "string" &&
      payload.detail.trim()
    ) {
      return payload.detail;
    }

    if (
      isRecord(
        payload.detail,
      ) &&
      isNonEmptyString(
        payload.detail.message,
      )
    ) {
      return payload.detail.message;
    }
  }

  if (status === 401) {
    return SESSION_EXPIRED_MESSAGE;
  }

  if (status === 404) {
    return (
      "The requested Quiz or Quiz attempt could not be found."
    );
  }

  if (status === 409) {
    return (
      "The Quiz attempt is no longer in the required state."
    );
  }

  if (status === 503) {
    return (
      "Quiz-attempt storage is temporarily unavailable."
    );
  }

  return (
    "The Quiz attempt could not be completed."
  );
}

function isQuizAttemptResponse(
  value: unknown,
): value is QuizAttemptResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.id,
    ) &&
    isNonEmptyString(
      value.quiz_id,
    ) &&
    isAttemptStatus(
      value.status,
    ) &&
    isIntegerAtLeast(
      value.current_position,
      1,
    ) &&
    isIntegerAtLeast(
      value.correct_count,
      0,
    ) &&
    isIntegerAtLeast(
      value.question_count,
      1,
    ) &&
    value.question_count <= 50 &&
    isPercentage(
      value.score_percentage,
    ) &&
    isNonEmptyString(
      value.started_at,
    ) &&
    isNullableString(
      value.completed_at,
    ) &&
    isNonEmptyString(
      value.created_at,
    ) &&
    isNonEmptyString(
      value.updated_at,
    )
  );
}

function isQuizAnswerFeedback(
  value: unknown,
): value is QuizAnswerFeedbackResponse {
  if (!isRecord(value)) {
    return false;
  }

  const validNextPosition =
    value.next_position === null ||
    isIntegerAtLeast(
      value.next_position,
      1,
    );

  return (
    isNonEmptyString(
      value.attempt_id,
    ) &&
    isNonEmptyString(
      value.quiz_question_id,
    ) &&
    isIntegerAtLeast(
      value.position,
      1,
    ) &&
    typeof value.is_correct ===
      "boolean" &&
    isNonEmptyString(
      value.correct_answer,
    ) &&
    isNonEmptyString(
      value.explanation,
    ) &&
    validNextPosition &&
    typeof value.attempt_completed ===
      "boolean"
  );
}

function isQuizAnswerSubmissionResponse(
  value: unknown,
): value is QuizAnswerSubmissionResponse {
  if (!isRecord(value)) {
    return false;
  }

  if (
    !isQuizAttemptResponse(
      value.attempt,
    ) ||
    !isQuizAnswerFeedback(
      value.feedback,
    )
  ) {
    return false;
  }

  return (
    value.attempt.id ===
    value.feedback.attempt_id
  );
}

function isQuizTopicResult(
  value: unknown,
): value is QuizTopicResult {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.topic,
    ) &&
    isIntegerAtLeast(
      value.correct_count,
      0,
    ) &&
    isIntegerAtLeast(
      value.question_count,
      1,
    ) &&
    isPercentage(
      value.accuracy_percentage,
    )
  );
}

function isQuizAttemptResult(
  value: unknown,
): value is QuizAttemptResultResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.attempt_id,
    ) &&
    isNonEmptyString(
      value.quiz_id,
    ) &&
    isIntegerAtLeast(
      value.correct_count,
      0,
    ) &&
    isIntegerAtLeast(
      value.question_count,
      1,
    ) &&
    isPercentage(
      value.score_percentage,
    ) &&
    Array.isArray(
      value.strong_topics,
    ) &&
    value.strong_topics.every(
      isQuizTopicResult,
    ) &&
    Array.isArray(
      value.weak_topics,
    ) &&
    value.weak_topics.every(
      isQuizTopicResult,
    ) &&
    isNonEmptyString(
      value.completed_at,
    )
  );
}

async function executeRequest(
  url: string,
  init: RequestInit,
): Promise<{
  response: Response;
  payload: unknown;
}> {
  let response: Response;

  try {
    response =
      await fetch(
        url,
        init,
      );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name ===
        "AbortError"
    ) {
      throw error;
    }

    throw new QuizApiError(
      "The Quiz could not connect to the backend.",
      null,
      "QUIZ_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(
      response,
    );

  if (!response.ok) {
    throw new QuizApiError(
      getErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      getErrorCode(
        payload,
      ),
    );
  }

  return {
    response,
    payload,
  };
}

export async function startQuizAttempt(
  quizId: string,
  options: RequestOptions = {},
): Promise<QuizAttemptResponse> {
  const normalizedQuizId =
    quizId.trim();

  if (!normalizedQuizId) {
    throw new QuizApiError(
      "A Quiz must be selected before starting.",
      400,
      "QUIZ_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    buildApiUrl(
      `/quizzes/${encodeURIComponent(
        normalizedQuizId,
      )}/attempts`,
    ),
    {
      method:
        "POST",

      headers: {
        Authorization:
          `Bearer ${accessToken}`,
      },

      cache:
        "no-store",

      signal:
        options.signal,
    },
  );

  if (
    !isQuizAttemptResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz attempt service returned an invalid response.",
      502,
      "INVALID_QUIZ_ATTEMPT_RESPONSE",
    );
  }

  return payload;
}

export async function getQuizAttempt(
  attemptId: string,
  options: RequestOptions = {},
): Promise<QuizAttemptResponse> {
  const normalizedAttemptId =
    attemptId.trim();

  if (!normalizedAttemptId) {
    throw new QuizApiError(
      "A Quiz attempt must be selected.",
      400,
      "QUIZ_ATTEMPT_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    buildApiUrl(
      `/quiz-attempts/${encodeURIComponent(
        normalizedAttemptId,
      )}`,
    ),
    {
      method:
        "GET",

      headers: {
        Authorization:
          `Bearer ${accessToken}`,
      },

      cache:
        "no-store",

      signal:
        options.signal,
    },
  );

  if (
    !isQuizAttemptResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz attempt service returned an invalid response.",
      502,
      "INVALID_QUIZ_ATTEMPT_RESPONSE",
    );
  }

  return payload;
}

export async function submitQuizAnswer(
  attemptId: string,
  position: number,
  answer: string,
  options: RequestOptions = {},
): Promise<QuizAnswerSubmissionResponse> {
  const normalizedAttemptId =
    attemptId.trim();

  const normalizedAnswer =
    answer.trim();

  if (!normalizedAttemptId) {
    throw new QuizApiError(
      "A Quiz attempt must be selected.",
      400,
      "QUIZ_ATTEMPT_ID_REQUIRED",
    );
  }

  if (
    !Number.isInteger(
      position,
    ) ||
    position < 1
  ) {
    throw new QuizApiError(
      "The Quiz question position is invalid.",
      400,
      "QUIZ_POSITION_INVALID",
    );
  }

  if (!normalizedAnswer) {
    throw new QuizApiError(
      "Enter or select an answer before submitting.",
      400,
      "QUIZ_ANSWER_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    buildApiUrl(
      [
        "/quiz-attempts/",
        encodeURIComponent(
          normalizedAttemptId,
        ),
        "/questions/",
        String(position),
        "/answer",
      ].join(""),
    ),
    {
      method:
        "POST",

      headers: {
        "Content-Type":
          "application/json",

        Authorization:
          `Bearer ${accessToken}`,
      },

      body:
        JSON.stringify({
          answer:
            normalizedAnswer,
        }),

      cache:
        "no-store",

      signal:
        options.signal,
    },
  );

  if (
    !isQuizAnswerSubmissionResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz answer service returned an invalid response.",
      502,
      "INVALID_QUIZ_ANSWER_RESPONSE",
    );
  }

  return payload;
}

export async function getQuizAttemptResult(
  attemptId: string,
  options: RequestOptions = {},
): Promise<QuizAttemptResultResponse> {
  const normalizedAttemptId =
    attemptId.trim();

  if (!normalizedAttemptId) {
    throw new QuizApiError(
      "A Quiz attempt must be selected.",
      400,
      "QUIZ_ATTEMPT_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    buildApiUrl(
      `/quiz-attempts/${encodeURIComponent(
        normalizedAttemptId,
      )}/result`,
    ),
    {
      method:
        "GET",

      headers: {
        Authorization:
          `Bearer ${accessToken}`,
      },

      cache:
        "no-store",

      signal:
        options.signal,
    },
  );

  if (
    !isQuizAttemptResult(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz result service returned an invalid response.",
      502,
      "INVALID_QUIZ_RESULT_RESPONSE",
    );
  }

  return payload;
}