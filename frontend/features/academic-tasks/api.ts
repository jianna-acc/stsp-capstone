// File: /frontend/features/academic-tasks/api.ts
// Purpose: Sends authenticated Academic Task CRUD and
// deterministic priority requests to the protected FastAPI API.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import type {
  AcademicTaskApiErrorResponse,
  AcademicTaskCreateRequest,
  AcademicTaskDifficulty,
  AcademicTaskListOptions,
  AcademicTaskListResponse,
  AcademicTaskOutputType,
  AcademicTaskPriorityBreakdown,
  AcademicTaskPriorityListResponse,
  AcademicTaskPriorityResponse,
  AcademicTaskRequestOptions,
  AcademicTaskResponse,
  AcademicTaskStatus,
  AcademicTaskStatusUpdateRequest,
  AcademicTaskType,
  AcademicTaskUpdateRequest,
} from "./types";

const ACADEMIC_TASKS_API_PATH =
  "/api/academic-tasks";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The academic task operation could not be completed.";

export class AcademicTaskApiError extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);

    this.name = "AcademicTaskApiError";
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

function isBoundedScore(
  value: unknown,
): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    value >= 0 &&
    value <= 100
  );
}

function isAcademicTaskDifficulty(
  value: unknown,
): value is AcademicTaskDifficulty {
  return (
    value === "easy" ||
    value === "medium" ||
    value === "hard"
  );
}

function isAcademicTaskType(
  value: unknown,
): value is AcademicTaskType {
  return (
    value === "assignment" ||
    value === "project" ||
    value === "exam" ||
    value === "quiz" ||
    value === "reading" ||
    value === "presentation" ||
    value === "research" ||
    value === "other"
  );
}

function isAcademicTaskOutputType(
  value: unknown,
): value is AcademicTaskOutputType {
  return (
    value === "writing" ||
    value === "computation" ||
    value === "research" ||
    value === "presentation" ||
    value === "creative" ||
    value === "reading_analysis" ||
    value === "memorization" ||
    value === "mixed" ||
    value === "other"
  );
}

function isAcademicTaskStatus(
  value: unknown,
): value is AcademicTaskStatus {
  return (
    value === "pending" ||
    value === "in_progress" ||
    value === "completed" ||
    value === "cancelled"
  );
}

function getApiBaseUrl(): string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (!configuredUrl) {
    throw new AcademicTaskApiError(
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

function buildAcademicTasksBaseUrl():
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
      "/academic-tasks",
    ].join("");
  }

  return [
    apiBaseUrl,
    ACADEMIC_TASKS_API_PATH,
  ].join("");
}

function buildAcademicTaskUrl(
  taskId: string,
): string {
  return [
    buildAcademicTasksBaseUrl(),
    "/",
    encodeURIComponent(
      taskId,
    ),
  ].join("");
}

function buildAcademicTaskStatusUrl(
  taskId: string,
): string {
  return [
    buildAcademicTaskUrl(
      taskId,
    ),
    "/status",
  ].join("");
}

function buildPrioritizedTasksUrl(
  limit?: number,
): string {
  const url = new URL(
    [
      buildAcademicTasksBaseUrl(),
      "/prioritized",
    ].join(""),
  );

  if (limit !== undefined) {
    url.searchParams.set(
      "limit",
      String(limit),
    );
  }

  return url.toString();
}

function buildAcademicTaskListUrl(
  limit?: number,
): string {
  const url = new URL(
    buildAcademicTasksBaseUrl(),
  );

  if (limit !== undefined) {
    url.searchParams.set(
      "limit",
      String(limit),
    );
  }

  return url.toString();
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
    typeof payload.code ===
    "string"
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
      AcademicTaskApiErrorResponse =
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
        "Check the academic task details."
      );

    case 401:
      return SESSION_EXPIRED_MESSAGE;

    case 404:
      return (
        "The academic task could not be found."
      );

    case 422:
      return (
        "The academic task request was invalid."
      );

    case 500:
      return (
        "Stored academic task data could not be processed."
      );

    case 503:
      return (
        "Academic task storage is temporarily unavailable."
      );

    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}

function isAcademicTaskResponse(
  value: unknown,
): value is AcademicTaskResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.id) &&
    isNonEmptyString(
      value.subject_id,
    ) &&
    isNonEmptyString(value.title) &&
    isNullableString(
      value.description,
    ) &&
    isNonEmptyString(
      value.deadline,
    ) &&
    typeof value.estimated_minutes ===
      "number" &&
    Number.isInteger(
      value.estimated_minutes,
    ) &&
    value.estimated_minutes >= 1 &&
    isAcademicTaskDifficulty(
      value.difficulty,
    ) &&
    isAcademicTaskType(
      value.task_type,
    ) &&
    isAcademicTaskOutputType(
      value.output_type,
    ) &&
    isAcademicTaskStatus(
      value.status,
    ) &&
    isNonEmptyString(
      value.created_at,
    ) &&
    isNonEmptyString(
      value.updated_at,
    )
  );
}

function isAcademicTaskListResponse(
  value: unknown,
): value is AcademicTaskListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(
      isAcademicTaskResponse,
    )
  );
}

function isPriorityBreakdown(
  value: unknown,
): value is AcademicTaskPriorityBreakdown {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isBoundedScore(
      value.total_score,
    ) &&
    isBoundedScore(
      value.deadline_score,
    ) &&
    isBoundedScore(
      value.difficulty_score,
    ) &&
    isBoundedScore(
      value.estimated_time_score,
    ) &&
    isBoundedScore(
      value.output_confidence_score,
    ) &&
    isBoundedScore(
      value.previous_performance_score,
    ) &&
    isBoundedScore(
      value.available_study_time_score,
    ) &&
    isBoundedScore(
      value.status_score,
    )
  );
}

function isAcademicTaskPriorityResponse(
  value: unknown,
): value is AcademicTaskPriorityResponse {
  return (
    isRecord(value) &&
    isAcademicTaskResponse(
      value.task,
    ) &&
    isPriorityBreakdown(
      value.priority,
    )
  );
}

function isAcademicTaskPriorityListResponse(
  value: unknown,
): value is AcademicTaskPriorityListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(
      isAcademicTaskPriorityResponse,
    )
  );
}

function normalizeTaskId(
  taskId: string,
): string {
  const normalizedTaskId =
    taskId.trim();

  if (!normalizedTaskId) {
    throw new AcademicTaskApiError(
      "An academic task must be selected.",
      400,
      "ACADEMIC_TASK_ID_REQUIRED",
    );
  }

  return normalizedTaskId;
}

function validateLimit(
  limit: number | undefined,
): void {
  if (limit === undefined) {
    return;
  }

  if (
    !Number.isInteger(limit) ||
    limit < 1 ||
    limit > 100
  ) {
    throw new AcademicTaskApiError(
      "Task list limit must be between 1 and 100.",
      400,
      "ACADEMIC_TASK_LIMIT_INVALID",
    );
  }
}

async function getAccessToken():
  Promise<string> {
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
    throw new AcademicTaskApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  return session.access_token;
}

async function sendRequest(
  url: string,
  init: RequestInit,
): Promise<Response> {
  try {
    return await fetch(
      url,
      {
        ...init,
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

    throw new AcademicTaskApiError(
      "The academic task service could not connect to the backend.",
      null,
      "ACADEMIC_TASK_API_UNREACHABLE",
    );
  }
}

async function requestJson(
  url: string,
  init: RequestInit,
): Promise<unknown> {
  const response =
    await sendRequest(
      url,
      init,
    );

  const payload =
    await readJsonResponse(
      response,
    );

  if (!response.ok) {
    throw new AcademicTaskApiError(
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

  return payload;
}

export async function listAcademicTasks(
  options: AcademicTaskListOptions = {},
): Promise<AcademicTaskResponse[]> {
  validateLimit(
    options.limit,
  );

  const accessToken =
    await getAccessToken();

  const payload =
    await requestJson(
      buildAcademicTaskListUrl(
        options.limit,
      ),
      {
        method: "GET",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },

        signal: options.signal,
      },
    );

  if (
    !isAcademicTaskListResponse(
      payload,
    )
  ) {
    throw new AcademicTaskApiError(
      "The academic task service returned an invalid list response.",
      502,
      "INVALID_ACADEMIC_TASK_LIST_RESPONSE",
    );
  }

  return payload.items;
}

export async function listPrioritizedAcademicTasks(
  options: AcademicTaskListOptions = {},
): Promise<AcademicTaskPriorityResponse[]> {
  validateLimit(
    options.limit,
  );

  const accessToken =
    await getAccessToken();

  const payload =
    await requestJson(
      buildPrioritizedTasksUrl(
        options.limit,
      ),
      {
        method: "GET",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },

        signal: options.signal,
      },
    );

  if (
    !isAcademicTaskPriorityListResponse(
      payload,
    )
  ) {
    throw new AcademicTaskApiError(
      "The academic task service returned an invalid priority response.",
      502,
      "INVALID_ACADEMIC_TASK_PRIORITY_RESPONSE",
    );
  }

  return payload.items;
}

export async function getAcademicTask(
  taskId: string,
  options: AcademicTaskRequestOptions = {},
): Promise<AcademicTaskResponse> {
  const normalizedTaskId =
    normalizeTaskId(
      taskId,
    );

  const accessToken =
    await getAccessToken();

  const payload =
    await requestJson(
      buildAcademicTaskUrl(
        normalizedTaskId,
      ),
      {
        method: "GET",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },

        signal: options.signal,
      },
    );

  if (
    !isAcademicTaskResponse(
      payload,
    )
  ) {
    throw new AcademicTaskApiError(
      "The academic task service returned an invalid task response.",
      502,
      "INVALID_ACADEMIC_TASK_RESPONSE",
    );
  }

  return payload;
}

export async function createAcademicTask(
  request: AcademicTaskCreateRequest,
  options: AcademicTaskRequestOptions = {},
): Promise<AcademicTaskResponse> {
  const accessToken =
    await getAccessToken();

  const payload =
    await requestJson(
      buildAcademicTasksBaseUrl(),
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

        signal: options.signal,
      },
    );

  if (
    !isAcademicTaskResponse(
      payload,
    )
  ) {
    throw new AcademicTaskApiError(
      "The academic task service returned an invalid task response.",
      502,
      "INVALID_ACADEMIC_TASK_RESPONSE",
    );
  }

  return payload;
}

export async function updateAcademicTask(
  taskId: string,
  request: AcademicTaskUpdateRequest,
  options: AcademicTaskRequestOptions = {},
): Promise<AcademicTaskResponse> {
  const normalizedTaskId =
    normalizeTaskId(
      taskId,
    );

  const accessToken =
    await getAccessToken();

  const payload =
    await requestJson(
      buildAcademicTaskUrl(
        normalizedTaskId,
      ),
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${accessToken}`,
        },

        body: JSON.stringify(
          request,
        ),

        signal: options.signal,
      },
    );

  if (
    !isAcademicTaskResponse(
      payload,
    )
  ) {
    throw new AcademicTaskApiError(
      "The academic task service returned an invalid task response.",
      502,
      "INVALID_ACADEMIC_TASK_RESPONSE",
    );
  }

  return payload;
}

export async function updateAcademicTaskStatus(
  taskId: string,
  request: AcademicTaskStatusUpdateRequest,
  options: AcademicTaskRequestOptions = {},
): Promise<AcademicTaskResponse> {
  const normalizedTaskId =
    normalizeTaskId(
      taskId,
    );

  const accessToken =
    await getAccessToken();

  const payload =
    await requestJson(
      buildAcademicTaskStatusUrl(
        normalizedTaskId,
      ),
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${accessToken}`,
        },

        body: JSON.stringify(
          request,
        ),

        signal: options.signal,
      },
    );

  if (
    !isAcademicTaskResponse(
      payload,
    )
  ) {
    throw new AcademicTaskApiError(
      "The academic task service returned an invalid task response.",
      502,
      "INVALID_ACADEMIC_TASK_RESPONSE",
    );
  }

  return payload;
}

export async function deleteAcademicTask(
  taskId: string,
  options: AcademicTaskRequestOptions = {},
): Promise<void> {
  const normalizedTaskId =
    normalizeTaskId(
      taskId,
    );

  const accessToken =
    await getAccessToken();

  const response =
    await sendRequest(
      buildAcademicTaskUrl(
        normalizedTaskId,
      ),
      {
        method: "DELETE",

        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },

        signal: options.signal,
      },
    );

  if (response.ok) {
    return;
  }

  const payload =
    await readJsonResponse(
      response,
    );

  throw new AcademicTaskApiError(
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