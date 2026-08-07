// File: /frontend/features/study-assistant/api.ts
// Purpose: Sends authenticated student questions to the
// protected FastAPI RAG answer endpoint.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";
import type {
  RagAnswerRequest,
  RagAnswerResponse,
  RagApiErrorResponse,
  RagSourceResponse,
} from "@/types/rag";

const RAG_ANSWER_API_PATH =
  "/api/rag/answer";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The Study Assistant could not answer your question.";

interface AskStudyAssistantOptions {
  signal?: AbortSignal;
}

export class StudyAssistantApiError
  extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);

    this.name = "StudyAssistantApiError";
    this.status = status;
    this.code = code;
  }
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

function getApiBaseUrl(): string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (!configuredUrl) {
    throw new StudyAssistantApiError(
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

function buildRagAnswerUrl(): string {
  const apiBaseUrl =
    getApiBaseUrl();

  /*
   * Support either of these configurations:
   *
   * http://localhost:8000
   * http://localhost:8000/api
   */
  if (apiBaseUrl.endsWith("/api")) {
    return [
      apiBaseUrl,
      "/rag/answer",
    ].join("");
  }

  return [
    apiBaseUrl,
    RAG_ANSWER_API_PATH,
  ].join("");
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
    typeof payload.code === "string"
  ) {
    return payload.code;
  }

  if (
    isRecord(payload.detail) &&
    typeof payload.detail.code ===
      "string"
  ) {
    return payload.detail.code;
  }

  return null;
}

function getErrorMessage(
  payload: unknown,
  status: number,
): string {
  if (isRecord(payload)) {
    const errorPayload: RagApiErrorResponse =
      payload;

    if (
      typeof errorPayload.message ===
      "string" &&
      errorPayload.message.trim()
    ) {
      return errorPayload.message;
    }

    if (
      typeof errorPayload.detail ===
        "string" &&
      errorPayload.detail.trim()
    ) {
      return errorPayload.detail;
    }

    if (
      isRecord(errorPayload.detail) &&
      typeof errorPayload.detail.message ===
        "string" &&
      errorPayload.detail.message.trim()
    ) {
      return errorPayload.detail.message;
    }
  }

  switch (status) {
    case 400:
      return (
        "The Study Assistant request was invalid."
      );

    case 401:
      return SESSION_EXPIRED_MESSAGE;

    case 422:
      return (
        "Check the question and selected filters."
      );

    case 500:
      return (
        "The Study Assistant returned an inconsistent response."
      );

    case 502:
      return (
        "The answer-generation service is temporarily unavailable."
      );

    case 503:
      return (
        "The study-material retrieval service is temporarily unavailable."
      );

    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}

function isRagSourceResponse(
  value: unknown,
): value is RagSourceResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.source_number ===
      "number" &&
    Number.isInteger(
      value.source_number,
    ) &&
    value.source_number > 0 &&
    typeof value.source_name ===
      "string" &&
    typeof value.chunk_index ===
      "number" &&
    Number.isInteger(
      value.chunk_index,
    ) &&
    value.chunk_index >= 0 &&
    typeof value.similarity_score ===
      "number" &&
    Number.isFinite(
      value.similarity_score,
    )
  );
}

function isRagAnswerResponse(
  value: unknown,
): value is RagAnswerResponse {
  if (!isRecord(value)) {
    return false;
  }

  const outcomeIsValid =
    value.outcome === "answered" ||
    value.outcome === "no_context";

  return (
    typeof value.conversation_id ===
      "string" &&
    value.conversation_id.trim()
      .length > 0 &&
    outcomeIsValid &&
    typeof value.answer === "string" &&
    Array.isArray(value.sources) &&
    value.sources.every(
      isRagSourceResponse,
    ) &&
    typeof value.retrieved_count ===
      "number" &&
    Number.isInteger(
      value.retrieved_count,
    ) &&
    value.retrieved_count >= 0 &&
    typeof value.source_count ===
      "number" &&
    Number.isInteger(
      value.source_count,
    ) &&
    value.source_count >= 0 &&
    typeof value.context_available ===
      "boolean"
  );
}

export async function askStudyAssistant(
  request: RagAnswerRequest,
  options: AskStudyAssistantOptions = {},
): Promise<RagAnswerResponse> {
  const supabase = createClient();

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
    throw new StudyAssistantApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  let response: Response;

  try {
    response = await fetch(
      buildRagAnswerUrl(),
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
          Authorization:
            `Bearer ${session.access_token}`,
        },

        body: JSON.stringify(request),
        cache: "no-store",
        signal: options.signal,
      },
    );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new StudyAssistantApiError(
      "The Study Assistant could not connect to the backend.",
      null,
      "RAG_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(response);

  if (!response.ok) {
    throw new StudyAssistantApiError(
      getErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      getErrorCode(payload),
    );
  }

  if (!isRagAnswerResponse(payload)) {
    throw new StudyAssistantApiError(
      "The Study Assistant returned an invalid response.",
      502,
      "INVALID_RAG_RESPONSE",
    );
  }

  return payload;
}