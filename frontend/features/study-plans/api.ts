// File: /frontend/features/study-plans/api.ts
// Purpose: Sends authenticated Track D study-plan requests
// to the protected FastAPI study-planning endpoints.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import type {
  StudyPlan,
  StudyPlanApiErrorResponse,
  StudyPlanApiRequestOptions,
  StudyPlanCreateRequest,
  StudyPlanGenerationRequest,
  StudyPlanGenerationResponse,
  StudyPlanListResponse,
  StudyPlanRegenerationRequest,
  StudySession,
  StudySessionCreateRequest,
  StudySessionListResponse,
  UnscheduledTask,
} from "./types";

const STUDY_PLANS_API_PATH =
  "/api/study-plans";

const STUDY_PLAN_GENERATION_API_PATH =
  "/api/study-plan-generation";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The study-plan request could not be completed.";


export class StudyPlanApiError
  extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    code: string | null = null,
  ) {
    super(message);

    this.name = "StudyPlanApiError";
    this.status = status;
    this.code = code;
  }
}


function isRecord(
  value: unknown,
): value is Record<
  string,
  unknown
> {
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


function isStudyPlan(
  value: unknown,
): value is StudyPlan {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.id) &&
    isNonEmptyString(value.title) &&
    isNonEmptyString(
      value.starts_on,
    ) &&
    isNonEmptyString(
      value.ends_on,
    ) &&
    (
      value.status === "draft" ||
      value.status === "active" ||
      value.status === "completed" ||
      value.status === "archived"
    ) &&
    (
      value.generation_mode ===
        "manual" ||
      value.generation_mode ===
        "generated"
    ) &&
    isNullableString(
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


function isStudySession(
  value: unknown,
): value is StudySession {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.id) &&
    isNonEmptyString(
      value.study_plan_id,
    ) &&
    isNonEmptyString(
      value.subject_id,
    ) &&
    isNonEmptyString(value.title) &&
    isNonEmptyString(
      value.starts_at,
    ) &&
    isNonEmptyString(
      value.ends_at,
    ) &&
    (
      value.status === "planned" ||
      value.status === "completed" ||
      value.status === "skipped"
    ) &&
    (
      value.origin === "manual" ||
      value.origin === "generated"
    ) &&
    isNullableString(
      value.notes,
    ) &&
    isNonEmptyString(
      value.created_at,
    ) &&
    isNonEmptyString(
      value.updated_at,
    )
  );
}


function isUnscheduledTask(
  value: unknown,
): value is UnscheduledTask {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(
      value.task_id,
    ) &&
    typeof value.remaining_minutes ===
      "number" &&
    Number.isInteger(
      value.remaining_minutes,
    ) &&
    value.remaining_minutes >= 0
  );
}


function isStudyPlanListResponse(
  value: unknown,
): value is StudyPlanListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(
      isStudyPlan,
    )
  );
}


function isStudySessionListResponse(
  value: unknown,
): value is StudySessionListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(
      isStudySession,
    )
  );
}


function isStudyPlanGenerationResponse(
  value: unknown,
): value is StudyPlanGenerationResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isStudyPlan(value.plan) &&
    Array.isArray(
      value.sessions,
    ) &&
    value.sessions.every(
      isStudySession,
    ) &&
    Array.isArray(
      value.unscheduled_tasks,
    ) &&
    value.unscheduled_tasks.every(
      isUnscheduledTask,
    )
  );
}


function getApiBaseUrl(): string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (!configuredUrl) {
    throw new StudyPlanApiError(
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
  apiPath: string,
): string {
  const apiBaseUrl =
    getApiBaseUrl();

  if (
    apiBaseUrl.endsWith(
      "/api",
    ) &&
    apiPath.startsWith(
      "/api/",
    )
  ) {
    return [
      apiBaseUrl,
      apiPath.slice(
        4,
      ),
    ].join("");
  }

  return [
    apiBaseUrl,
    apiPath,
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

  return typeof payload.error_code ===
    "string"
    ? payload.error_code
    : null;
}


function getErrorMessage(
  payload: unknown,
): string {
  if (!isRecord(payload)) {
    return DEFAULT_ERROR_MESSAGE;
  }

  if (
    typeof payload.message ===
      "string" &&
    payload.message.trim()
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

  return DEFAULT_ERROR_MESSAGE;
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
    throw new StudyPlanApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTH_SESSION_REQUIRED",
    );
  }

  return session.access_token;
}


async function authenticatedFetch(
  apiPath: string,
  init: RequestInit,
  options: StudyPlanApiRequestOptions = {},
): Promise<Response> {
  const accessToken =
    await getAccessToken();

  const headers =
    new Headers(
      init.headers,
    );

  headers.set(
    "Authorization",
    `Bearer ${accessToken}`,
  );

  if (
    init.body !== undefined &&
    init.body !== null
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  try {
    return await fetch(
      buildApiUrl(
        apiPath,
      ),
      {
        ...init,
        headers,
        signal:
          options.signal,
      },
    );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new StudyPlanApiError(
      "The study-plan service could not be reached.",
      null,
      "STUDY_PLAN_NETWORK_ERROR",
    );
  }
}


async function requireSuccessfulJson(
  response: Response,
): Promise<unknown> {
  const payload =
    await readJsonResponse(
      response,
    );

  if (!response.ok) {
    const typedPayload =
      isRecord(payload)
        ? payload as StudyPlanApiErrorResponse
        : null;

    throw new StudyPlanApiError(
      getErrorMessage(
        typedPayload,
      ),
      response.status,
      getErrorCode(
        typedPayload,
      ),
    );
  }

  return payload;
}


function planPath(
  studyPlanId: string,
): string {
  return [
    STUDY_PLANS_API_PATH,
    "/",
    encodeURIComponent(
      studyPlanId,
    ),
  ].join("");
}

function regenerationPath(
  studyPlanId: string,
): string {
  return [
    STUDY_PLAN_GENERATION_API_PATH,
    "/",
    encodeURIComponent(
      studyPlanId,
    ),
    "/regenerate",
  ].join("");
}

function sessionsPath(
  studyPlanId: string,
): string {
  return [
    planPath(
      studyPlanId,
    ),
    "/sessions",
  ].join("");
}


export async function createStudyPlan(
  request: StudyPlanCreateRequest,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudyPlan> {
  const response =
    await authenticatedFetch(
      STUDY_PLANS_API_PATH,
      {
        method: "POST",
        body: JSON.stringify(
          request,
        ),
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (!isStudyPlan(payload)) {
    throw new StudyPlanApiError(
      "The study-plan service returned an invalid response.",
      response.status,
      "INVALID_STUDY_PLAN_RESPONSE",
    );
  }

  return payload;
}


export async function listStudyPlans(
  limit = 50,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudyPlan[]> {
  const query =
    new URLSearchParams({
      limit: String(
        limit,
      ),
    });

  const response =
    await authenticatedFetch(
      [
        STUDY_PLANS_API_PATH,
        "?",
        query.toString(),
      ].join(""),
      {
        method: "GET",
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isStudyPlanListResponse(
      payload,
    )
  ) {
    throw new StudyPlanApiError(
      "The study-plan service returned an invalid response.",
      response.status,
      "INVALID_STUDY_PLAN_LIST_RESPONSE",
    );
  }

  return payload.items;
}


export async function getStudyPlan(
  studyPlanId: string,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudyPlan> {
  const response =
    await authenticatedFetch(
      planPath(
        studyPlanId,
      ),
      {
        method: "GET",
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (!isStudyPlan(payload)) {
    throw new StudyPlanApiError(
      "The study-plan service returned an invalid response.",
      response.status,
      "INVALID_STUDY_PLAN_RESPONSE",
    );
  }

  return payload;
}


export async function deleteStudyPlan(
  studyPlanId: string,
  options: StudyPlanApiRequestOptions = {},
): Promise<void> {
  const response =
    await authenticatedFetch(
      planPath(
        studyPlanId,
      ),
      {
        method: "DELETE",
      },
      options,
    );

  if (!response.ok) {
    await requireSuccessfulJson(
      response,
    );
  }
}


export async function createStudySession(
  studyPlanId: string,
  request: StudySessionCreateRequest,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudySession> {
  const response =
    await authenticatedFetch(
      sessionsPath(
        studyPlanId,
      ),
      {
        method: "POST",
        body: JSON.stringify(
          request,
        ),
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (!isStudySession(payload)) {
    throw new StudyPlanApiError(
      "The study-plan service returned an invalid session response.",
      response.status,
      "INVALID_STUDY_SESSION_RESPONSE",
    );
  }

  return payload;
}


export async function listStudySessions(
  studyPlanId: string,
  limit = 200,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudySession[]> {
  const query =
    new URLSearchParams({
      limit: String(
        limit,
      ),
    });

  const response =
    await authenticatedFetch(
      [
        sessionsPath(
          studyPlanId,
        ),
        "?",
        query.toString(),
      ].join(""),
      {
        method: "GET",
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isStudySessionListResponse(
      payload,
    )
  ) {
    throw new StudyPlanApiError(
      "The study-plan service returned an invalid session list.",
      response.status,
      "INVALID_STUDY_SESSION_LIST_RESPONSE",
    );
  }

  return payload.items;
}


export async function deleteStudySession(
  studyPlanId: string,
  studySessionId: string,
  options: StudyPlanApiRequestOptions = {},
): Promise<void> {
  const apiPath = [
    sessionsPath(
      studyPlanId,
    ),
    "/",
    encodeURIComponent(
      studySessionId,
    ),
  ].join("");

  const response =
    await authenticatedFetch(
      apiPath,
      {
        method: "DELETE",
      },
      options,
    );

  if (!response.ok) {
    await requireSuccessfulJson(
      response,
    );
  }
}


export async function generateStudyPlan(
  request: StudyPlanGenerationRequest,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudyPlanGenerationResponse> {
  const response =
    await authenticatedFetch(
      STUDY_PLAN_GENERATION_API_PATH,
      {
        method: "POST",
        body: JSON.stringify(
          request,
        ),
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isStudyPlanGenerationResponse(
      payload,
    )
  ) {
    throw new StudyPlanApiError(
      "The study-plan generator returned an invalid response.",
      response.status,
      "INVALID_STUDY_PLAN_GENERATION_RESPONSE",
    );
  }

  return payload;
}
export async function regenerateStudyPlan(
  studyPlanId: string,
  request: StudyPlanRegenerationRequest,
  options: StudyPlanApiRequestOptions = {},
): Promise<StudyPlanGenerationResponse> {
  const response =
    await authenticatedFetch(
      regenerationPath(
        studyPlanId,
      ),
      {
        method: "POST",
        body: JSON.stringify(
          request,
        ),
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isStudyPlanGenerationResponse(
      payload,
    )
  ) {
    throw new StudyPlanApiError(
      "The study-plan regenerator returned an invalid response.",
      response.status,
      "INVALID_STUDY_PLAN_REGENERATION_RESPONSE",
    );
  }

  return payload;
}