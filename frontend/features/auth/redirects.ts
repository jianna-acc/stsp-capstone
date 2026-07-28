// File: /frontend/features/auth/redirects.ts
// Purpose: Validates internal authentication redirect paths so
// authentication routes cannot redirect users to external sites.

export const DEFAULT_AFTER_CONFIRM_PATH =
  "/login?confirmed=1";

export const DEFAULT_AFTER_LOGIN_PATH =
  "/dashboard";

export function getSafeInternalPath(
  value: string | null | undefined,
  fallback = DEFAULT_AFTER_CONFIRM_PATH,
): string {
  const candidate = value?.trim();

  if (
    !candidate ||
    !candidate.startsWith("/") ||
    candidate.startsWith("//") ||
    candidate.includes("\\") ||
    /[\r\n]/.test(candidate)
  ) {
    return fallback;
  }

  try {
    const trustedOrigin =
      new URL("http://internal.local");

    const parsedUrl =
      new URL(candidate, trustedOrigin);

    if (
      parsedUrl.origin !== trustedOrigin.origin
    ) {
      return fallback;
    }

    return [
      parsedUrl.pathname,
      parsedUrl.search,
      parsedUrl.hash,
    ].join("");
  } catch {
    return fallback;
  }
}