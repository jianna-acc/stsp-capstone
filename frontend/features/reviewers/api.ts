// File: /frontend/features/reviewers/api.ts
// Purpose: Sends authenticated reviewer-generation requests
// to the protected FastAPI reviewer endpoint.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import type {
  ReviewerApiErrorResponse,
  ReviewerContent,
  ReviewerDefinition,
  ReviewerGenerateRequest,
  ReviewerLength,
  ReviewerLocatorType,
  ReviewerResponse,
  ReviewerScopeType,
  ReviewerSource,
  ReviewerTopic,
} from "./types";

const REVIEWER_GENERATE_API_PATH =
  "/api/reviewers/generate";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The reviewer could not be generated.";

interface GenerateReviewerOptions {
  signal?: AbortSignal;
}

interface RegenerateReviewerOptions {
  signal?: AbortSignal;
}

export class ReviewerApiError extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);

    this.name = "ReviewerApiError";
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

function isNonEmptyString(
  value: unknown,
): value is string {
  return (
    typeof value === "string" &&
    value.trim().length > 0
  );
}

function getApiBaseUrl(): string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (!configuredUrl) {
    throw new ReviewerApiError(
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

function buildReviewerGenerateUrl():
  string {
  const apiBaseUrl =
    getApiBaseUrl();

  /*
   * Support either:
   *
   * http://localhost:8000
   * http://localhost:8000/api
   */
  if (apiBaseUrl.endsWith("/api")) {
    return [
      apiBaseUrl,
      "/reviewers/generate",
    ].join("");
  }

  return [
    apiBaseUrl,
    REVIEWER_GENERATE_API_PATH,
  ].join("");
}

function buildReviewerRegenerateUrl(
  reviewerId: string,
): string {
  const apiBaseUrl =
    getApiBaseUrl();

  const encodedReviewerId =
    encodeURIComponent(
      reviewerId,
    );

  if (apiBaseUrl.endsWith("/api")) {
    return [
      apiBaseUrl,
      "/reviewers/",
      encodedReviewerId,
      "/regenerate",
    ].join("");
  }

  return [
    apiBaseUrl,
    "/api/reviewers/",
    encodedReviewerId,
    "/regenerate",
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
    typeof payload.error_code ===
    "string"
  ) {
    return payload.error_code;
  }

  if (
    typeof payload.code === "string"
  ) {
    return payload.code;
  }

  if (isRecord(payload.detail)) {
    if (
      typeof payload.detail
        .error_code === "string"
    ) {
      return payload.detail.error_code;
    }

    if (
      typeof payload.detail.code ===
      "string"
    ) {
      return payload.detail.code;
    }
  }

  return null;
}

function getErrorMessage(
  payload: unknown,
  status: number,
): string {
  if (isRecord(payload)) {
    const errorPayload:
      ReviewerApiErrorResponse =
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
      typeof errorPayload.detail
        .message === "string" &&
      errorPayload.detail.message.trim()
    ) {
      return errorPayload.detail.message;
    }
  }

  switch (status) {
    case 400:
      return (
        "Check the reviewer generation options."
      );

    case 401:
      return SESSION_EXPIRED_MESSAGE;

    case 404:
      return (
        "The selected study material could not be found."
      );

    case 409:
      return (
        "The selected study material is not ready for reviewer generation."
      );

    case 500:
      return (
        "The generated reviewer could not be processed."
      );

    case 502:
      return (
        "The reviewer-generation service is temporarily unavailable."
      );

    case 503:
      return (
        "Reviewer storage or study-material loading is temporarily unavailable."
      );

    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}

function isReviewerScopeType(
  value: unknown,
): value is ReviewerScopeType {
  return (
    value === "subject" ||
    value === "file"
  );
}

function isReviewerLength(
  value: unknown,
): value is ReviewerLength {
  return (
    value === "short" ||
    value === "medium" ||
    value === "long"
  );
}

function isReviewerLocatorType(
  value: unknown,
): value is ReviewerLocatorType {
  return (
    value === "page" ||
    value === "slide" ||
    value === "sheet" ||
    value === "section" ||
    value === "document"
  );
}

function isReviewerDefinition(
  value: unknown,
): value is ReviewerDefinition {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.term) &&
    isNonEmptyString(
      value.definition,
    )
  );
}

function isReviewerTopic(
  value: unknown,
): value is ReviewerTopic {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.title) &&
    isNonEmptyString(value.summary) &&
    Array.isArray(
      value.key_points,
    ) &&
    value.key_points.length > 0 &&
    value.key_points.every(
      isNonEmptyString,
    ) &&
    Array.isArray(
      value.definitions,
    ) &&
    value.definitions.every(
      isReviewerDefinition,
    )
  );
}

function isReviewerContent(
  value: unknown,
): value is ReviewerContent {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.overview,
    ) &&
    Array.isArray(value.topics) &&
    value.topics.length > 0 &&
    value.topics.every(
      isReviewerTopic,
    )
  );
}

function isReviewerSource(
  value: unknown,
): value is ReviewerSource {
  if (!isRecord(value)) {
    return false;
  }

  const locatorTypeIsValid =
    value.locator_type === null ||
    isReviewerLocatorType(
      value.locator_type,
    );

  const locatorLabelIsValid =
    value.locator_label === null ||
    typeof value.locator_label ===
      "string";

  return (
    isNonEmptyString(
      value.study_file_id,
    ) &&
    isNonEmptyString(
      value.source_name,
    ) &&
    typeof value.chunk_index ===
      "number" &&
    Number.isInteger(
      value.chunk_index,
    ) &&
    value.chunk_index >= 0 &&
    locatorTypeIsValid &&
    locatorLabelIsValid
  );
}

function isReviewerResponse(
  value: unknown,
): value is ReviewerResponse {
  if (!isRecord(value)) {
    return false;
  }

  if (
    !isReviewerScopeType(
      value.scope_type,
    )
  ) {
    return false;
  }

  const studyFileIdIsValid =
    value.scope_type === "subject"
      ? value.study_file_id === null
      : isNonEmptyString(
          value.study_file_id,
        );

  return (
    isNonEmptyString(value.id) &&
    isNonEmptyString(
      value.subject_id,
    ) &&
    studyFileIdIsValid &&
    isNonEmptyString(value.title) &&
    isReviewerLength(
      value.reviewer_length,
    ) &&
    isReviewerContent(
      value.content,
    ) &&
    Array.isArray(value.sources) &&
    value.sources.every(
      isReviewerSource,
    ) &&
    isNonEmptyString(
      value.generation_model,
    ) &&
    typeof value.generation_count ===
      "number" &&
    Number.isInteger(
      value.generation_count,
    ) &&
    value.generation_count >= 1 &&
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

export async function generateReviewer(
  request: ReviewerGenerateRequest,
  options: GenerateReviewerOptions = {},
): Promise<ReviewerResponse> {
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
    throw new ReviewerApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  let response: Response;

  try {
    response = await fetch(
      buildReviewerGenerateUrl(),
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${session.access_token}`,
        },

        body: JSON.stringify(
          request,
        ),

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

    throw new ReviewerApiError(
      "The reviewer could not connect to the backend.",
      null,
      "REVIEWER_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(
      response,
    );

  if (!response.ok) {
    throw new ReviewerApiError(
      getErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      getErrorCode(payload),
    );
  }

  if (
    !isReviewerResponse(payload)
  ) {
    throw new ReviewerApiError(
      "The reviewer service returned an invalid response.",
      502,
      "INVALID_REVIEWER_RESPONSE",
    );
  }

  return payload;
}

export async function regenerateReviewer(
  reviewerId: string,
  options: RegenerateReviewerOptions = {},
): Promise<ReviewerResponse> {
  const normalizedReviewerId =
    reviewerId.trim();

  if (!normalizedReviewerId) {
    throw new ReviewerApiError(
      "A reviewer must be selected before regeneration.",
      400,
      "REVIEWER_ID_REQUIRED",
    );
  }

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
    throw new ReviewerApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  let response: Response;

  try {
    response = await fetch(
      buildReviewerRegenerateUrl(
        normalizedReviewerId,
      ),
      {
        method: "POST",

        headers: {
          Authorization:
            `Bearer ${session.access_token}`,
        },

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

    throw new ReviewerApiError(
      "The reviewer could not connect to the backend.",
      null,
      "REVIEWER_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(
      response,
    );

  if (!response.ok) {
    throw new ReviewerApiError(
      getErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      getErrorCode(payload),
    );
  }

  if (
    !isReviewerResponse(payload)
  ) {
    throw new ReviewerApiError(
      "The reviewer service returned an invalid response.",
      502,
      "INVALID_REVIEWER_RESPONSE",
    );
  }

  return payload;
}