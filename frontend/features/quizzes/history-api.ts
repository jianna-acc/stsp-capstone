// File: /frontend/features/quizzes/history-api.ts
// Purpose: Loads saved Quizzes, Quiz attempt history,
// completed-attempt reviews, and performs Quiz deletion.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import {
  QuizApiError,
} from "./api";

import type {
  QuizAttemptListResponse,
  QuizAttemptResponse,
  QuizAttemptResultResponse,
  QuizAttemptReviewAnswerResponse,
  QuizAttemptReviewResponse,
  QuizDifficulty,
  QuizListResponse,
  QuizQuestionResponse,
  QuizQuestionType,
  QuizResponse,
  QuizScopeType,
  QuizSummaryResponse,
  QuizTopicResult,
  QuizType,
} from "./types";


const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The saved Quiz operation could not be completed.";


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


function isQuizScopeType(
  value: unknown,
): value is QuizScopeType {
  return (
    value === "subject" ||
    value === "file"
  );
}


function isQuizType(
  value: unknown,
): value is QuizType {
  return (
    value === "multiple_choice" ||
    value === "true_false" ||
    value === "identification" ||
    value === "mixed"
  );
}


function isQuizQuestionType(
  value: unknown,
): value is QuizQuestionType {
  return (
    value === "multiple_choice" ||
    value === "true_false" ||
    value === "identification"
  );
}


function isQuizDifficulty(
  value: unknown,
): value is QuizDifficulty {
  return (
    value === "easy" ||
    value === "medium" ||
    value === "hard"
  );
}


function isQuizAttemptStatus(
  value: unknown,
): value is "in_progress" | "completed" {
  return (
    value === "in_progress" ||
    value === "completed"
  );
}


function isQuizQuestionResponse(
  value: unknown,
): value is QuizQuestionResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.id,
    ) &&
    isIntegerAtLeast(
      value.position,
      1,
    ) &&
    isQuizQuestionType(
      value.question_type,
    ) &&
    isNonEmptyString(
      value.topic,
    ) &&
    isNonEmptyString(
      value.question,
    ) &&
    Array.isArray(
      value.choices,
    ) &&
    value.choices.every(
      isNonEmptyString,
    )
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
    isQuizAttemptStatus(
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


function isQuizResult(
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


function isQuizSummary(
  value: unknown,
): value is QuizSummaryResponse {
  if (!isRecord(value)) {
    return false;
  }

  const latestAttempt =
    value.latest_attempt;

  return (
    isNonEmptyString(
      value.id,
    ) &&
    isNonEmptyString(
      value.subject_id,
    ) &&
    isNullableString(
      value.study_file_id,
    ) &&
    isQuizScopeType(
      value.scope_type,
    ) &&
    isNonEmptyString(
      value.title,
    ) &&
    isQuizType(
      value.quiz_type,
    ) &&
    isQuizDifficulty(
      value.difficulty,
    ) &&
    isIntegerAtLeast(
      value.question_count,
      1,
    ) &&
    value.question_count <= 50 &&
    isIntegerAtLeast(
      value.attempt_count,
      0,
    ) &&
    (
      latestAttempt === null ||
      isQuizAttemptResponse(
        latestAttempt,
      )
    ) &&
    isNonEmptyString(
      value.generated_at,
    ) &&
    isNonEmptyString(
      value.created_at,
    ) &&
    isNonEmptyString(
      value.updated_at,
    )
  );
}


function isQuizListResponse(
  value: unknown,
): value is QuizListResponse {
  return (
    isRecord(
      value,
    ) &&
    Array.isArray(
      value.items,
    ) &&
    value.items.every(
      isQuizSummary,
    )
  );
}


function isQuizAttemptListResponse(
  value: unknown,
): value is QuizAttemptListResponse {
  return (
    isRecord(
      value,
    ) &&
    isNonEmptyString(
      value.quiz_id,
    ) &&
    Array.isArray(
      value.items,
    ) &&
    value.items.every(
      isQuizAttemptResponse,
    )
  );
}


function isQuizResponse(
  value: unknown,
): value is QuizResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.id,
    ) &&
    isNonEmptyString(
      value.subject_id,
    ) &&
    isNullableString(
      value.study_file_id,
    ) &&
    isQuizScopeType(
      value.scope_type,
    ) &&
    isNonEmptyString(
      value.title,
    ) &&
    isQuizType(
      value.quiz_type,
    ) &&
    isQuizDifficulty(
      value.difficulty,
    ) &&
    isIntegerAtLeast(
      value.question_count,
      1,
    ) &&
    Array.isArray(
      value.questions,
    ) &&
    value.questions.length ===
      value.question_count &&
    value.questions.every(
      isQuizQuestionResponse,
    ) &&
    isNonEmptyString(
      value.generation_model,
    ) &&
    isIntegerAtLeast(
      value.generation_count,
      1,
    ) &&
    isNonEmptyString(
      value.generated_at,
    ) &&
    isNonEmptyString(
      value.created_at,
    ) &&
    isNonEmptyString(
      value.updated_at,
    )
  );
}


function isReviewAnswer(
  value: unknown,
): value is QuizAttemptReviewAnswerResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.answer_id,
    ) &&
    isQuizQuestionResponse(
      value.question,
    ) &&
    isNonEmptyString(
      value.submitted_answer,
    ) &&
    typeof value.is_correct ===
      "boolean" &&
    isNonEmptyString(
      value.correct_answer,
    ) &&
    isNonEmptyString(
      value.explanation,
    ) &&
    isNonEmptyString(
      value.answered_at,
    )
  );
}


function isQuizAttemptReviewResponse(
  value: unknown,
): value is QuizAttemptReviewResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isQuizAttemptResponse(
      value.attempt,
    ) &&
    Array.isArray(
      value.answers,
    ) &&
    value.answers.every(
      isReviewAnswer,
    ) &&
    isQuizResult(
      value.result,
    )
  );
}


function getApiBaseUrl():
string {
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
    isRecord(
      payload.detail,
    ) &&
    typeof payload.detail
      .error_code === "string"
  ) {
    return payload.detail
      .error_code;
  }

  return null;
}


function getErrorMessage(
  payload: unknown,
  status: number,
): string {
  if (isRecord(payload)) {
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
      "The requested Quiz or attempt could not be found."
    );
  }

  if (status === 409) {
    return (
      "This Quiz attempt cannot be reviewed until it is completed."
    );
  }

  if (status === 503) {
    return (
      "Saved Quiz storage is temporarily unavailable."
    );
  }

  return DEFAULT_ERROR_MESSAGE;
}


async function executeRequest(
  path: string,
  init: RequestInit,
): Promise<{
  response: Response;
  payload: unknown;
}> {
  let response:
    Response;

  try {
    response =
      await fetch(
        buildApiUrl(
          path,
        ),
        init,
      );
  } catch (error) {
    if (
      error instanceof
        DOMException &&
      error.name ===
        "AbortError"
    ) {
      throw error;
    }

    throw new QuizApiError(
      "The saved Quiz service could not connect to the backend.",
      null,
      "QUIZ_API_UNREACHABLE",
    );
  }

  const payload =
    response.status === 204
      ? null
      : await readJsonResponse(
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


export async function listSavedQuizzes(
  options: RequestOptions = {},
): Promise<QuizListResponse> {
  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    "/quizzes",
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
    !isQuizListResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The saved Quiz service returned an invalid response.",
      502,
      "INVALID_QUIZ_LIST_RESPONSE",
    );
  }

  return payload;
}


export async function getSavedQuiz(
  quizId: string,
  options: RequestOptions = {},
): Promise<QuizResponse> {
  const normalizedQuizId =
    quizId.trim();

  if (!normalizedQuizId) {
    throw new QuizApiError(
      "A Quiz must be selected.",
      400,
      "QUIZ_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    `/quizzes/${encodeURIComponent(
      normalizedQuizId,
    )}`,
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
    !isQuizResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The saved Quiz service returned an invalid Quiz.",
      502,
      "INVALID_QUIZ_RESPONSE",
    );
  }

  return payload;
}


export async function deleteSavedQuiz(
  quizId: string,
  options: RequestOptions = {},
): Promise<void> {
  const normalizedQuizId =
    quizId.trim();

  if (!normalizedQuizId) {
    throw new QuizApiError(
      "A Quiz must be selected before deletion.",
      400,
      "QUIZ_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  await executeRequest(
    `/quizzes/${encodeURIComponent(
      normalizedQuizId,
    )}`,
    {
      method:
        "DELETE",

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
}


export async function listQuizAttempts(
  quizId: string,
  options: RequestOptions = {},
): Promise<QuizAttemptListResponse> {
  const normalizedQuizId =
    quizId.trim();

  if (!normalizedQuizId) {
    throw new QuizApiError(
      "A Quiz must be selected.",
      400,
      "QUIZ_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const {
    payload,
  } = await executeRequest(
    `/quizzes/${encodeURIComponent(
      normalizedQuizId,
    )}/attempts`,
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
    !isQuizAttemptListResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz-attempt history service returned an invalid response.",
      502,
      "INVALID_QUIZ_ATTEMPT_LIST_RESPONSE",
    );
  }

  return payload;
}


export async function getQuizAttemptReview(
  attemptId: string,
  options: RequestOptions = {},
): Promise<QuizAttemptReviewResponse> {
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
    `/quiz-attempts/${encodeURIComponent(
      normalizedAttemptId,
    )}/review`,
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
    !isQuizAttemptReviewResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz-review service returned an invalid response.",
      502,
      "INVALID_QUIZ_REVIEW_RESPONSE",
    );
  }

  return payload;
}