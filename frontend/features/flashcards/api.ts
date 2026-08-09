// File: /frontend/features/flashcards/api.ts
// Purpose: Sends authenticated Flashcard generation and saved-deck
// requests to the protected FastAPI Flashcard endpoints.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import type {
  FlashcardApiErrorResponse,
  FlashcardDeckResponse,
  FlashcardDeckSummary,
  FlashcardGenerateRequest,
  FlashcardItem,
  FlashcardListResponse,
  FlashcardLocatorType,
  FlashcardScopeType,
  FlashcardSource,
} from "./types";

const FLASHCARD_API_PATH =
  "/api/flashcards";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The Flashcard request could not be completed.";

interface FlashcardRequestOptions {
  signal?: AbortSignal;
}

export class FlashcardApiError extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);

    this.name = "FlashcardApiError";
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
    throw new FlashcardApiError(
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

function buildFlashcardBaseUrl():
  string {
  const apiBaseUrl =
    getApiBaseUrl();

  if (apiBaseUrl.endsWith("/api")) {
    return [
      apiBaseUrl,
      "/flashcards",
    ].join("");
  }

  return [
    apiBaseUrl,
    FLASHCARD_API_PATH,
  ].join("");
}

function buildFlashcardGenerateUrl():
  string {
  return [
    buildFlashcardBaseUrl(),
    "/generate",
  ].join("");
}

function buildFlashcardDeckUrl(
  deckId: string,
): string {
  return [
    buildFlashcardBaseUrl(),
    "/",
    encodeURIComponent(
      deckId,
    ),
  ].join("");
}

async function getAccessToken():
    Promise<string> {
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
        throw new FlashcardApiError(
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
      FlashcardApiErrorResponse =
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
        "Check the Flashcard options."
      );

    case 401:
      return SESSION_EXPIRED_MESSAGE;

    case 404:
      return (
        "The requested Flashcard deck or study material could not be found."
      );

    case 409:
      return (
        "The selected study material is not ready for Flashcard generation."
      );

    case 500:
      return (
        "The generated Flashcards could not be processed."
      );

    case 502:
      return (
        "The Flashcard generation service is temporarily unavailable."
      );

    case 503:
      return (
        "Flashcard storage or study-material loading is temporarily unavailable."
      );

    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}

function isFlashcardScopeType(
  value: unknown,
): value is FlashcardScopeType {
  return (
    value === "subject" ||
    value === "file"
  );
}

function isFlashcardLocatorType(
  value: unknown,
): value is FlashcardLocatorType {
  return (
    value === "page" ||
    value === "slide" ||
    value === "sheet" ||
    value === "section" ||
    value === "document"
  );
}

function isFlashcardItem(
  value: unknown,
): value is FlashcardItem {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.question,
    ) &&
    isNonEmptyString(
      value.answer,
    )
  );
}

function isFlashcardSource(
  value: unknown,
): value is FlashcardSource {
  if (!isRecord(value)) {
    return false;
  }

  const locatorTypeIsValid =
    value.locator_type === null ||
    isFlashcardLocatorType(
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

function isPositiveInteger(
  value: unknown,
): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 1
  );
}

function hasValidSharedDeckFields(
  value: Record<string, unknown>,
): boolean {
  if (
    !isFlashcardScopeType(
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
    isPositiveInteger(
      value.requested_card_count,
    ) &&
    isNonEmptyString(
      value.generation_model,
    ) &&
    isPositiveInteger(
      value.generation_count,
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

function isFlashcardDeckResponse(
  value: unknown,
): value is FlashcardDeckResponse {
  if (
    !isRecord(value) ||
    !hasValidSharedDeckFields(
      value,
    )
  ) {
    return false;
  }

  return (
    Array.isArray(value.cards) &&
    value.cards.length >= 1 &&
    value.cards.every(
      isFlashcardItem,
    ) &&
    Array.isArray(value.sources) &&
    value.sources.every(
      isFlashcardSource,
    )
  );
}

function isFlashcardDeckSummary(
  value: unknown,
): value is FlashcardDeckSummary {
  return (
    isRecord(value) &&
    hasValidSharedDeckFields(
      value,
    )
  );
}

function isFlashcardListResponse(
  value: unknown,
): value is FlashcardListResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    Array.isArray(value.items) &&
    value.items.every(
      isFlashcardDeckSummary,
    )
  );
}

async function performJsonRequest(
  url: string,
  requestInit: RequestInit,
): Promise<unknown> {
  let response: Response;

  try {
    response = await fetch(
      url,
      requestInit,
    );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new FlashcardApiError(
      "Flashcards could not connect to the backend.",
      null,
      "FLASHCARD_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(
      response,
    );

  if (!response.ok) {
    throw new FlashcardApiError(
      getErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      getErrorCode(payload),
    );
  }

  return payload;
}

export async function generateFlashcards(
  request: FlashcardGenerateRequest,
  options: FlashcardRequestOptions = {},
): Promise<FlashcardDeckResponse> {
  const accessToken =
    await getAccessToken();

  const payload =
    await performJsonRequest(
      buildFlashcardGenerateUrl(),
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${accessToken}`,
        },

        body: JSON.stringify(
          request,
        ),

        cache: "no-store",
        signal: options.signal,
      },
    );

  if (
    !isFlashcardDeckResponse(
      payload,
    )
  ) {
    throw new FlashcardApiError(
      "The Flashcard service returned an invalid response.",
      502,
      "INVALID_FLASHCARD_RESPONSE",
    );
  }

  return payload;
}

export async function listFlashcardDecks(
  subjectId?: string,
  options: FlashcardRequestOptions = {},
): Promise<FlashcardListResponse> {
  const accessToken =
    await getAccessToken();

  const normalizedSubjectId =
    subjectId?.trim();

  const query =
    normalizedSubjectId
      ? [
          "?subject_id=",
          encodeURIComponent(
            normalizedSubjectId,
          ),
        ].join("")
      : "";

  const payload =
    await performJsonRequest(
      [
        buildFlashcardBaseUrl(),
        query,
      ].join(""),
      {
        method: "GET",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },

        cache: "no-store",
        signal: options.signal,
      },
    );

  if (
    !isFlashcardListResponse(
      payload,
    )
  ) {
    throw new FlashcardApiError(
      "The Flashcard service returned an invalid saved-deck list.",
      502,
      "INVALID_FLASHCARD_LIST_RESPONSE",
    );
  }

  return payload;
}

export async function getFlashcardDeck(
  deckId: string,
  options: FlashcardRequestOptions = {},
): Promise<FlashcardDeckResponse> {
  const normalizedDeckId =
    deckId.trim();

  if (!normalizedDeckId) {
    throw new FlashcardApiError(
      "A Flashcard deck must be selected.",
      400,
      "FLASHCARD_DECK_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  const payload =
    await performJsonRequest(
      buildFlashcardDeckUrl(
        normalizedDeckId,
      ),
      {
        method: "GET",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },

        cache: "no-store",
        signal: options.signal,
      },
    );

  if (
    !isFlashcardDeckResponse(
      payload,
    )
  ) {
    throw new FlashcardApiError(
      "The Flashcard service returned an invalid response.",
      502,
      "INVALID_FLASHCARD_RESPONSE",
    );
  }

  return payload;
}

export async function deleteFlashcardDeck(
  deckId: string,
  options: FlashcardRequestOptions = {},
): Promise<void> {
  const normalizedDeckId =
    deckId.trim();

  if (!normalizedDeckId) {
    throw new FlashcardApiError(
      "A Flashcard deck must be selected.",
      400,
      "FLASHCARD_DECK_ID_REQUIRED",
    );
  }

  const accessToken =
    await getAccessToken();

  let response: Response;

  try {
    response = await fetch(
      buildFlashcardDeckUrl(
        normalizedDeckId,
      ),
      {
        method: "DELETE",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
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

    throw new FlashcardApiError(
      "Flashcards could not connect to the backend.",
      null,
      "FLASHCARD_API_UNREACHABLE",
    );
  }

  if (response.ok) {
    return;
  }

  const payload =
    await readJsonResponse(
      response,
    );

  throw new FlashcardApiError(
    getErrorMessage(
      payload,
      response.status,
    ),
    response.status,
    getErrorCode(payload),
  );
}