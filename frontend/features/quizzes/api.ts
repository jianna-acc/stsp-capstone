// File: /frontend/features/quizzes/api.ts
// Purpose: Sends authenticated Quiz-generation requests
// to the protected FastAPI Quiz endpoint.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import type {
  QuizDifficulty,
  QuizGenerateRequest,
  QuizQuestionResponse,
  QuizQuestionType,
  QuizResponse,
  QuizScopeType,
  QuizType,
} from "./types";

const QUIZ_GENERATE_API_PATH =
  "/api/quizzes/generate";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The Quiz could not be generated.";

interface GenerateQuizOptions {
  signal?: AbortSignal;
}

export class QuizApiError extends Error {
  readonly status:
    number | null;

  readonly code:
    string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(
      message,
    );

    this.name =
      "QuizApiError";

    this.status =
      status;

    this.code =
      code;
  }
}

function isRecord(
  value: unknown,
): value is Record<
  string,
  unknown
> {
  return (
    typeof value ===
      "object" &&
    value !== null &&
    !Array.isArray(
      value,
    )
  );
}

function isNonEmptyString(
  value: unknown,
): value is string {
  return (
    typeof value ===
      "string" &&
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

function isStringArray(
  value: unknown,
): value is string[] {
  return (
    Array.isArray(
      value,
    ) &&
    value.every(
      (
        item,
      ) =>
        isNonEmptyString(
          item,
        ),
    )
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
    value ===
      "multiple_choice" ||
    value ===
      "true_false" ||
    value ===
      "identification" ||
    value ===
      "mixed"
  );
}

function isQuizQuestionType(
  value: unknown,
): value is QuizQuestionType {
  return (
    value ===
      "multiple_choice" ||
    value ===
      "true_false" ||
    value ===
      "identification"
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

function buildQuizGenerateUrl():
string {
  const apiBaseUrl =
    getApiBaseUrl();

  if (
    apiBaseUrl.endsWith(
      "/api",
    )
  ) {
    return [
      apiBaseUrl,
      "/quizzes/generate",
    ].join(
      "",
    );
  }

  return [
    apiBaseUrl,
    QUIZ_GENERATE_API_PATH,
  ].join(
    "",
  );
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
  if (
    !isRecord(
      payload,
    )
  ) {
    return null;
  }

  if (
    typeof payload.error_code ===
      "string"
  ) {
    return payload.error_code;
  }

  if (
    typeof payload.code ===
      "string"
  ) {
    return payload.code;
  }

  if (
    isRecord(
      payload.detail,
    )
  ) {
    if (
      typeof payload.detail
        .error_code ===
        "string"
    ) {
      return payload.detail
        .error_code;
    }

    if (
      typeof payload.detail
        .code ===
        "string"
    ) {
      return payload.detail
        .code;
    }
  }

  return null;
}

function getErrorMessage(
  payload: unknown,
  status: number,
): string {
  if (
    isRecord(
      payload,
    )
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
      return payload.detail
        .message;
    }

    if (
      Array.isArray(
        payload.detail,
      )
    ) {
      return (
        "Check the Quiz generation options."
      );
    }
  }

  if (status === 401) {
    return SESSION_EXPIRED_MESSAGE;
  }

  if (status === 404) {
    return (
      "The selected subject or study material could not be found."
    );
  }

  if (status === 409) {
    return (
      "The selected study material is not ready for Quiz generation."
    );
  }

  if (status === 502) {
    return (
      "The Quiz-generation service is temporarily unavailable."
    );
  }

  if (status === 503) {
    return (
      "Quiz storage or study-material loading is temporarily unavailable."
    );
  }

  return DEFAULT_ERROR_MESSAGE;
}

function isQuizQuestionResponse(
  value: unknown,
): value is QuizQuestionResponse {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  return (
    isNonEmptyString(
      value.id,
    ) &&
    typeof value.position ===
      "number" &&
    Number.isInteger(
      value.position,
    ) &&
    value.position >= 1 &&
    isQuizQuestionType(
      value.question_type,
    ) &&
    isNonEmptyString(
      value.topic,
    ) &&
    isNonEmptyString(
      value.question,
    ) &&
    isStringArray(
      value.choices,
    )
  );
}

function isQuizResponse(
  value: unknown,
): value is QuizResponse {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  if (
    !isNonEmptyString(
      value.id,
    ) ||
    !isNonEmptyString(
      value.subject_id,
    ) ||
    !isNullableString(
      value.study_file_id,
    ) ||
    !isQuizScopeType(
      value.scope_type,
    ) ||
    !isNonEmptyString(
      value.title,
    ) ||
    !isQuizType(
      value.quiz_type,
    ) ||
    !isQuizDifficulty(
      value.difficulty,
    ) ||
    typeof value.question_count !==
      "number" ||
    !Number.isInteger(
      value.question_count,
    ) ||
    value.question_count < 1 ||
    value.question_count > 50 ||
    !Array.isArray(
      value.questions,
    ) ||
    !isNonEmptyString(
      value.generation_model,
    ) ||
    typeof value.generation_count !==
      "number" ||
    !Number.isInteger(
      value.generation_count,
    ) ||
    value.generation_count < 1 ||
    !isNonEmptyString(
      value.generated_at,
    ) ||
    !isNonEmptyString(
      value.created_at,
    ) ||
    !isNonEmptyString(
      value.updated_at,
    )
  ) {
    return false;
  }

  if (
    value.questions.length !==
      value.question_count
  ) {
    return false;
  }

  if (
    value.scope_type ===
      "file" &&
    !isNonEmptyString(
      value.study_file_id,
    )
  ) {
    return false;
  }

  if (
    value.scope_type ===
      "subject" &&
    value.study_file_id !== null
  ) {
    return false;
  }

  for (
    let index = 0;
    index <
    value.questions.length;
    index += 1
  ) {
    const question =
      value.questions[
        index
      ];

    if (
      !isQuizQuestionResponse(
        question,
      ) ||
      question.position !==
        index + 1
    ) {
      return false;
    }
  }

  return true;
}

export async function generateQuiz(
  request: QuizGenerateRequest,
  options: GenerateQuizOptions = {},
): Promise<QuizResponse> {
  const supabase =
    createClient();

  const {
    data: {
      session,
    },
    error: sessionError,
  } = await supabase.auth.getSession();

  if (
    sessionError ||
    !session?.access_token
  ) {
    throw new QuizApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  let response:
    Response;

  try {
    response =
      await fetch(
        buildQuizGenerateUrl(),
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${session.access_token}`,
          },

          body:
            JSON.stringify(
              request,
            ),

          cache:
            "no-store",

          signal:
            options.signal,
        },
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
      "The Quiz could not connect to the backend.",
      null,
      "QUIZ_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(
      response,
    );

  if (
    !response.ok
  ) {
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

  if (
    !isQuizResponse(
      payload,
    )
  ) {
    throw new QuizApiError(
      "The Quiz service returned an invalid response.",
      502,
      "INVALID_QUIZ_RESPONSE",
    );
  }

  return payload;
}