// File: /frontend/features/study-timer/api.ts
// Purpose: Sends authenticated actual Study Activity timer
// requests to the protected FastAPI lifecycle endpoints.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import type {
  StudyActivity,
  StudyActivityApiErrorResponse,
  StudyActivityApiRequestOptions,
  StudyActivityStartRequest,
} from "./types";

const STUDY_ACTIVITY_API_PATH =
  "/api/study-activity";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "The study timer request could not be completed.";


export class StudyActivityApiError
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
      "StudyActivityApiError";

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
    typeof value === "object" &&
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


function isNonNegativeInteger(
  value: unknown,
): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(
      value,
    ) &&
    value >= 0
  );
}


function isStudyActivity(
  value: unknown,
): value is StudyActivity {
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
    isNullableString(
      value.subject_id,
    ) &&
    isNullableString(
      value.study_plan_id,
    ) &&
    isNullableString(
      value.study_session_id,
    ) &&
    isNonEmptyString(
      value.title,
    ) &&
    (
      value.status ===
        "running" ||
      value.status ===
        "paused" ||
      value.status ===
        "completed"
    ) &&
    (
      value.mode ===
        "focus" ||
      value.mode ===
        "break"
    ) &&
    isNonEmptyString(
      value.started_at,
    ) &&
    isNullableString(
      value.ended_at,
    ) &&
    isNullableString(
      value.segment_started_at,
    ) &&
    isNonNegativeInteger(
      value.focus_seconds,
    ) &&
    isNonNegativeInteger(
      value.break_seconds,
    ) &&
    isNonEmptyString(
      value.created_at,
    ) &&
    isNonEmptyString(
      value.updated_at,
    )
  );
}


function getApiBaseUrl():
  string {
  const configuredUrl =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (
    !configuredUrl
  ) {
    throw new StudyActivityApiError(
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
  if (
    !isRecord(
      payload,
    )
  ) {
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
  if (
    !isRecord(
      payload,
    )
  ) {
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
  } =
    await supabase.auth.getSession();

  if (
    error ||
    !session?.access_token
  ) {
    throw new StudyActivityApiError(
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
  options:
    StudyActivityApiRequestOptions = {},
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
  } catch (
    error
  ) {
    if (
      error instanceof DOMException &&
      error.name ===
        "AbortError"
    ) {
      throw error;
    }

    throw new StudyActivityApiError(
      "The study timer service could not be reached.",
      null,
      "STUDY_ACTIVITY_NETWORK_ERROR",
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

  if (
    !response.ok
  ) {
    const typedPayload =
      isRecord(
        payload,
      )
        ? payload as
          StudyActivityApiErrorResponse
        : null;

    throw new StudyActivityApiError(
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


function activityPath(
  activityId: string,
): string {
  return [
    STUDY_ACTIVITY_API_PATH,
    "/",
    encodeURIComponent(
      activityId,
    ),
  ].join("");
}


async function transitionActivity(
  activityId: string,
  suffix: string,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  const response =
    await authenticatedFetch(
      [
        activityPath(
          activityId,
        ),
        suffix,
      ].join(""),
      {
        method: "POST",
      },
      options,
    );

  const payload =
    await requireSuccessfulJson(
      response,
    );

  if (
    !isStudyActivity(
      payload,
    )
  ) {
    throw new StudyActivityApiError(
      "The study timer service returned an invalid response.",
      response.status,
      "INVALID_STUDY_ACTIVITY_RESPONSE",
    );
  }

  return payload;
}


export async function getActiveStudyActivity(
  options:
    StudyActivityApiRequestOptions = {},
): Promise<
  StudyActivity | null
> {
  const response =
    await authenticatedFetch(
      `${STUDY_ACTIVITY_API_PATH}/active`,
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
    payload === null
  ) {
    return null;
  }

  if (
    !isStudyActivity(
      payload,
    )
  ) {
    throw new StudyActivityApiError(
      "The study timer service returned an invalid active timer.",
      response.status,
      "INVALID_STUDY_ACTIVITY_RESPONSE",
    );
  }

  return payload;
}


export async function startStudyActivity(
  request:
    StudyActivityStartRequest,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  const response =
    await authenticatedFetch(
      `${STUDY_ACTIVITY_API_PATH}/start`,
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
    !isStudyActivity(
      payload,
    )
  ) {
    throw new StudyActivityApiError(
      "The study timer service returned an invalid start response.",
      response.status,
      "INVALID_STUDY_ACTIVITY_RESPONSE",
    );
  }

  return payload;
}


export function pauseStudyActivity(
  activityId: string,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  return transitionActivity(
    activityId,
    "/pause",
    options,
  );
}


export function resumeStudyActivity(
  activityId: string,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  return transitionActivity(
    activityId,
    "/resume",
    options,
  );
}


export function startStudyActivityBreak(
  activityId: string,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  return transitionActivity(
    activityId,
    "/break/start",
    options,
  );
}


export function endStudyActivityBreak(
  activityId: string,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  return transitionActivity(
    activityId,
    "/break/end",
    options,
  );
}


export function endStudyActivity(
  activityId: string,
  options:
    StudyActivityApiRequestOptions = {},
): Promise<StudyActivity> {
  return transitionActivity(
    activityId,
    "/end",
    options,
  );
}