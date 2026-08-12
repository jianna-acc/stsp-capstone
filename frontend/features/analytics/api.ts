// File: /frontend/features/analytics/api.ts
// Purpose: Loads authenticated study Analytics data
// from the protected FastAPI Analytics endpoint.

"use client";

import {
  createClient,
} from "@/lib/supabase/client";

import {
  ANALYTICS_PERIODS,
} from "./types";

import type {
  AnalyticsApiErrorResponse,
  AnalyticsAvailability,
  AnalyticsCountMetric,
  AnalyticsCountScope,
  AnalyticsDataState,
  AnalyticsMetric,
  AnalyticsOverviewResponse,
  AnalyticsPeriod,
  AnalyticsStudyWeek,
  AnalyticsTopicPerformance,
} from "./types";


const ANALYTICS_API_PATH =
  "/api/analytics/overview";

const SESSION_EXPIRED_MESSAGE =
  "Your session has expired. Sign in again.";

const DEFAULT_ERROR_MESSAGE =
  "Analytics could not be loaded.";


interface AnalyticsRequestOptions {
  signal?:
    AbortSignal;
}


export class AnalyticsApiError
  extends Error {
  readonly status:
    number | null;

  readonly code:
    string | null;

  constructor(
    message:
      string,
    status:
      number | null = null,
    code:
      string | null = null,
  ) {
    super(
      message,
    );

    this.name =
      "AnalyticsApiError";

    this.status =
      status;

    this.code =
      code;
  }
}


function isRecord(
  value:
    unknown,
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
  value:
    unknown,
): value is string {
  return (
    typeof value ===
      "string" &&
    value.trim().length >
      0
  );
}


function isNullableString(
  value:
    unknown,
): value is string | null {
  return (
    value === null ||
    typeof value ===
      "string"
  );
}


function isNonNegativeInteger(
  value:
    unknown,
): value is number {
  return (
    typeof value ===
      "number" &&
    Number.isInteger(
      value,
    ) &&
    value >= 0
  );
}


function isPositiveInteger(
  value:
    unknown,
): value is number {
  return (
    typeof value ===
      "number" &&
    Number.isInteger(
      value,
    ) &&
    value >= 1
  );
}


function isFiniteNumber(
  value:
    unknown,
): value is number {
  return (
    typeof value ===
      "number" &&
    Number.isFinite(
      value,
    )
  );
}


function parseIsoDate(
  value:
    unknown,
): number | null {
  if (
    typeof value !==
      "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(
      value,
    )
  ) {
    return null;
  }

  const milliseconds =
    Date.parse(
      `${value}T00:00:00Z`,
    );

  if (
    !Number.isFinite(
      milliseconds,
    )
  ) {
    return null;
  }

  const normalized =
    new Date(
      milliseconds,
    )
      .toISOString()
      .slice(
        0,
        10,
      );

  if (
    normalized !== value
  ) {
    return null;
  }

  return milliseconds;
}


function isAnalyticsPeriod(
  value:
    unknown,
): value is AnalyticsPeriod {
  return (
    typeof value ===
      "string" &&
    ANALYTICS_PERIODS.some(
      (
        period,
      ) =>
        period ===
        value,
    )
  );
}


function isAnalyticsAvailability(
  value:
    unknown,
): value is AnalyticsAvailability {
  return (
    value ===
      "available" ||
    value ===
      "unavailable"
  );
}


function isAnalyticsDataState(
  value:
    unknown,
): value is AnalyticsDataState {
  return (
    value ===
      "partial" ||
    value ===
      "ready"
  );
}


function isAnalyticsCountScope(
  value:
    unknown,
): value is AnalyticsCountScope {
  return (
    value ===
      "current_inventory"
  );
}


function isAnalyticsMetric(
  value:
    unknown,
): value is AnalyticsMetric {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  const metricValueIsValid =
    value.value ===
      null ||
    isFiniteNumber(
      value.value,
    );

  return (
    isAnalyticsAvailability(
      value.availability,
    ) &&
    metricValueIsValid &&
    isNonNegativeInteger(
      value.sample_size,
    ) &&
    isNullableString(
      value.message,
    )
  );
}


function isAnalyticsCountMetric(
  value:
    unknown,
): value is AnalyticsCountMetric {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  const countValueIsValid =
    value.value ===
      null ||
    isNonNegativeInteger(
      value.value,
    );

  return (
    isAnalyticsAvailability(
      value.availability,
    ) &&
    countValueIsValid &&
    isAnalyticsCountScope(
      value.scope,
    ) &&
    isNullableString(
      value.message,
    )
  );
}


function isAnalyticsTopicPerformance(
  value:
    unknown,
): value is AnalyticsTopicPerformance {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  return (
    isNonEmptyString(
      value.topic,
    ) &&
    isFiniteNumber(
      value.score_percent,
    ) &&
    value.score_percent >=
      0 &&
    value.score_percent <=
      100 &&
    isPositiveInteger(
      value.sample_size,
    )
  );
}


function isAnalyticsStudyWeek(
  value:
    unknown,
): value is AnalyticsStudyWeek {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  const weekStart =
    parseIsoDate(
      value.week_start,
    );

  const weekEnd =
    parseIsoDate(
      value.week_end,
    );

  return (
    weekStart !==
      null &&
    weekEnd !==
      null &&
    weekEnd >=
      weekStart &&
    isFiniteNumber(
      value.study_minutes,
    ) &&
    value.study_minutes >=
      0 &&
    isPositiveInteger(
      value.session_count,
    )
  );
}


function isAnalyticsOverviewResponse(
  value:
    unknown,
): value is AnalyticsOverviewResponse {
  if (
    !isRecord(
      value,
    )
  ) {
    return false;
  }

  return (
    isAnalyticsPeriod(
      value.period,
    ) &&
    isAnalyticsDataState(
      value.data_state,
    ) &&
    isAnalyticsCountMetric(
      value.subject_count,
    ) &&
    isAnalyticsCountMetric(
      value.study_material_count,
    ) &&
    isAnalyticsCountMetric(
      value.ready_study_material_count,
    ) &&
    isAnalyticsMetric(
      value.quiz_accuracy_percent,
    ) &&
    isAnalyticsMetric(
      value.flashcard_performance_percent,
    ) &&
    isAnalyticsMetric(
      value.study_minutes,
    ) &&
    Array.isArray(
      value.study_time_by_week,
    ) &&
    value.study_time_by_week.every(
      isAnalyticsStudyWeek,
    ) &&
    Array.isArray(
      value.strong_topics,
    ) &&
    value.strong_topics.every(
      isAnalyticsTopicPerformance,
    ) &&
    Array.isArray(
      value.weak_topics,
    ) &&
    value.weak_topics.every(
      isAnalyticsTopicPerformance,
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
    throw new AnalyticsApiError(
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


function buildAnalyticsOverviewUrl(
  period:
    AnalyticsPeriod,
): string {
  const apiBaseUrl =
    getApiBaseUrl();

  const baseUrl =
    apiBaseUrl.endsWith(
      "/api",
    )
      ? [
          apiBaseUrl,
          "/analytics/overview",
        ].join(
          "",
        )
      : [
          apiBaseUrl,
          ANALYTICS_API_PATH,
        ].join(
          "",
        );

  const query =
    new URLSearchParams({
      period,
    });

  return [
    baseUrl,
    "?",
    query.toString(),
  ].join(
    "",
  );
}


async function getAccessToken():
  Promise<string> {
  const supabase =
    createClient();

  const {
    data: {
      session,
    },
    error:
      sessionError,
  } =
    await supabase.auth
      .getSession();

  if (
    sessionError ||
    !session?.access_token
  ) {
    throw new AnalyticsApiError(
      SESSION_EXPIRED_MESSAGE,
      401,
      "AUTHENTICATION_REQUIRED",
    );
  }

  return session.access_token;
}


async function readJsonResponse(
  response:
    Response,
): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}


function getErrorCode(
  payload:
    unknown,
): string | null {
  if (
    !isRecord(
      payload,
    )
  ) {
    return null;
  }

  const errorPayload:
    AnalyticsApiErrorResponse =
    payload;

  if (
    typeof errorPayload
      .error_code ===
      "string"
  ) {
    return errorPayload
      .error_code;
  }

  if (
    isRecord(
      errorPayload.detail,
    )
  ) {
    if (
      typeof errorPayload
        .detail
        .error_code ===
        "string"
    ) {
      return errorPayload
        .detail
        .error_code;
    }

    if (
      typeof errorPayload
        .detail
        .code ===
        "string"
    ) {
      return errorPayload
        .detail
        .code;
    }
  }

  return null;
}


function getErrorMessage(
  payload:
    unknown,
  status:
    number,
): string {
  if (
    isRecord(
      payload,
    )
  ) {
    const errorPayload:
      AnalyticsApiErrorResponse =
      payload;

    if (
      typeof errorPayload
        .message ===
        "string" &&
      errorPayload
        .message
        .trim()
    ) {
      return errorPayload
        .message;
    }

    if (
      typeof errorPayload
        .detail ===
        "string" &&
      errorPayload
        .detail
        .trim()
    ) {
      return errorPayload
        .detail;
    }

    if (
      isRecord(
        errorPayload.detail,
      ) &&
      typeof errorPayload
        .detail
        .message ===
        "string" &&
      errorPayload
        .detail
        .message
        .trim()
    ) {
      return errorPayload
        .detail
        .message;
    }
  }

  switch (
    status
  ) {
    case 401:
      return SESSION_EXPIRED_MESSAGE;

    case 422:
      return (
        "The selected Analytics period is invalid."
      );

    case 503:
      return (
        "Analytics data is temporarily unavailable."
      );

    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}


export async function getAnalyticsOverview(
  period:
    AnalyticsPeriod =
      "all_time",
  options:
    AnalyticsRequestOptions = {},
): Promise<AnalyticsOverviewResponse> {
  if (
    !isAnalyticsPeriod(
      period,
    )
  ) {
    throw new AnalyticsApiError(
      "The selected Analytics period is invalid.",
      400,
      "ANALYTICS_PERIOD_INVALID",
    );
  }

  const accessToken =
    await getAccessToken();

  let response:
    Response;

  try {
    response =
      await fetch(
        buildAnalyticsOverviewUrl(
          period,
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
  } catch (
    error
  ) {
    if (
      error instanceof
        DOMException &&
      error.name ===
        "AbortError"
    ) {
      throw error;
    }

    throw new AnalyticsApiError(
      "Analytics could not connect to the backend.",
      null,
      "ANALYTICS_API_UNREACHABLE",
    );
  }

  const payload =
    await readJsonResponse(
      response,
    );

  if (
    !response.ok
  ) {
    throw new AnalyticsApiError(
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
    !isAnalyticsOverviewResponse(
      payload,
    )
  ) {
    throw new AnalyticsApiError(
      "The Analytics service returned an invalid response.",
      502,
      "INVALID_ANALYTICS_RESPONSE",
    );
  }

  return payload;
}