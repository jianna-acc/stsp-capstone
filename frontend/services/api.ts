// File: /frontend/services/api.ts
// Purpose: Provides reusable functions for communicating with
// the FastAPI backend and handling request errors consistently.

import type {
  ApiEnvironment,
  ApiHealthResponse,
} from "@/types/api";

const REQUEST_TIMEOUT_MS = 8_000;

export class ApiRequestError extends Error {
  readonly endpoint: string;
  readonly status: number | null;

  constructor(
    message: string,
    endpoint: string,
    status: number | null = null,
  ) {
    super(message);

    this.name = "ApiRequestError";
    this.endpoint = endpoint;
    this.status = status;

    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export function getApiBaseUrl(): string {
  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

  if (!apiBaseUrl) {
    throw new ApiRequestError(
      "The frontend API address is not configured.",
      "NEXT_PUBLIC_API_BASE_URL",
    );
  }

  return apiBaseUrl.replace(/\/+$/, "");
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  return `${getApiBaseUrl()}${normalizedPath}`;
}

function isApiEnvironment(
  value: unknown,
): value is ApiEnvironment {
  return (
    value === "development" ||
    value === "testing" ||
    value === "production"
  );
}

function isApiHealthResponse(
  value: unknown,
): value is ApiHealthResponse {
  if (
    typeof value !== "object" ||
    value === null
  ) {
    return false;
  }

  const data = value as Record<string, unknown>;

  return (
    data.status === "healthy" &&
    typeof data.service === "string" &&
    typeof data.version === "string" &&
    isApiEnvironment(data.environment)
  );
}

async function requestJson(
  endpoint: string,
  requestInit: RequestInit = {},
): Promise<unknown> {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  const headers = new Headers(requestInit.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  try {
    const response = await fetch(endpoint, {
      ...requestInit,
      headers,
      signal: controller.signal,
      cache: "no-store",
    });

    if (!response.ok) {
      let errorMessage =
        `The backend returned status ${response.status}.`;

      try {
        const errorData: unknown =
          await response.json();

        if (
          typeof errorData === "object" &&
          errorData !== null &&
          "detail" in errorData &&
          typeof errorData.detail === "string"
        ) {
          errorMessage = errorData.detail;
        }
      } catch {
        // Keep the status-based error message when the
        // response body is empty or is not valid JSON.
      }

      throw new ApiRequestError(
        errorMessage,
        endpoint,
        response.status,
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }

    if (
      error instanceof Error &&
      error.name === "AbortError"
    ) {
      throw new ApiRequestError(
        "The backend took too long to respond.",
        endpoint,
      );
    }

    throw new ApiRequestError(
      "The frontend could not connect to the backend.",
      endpoint,
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getApiHealth():
  Promise<ApiHealthResponse> {
  const endpoint = buildApiUrl("/api/health");

  const responseData =
    await requestJson(endpoint);

  if (!isApiHealthResponse(responseData)) {
    throw new ApiRequestError(
      "The backend returned an unexpected health response.",
      endpoint,
      200,
    );
  }

  return responseData;
}