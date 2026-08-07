// File: /frontend/features/study-assistant/conversations-api.ts
// Purpose: Loads, renames, and deletes authenticated saved
// Study Assistant conversations through the FastAPI backend.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";
import type {
  StudyConversationApiErrorResponse,
  StudyConversationDetailResponse,
  StudyConversationListResponse,
  StudyConversationResponse,
  StudyMessageResponse,
} from "@/types/study-conversation";

const STUDY_CONVERSATIONS_API_PATH =
  "/api/study-conversations";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The saved conversation request could not be completed.";

interface ConversationRequestOptions {
  signal?: AbortSignal;
}

interface ListConversationOptions
  extends ConversationRequestOptions {
  limit?: number;
}

interface GetConversationOptions
  extends ConversationRequestOptions {
  messageLimit?: number;
}

export class StudyConversationApiError
  extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);

    this.name =
      "StudyConversationApiError";

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

function isNullableString(
  value: unknown,
): value is string | null {
  return (
    value === null ||
    typeof value === "string"
  );
}

function isTimestamp(
  value: unknown,
): value is string {
  return (
    typeof value === "string" &&
    value.trim().length > 0 &&
    Number.isFinite(
      Date.parse(value),
    )
  );
}

function getApiBaseUrl(): string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (!configuredUrl) {
    throw new StudyConversationApiError(
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

function buildConversationApiUrl(
  suffix = "",
): string {
  const apiBaseUrl =
    getApiBaseUrl();

  const normalizedSuffix =
    suffix.startsWith("/")
      ? suffix
      : suffix
        ? `/${suffix}`
        : "";

  if (apiBaseUrl.endsWith("/api")) {
    return [
      apiBaseUrl,
      "/study-conversations",
      normalizedSuffix,
    ].join("");
  }

  return [
    apiBaseUrl,
    STUDY_CONVERSATIONS_API_PATH,
    normalizedSuffix,
  ].join("");
}

function normalizeConversationId(
  conversationId: string,
): string {
  const normalizedId =
    conversationId.trim();

  if (!normalizedId) {
    throw new StudyConversationApiError(
      "A saved conversation must be selected.",
      400,
      "INVALID_CONVERSATION_ID",
    );
  }

  return normalizedId;
}

function normalizeConversationTitle(
  title: string,
): string {
  const normalizedTitle =
    title.trim();

  if (!normalizedTitle) {
    throw new StudyConversationApiError(
      "The conversation title must not be empty.",
      400,
      "INVALID_CONVERSATION_TITLE",
    );
  }

  if (normalizedTitle.length > 120) {
    throw new StudyConversationApiError(
      "The conversation title must not exceed 120 characters.",
      400,
      "INVALID_CONVERSATION_TITLE",
    );
  }

  return normalizedTitle;
}

function validateIntegerRange(
  value: number,
  minimum: number,
  maximum: number,
  fieldName: string,
): number {
  if (
    !Number.isInteger(value) ||
    value < minimum ||
    value > maximum
  ) {
    throw new StudyConversationApiError(
      `${fieldName} must be between ${minimum} and ${maximum}.`,
      400,
      "INVALID_CONVERSATION_LIMIT",
    );
  }

  return value;
}

async function getAccessToken():
  Promise<string> {
  const supabase = createClient();

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
    throw new StudyConversationApiError(
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

  const errorPayload:
    StudyConversationApiErrorResponse =
      payload;

  if (
    typeof errorPayload.error_code ===
      "string"
  ) {
    return errorPayload.error_code;
  }

  if (
    typeof errorPayload.code ===
      "string"
  ) {
    return errorPayload.code;
  }

  if (
    isRecord(errorPayload.detail)
  ) {
    if (
      typeof errorPayload.detail
        .error_code === "string"
    ) {
      return errorPayload.detail
        .error_code;
    }

    if (
      typeof errorPayload.detail.code ===
        "string"
    ) {
      return errorPayload.detail.code;
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
      StudyConversationApiErrorResponse =
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
        "The saved-conversation request was invalid."
      );

    case 401:
      return SESSION_EXPIRED_MESSAGE;

    case 404:
      return (
        "The requested conversation was not found."
      );

    case 422:
      return (
        "The saved-conversation request contains invalid information."
      );

    case 500:
      return (
        "The saved conversation could not be processed."
      );

    case 503:
      return (
        "Conversation storage is temporarily unavailable."
      );

    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}

async function sendAuthenticatedRequest(
  url: string,
  requestInit: RequestInit,
): Promise<Response> {
  const accessToken =
    await getAccessToken();

  const headers =
    new Headers(
      requestInit.headers,
    );

  headers.set(
    "Accept",
    "application/json",
  );

  try {
    return await fetch(
      url,
      {
        ...requestInit,
        headers: {
          ...Object.fromEntries(
            headers.entries(),
          ),
          Authorization:
            `Bearer ${accessToken}`,
        },
        cache: "no-store",
      },
    );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new StudyConversationApiError(
      "The Study Assistant could not connect to conversation storage.",
      null,
      "CONVERSATION_API_UNREACHABLE",
    );
  }
}

async function requireSuccessfulJson(
  response: Response,
): Promise<unknown> {
  const payload =
    await readJsonResponse(response);

  if (!response.ok) {
    throw new StudyConversationApiError(
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

function isSourceResponse(
  value: unknown,
): boolean {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.source_number ===
      "number" &&
    Number.isInteger(
      value.source_number,
    ) &&
    value.source_number >= 1 &&
    isNonEmptyString(
      value.source_name,
    ) &&
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
    ) &&
    value.similarity_score >= 0 &&
    value.similarity_score <= 1
  );
}

function isConversationResponse(
  value: unknown,
): value is StudyConversationResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.id) &&
    isNonEmptyString(value.title) &&
    isNullableString(
      value.subject_id,
    ) &&
    isNullableString(
      value.study_file_id,
    ) &&
    isTimestamp(
      value.created_at,
    ) &&
    isTimestamp(
      value.updated_at,
    ) &&
    isTimestamp(
      value.last_message_at,
    )
  );
}

function isMessageResponse(
  value: unknown,
): value is StudyMessageResponse {
  if (!isRecord(value)) {
    return false;
  }

  const roleIsValid =
    value.role === "user" ||
    value.role === "assistant";

  const outcomeIsValid =
    value.outcome === null ||
    value.outcome === "answered" ||
    value.outcome === "no_context";

  if (
    !isNonEmptyString(value.id) ||
    !isNonEmptyString(
      value.conversation_id,
    ) ||
    !roleIsValid ||
    !isNonEmptyString(value.content) ||
    !outcomeIsValid ||
    !Array.isArray(value.sources) ||
    !value.sources.every(
      isSourceResponse,
    ) ||
    !isTimestamp(value.created_at)
  ) {
    return false;
  }

  if (
    value.role === "user"
  ) {
    return (
      value.outcome === null &&
      value.sources.length === 0
    );
  }

  return value.outcome !== null;
}

function isConversationListResponse(
  value: unknown,
): value is StudyConversationListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(
      isConversationResponse,
    )
  );
}

function isConversationDetailResponse(
  value: unknown,
): value is StudyConversationDetailResponse {
  if (!isRecord(value)) {
    return false;
  }

  const conversation =
    value.conversation;

  const messages =
    value.messages;

  if (
    !isConversationResponse(
      conversation,
    ) ||
    !Array.isArray(messages) ||
    !messages.every(
      isMessageResponse,
    )
  ) {
    return false;
  }

  return messages.every(
    (message) =>
      message.conversation_id ===
      conversation.id,
  );
}

export async function listStudyConversations(
  options: ListConversationOptions = {},
): Promise<StudyConversationListResponse> {
  const searchParameters =
    new URLSearchParams();

  if (options.limit !== undefined) {
    searchParameters.set(
      "limit",
      String(
        validateIntegerRange(
          options.limit,
          1,
          50,
          "Conversation limit",
        ),
      ),
    );
  }

  const query =
    searchParameters.size > 0
      ? `?${searchParameters.toString()}`
      : "";

  const response =
    await sendAuthenticatedRequest(
      `${buildConversationApiUrl()}${query}`,
      {
        method: "GET",
        signal: options.signal,
      },
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isConversationListResponse(
      payload,
    )
  ) {
    throw new StudyConversationApiError(
      "The conversation list response was invalid.",
      502,
      "INVALID_CONVERSATION_LIST_RESPONSE",
    );
  }

  return payload;
}

export async function getStudyConversation(
  conversationId: string,
  options: GetConversationOptions = {},
): Promise<StudyConversationDetailResponse> {
  const normalizedId =
    normalizeConversationId(
      conversationId,
    );

  const searchParameters =
    new URLSearchParams();

  if (
    options.messageLimit !==
    undefined
  ) {
    searchParameters.set(
      "message_limit",
      String(
        validateIntegerRange(
          options.messageLimit,
          1,
          500,
          "Message limit",
        ),
      ),
    );
  }

  const query =
    searchParameters.size > 0
      ? `?${searchParameters.toString()}`
      : "";

  const response =
    await sendAuthenticatedRequest(
      [
        buildConversationApiUrl(
          encodeURIComponent(
            normalizedId,
          ),
        ),
        query,
      ].join(""),
      {
        method: "GET",
        signal: options.signal,
      },
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isConversationDetailResponse(
      payload,
    )
  ) {
    throw new StudyConversationApiError(
      "The conversation detail response was invalid.",
      502,
      "INVALID_CONVERSATION_DETAIL_RESPONSE",
    );
  }

  return payload;
}

export async function renameStudyConversation(
  conversationId: string,
  title: string,
  options: ConversationRequestOptions = {},
): Promise<StudyConversationResponse> {
  const normalizedId =
    normalizeConversationId(
      conversationId,
    );

  const normalizedTitle =
    normalizeConversationTitle(
      title,
    );

  const response =
    await sendAuthenticatedRequest(
      buildConversationApiUrl(
        encodeURIComponent(
          normalizedId,
        ),
      ),
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          title: normalizedTitle,
        }),

        signal: options.signal,
      },
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isConversationResponse(
      payload,
    )
  ) {
    throw new StudyConversationApiError(
      "The renamed conversation response was invalid.",
      502,
      "INVALID_CONVERSATION_RESPONSE",
    );
  }

  return payload;
}

export async function deleteStudyConversation(
  conversationId: string,
  options: ConversationRequestOptions = {},
): Promise<void> {
  const normalizedId =
    normalizeConversationId(
      conversationId,
    );

  const response =
    await sendAuthenticatedRequest(
      buildConversationApiUrl(
        encodeURIComponent(
          normalizedId,
        ),
      ),
      {
        method: "DELETE",
        signal: options.signal,
      },
    );

  if (!response.ok) {
    const payload =
      await readJsonResponse(
        response,
      );

    throw new StudyConversationApiError(
      getErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      getErrorCode(payload),
    );
  }

  if (
    response.status !== 204
  ) {
    throw new StudyConversationApiError(
      "The conversation deletion response was invalid.",
      502,
      "INVALID_CONVERSATION_DELETE_RESPONSE",
    );
  }
}
