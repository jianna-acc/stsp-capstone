// File: /frontend/lib/supabase/proxy.ts
// Purpose: Refreshes the Supabase authentication session,
// synchronizes cookies, and prevents unauthenticated access to
// protected application routes.

import { createServerClient } from "@supabase/ssr";
import {
  NextResponse,
  type NextRequest,
} from "next/server";

import type { Database } from "@/types/database";

import { getSupabasePublicConfig } from "./config";

const PROTECTED_ROUTE_PREFIXES = [
  "/dashboard",
  "/profile",
  "/onboarding",
  "/subjects",
  "/files",
  "/tasks",
  "/study-plan",
  "/calendar",
  "/progress",
  "/assistant",
  "/analytics",
  "/settings",
] as const;

function isProtectedPath(
  pathname: string,
): boolean {
  return PROTECTED_ROUTE_PREFIXES.some(
    (prefix) =>
      pathname === prefix ||
      pathname.startsWith(
        `${prefix}/`,
      ),
  );
}

function copyResponseCookies(
  source: NextResponse,
  destination: NextResponse,
): NextResponse {
  source.cookies
    .getAll()
    .forEach((cookie) => {
      destination.cookies.set(cookie);
    });

  return destination;
}

function createLoginRedirect(
  request: NextRequest,
  currentResponse: NextResponse,
): NextResponse {
  const loginUrl =
    request.nextUrl.clone();

  const requestedPath = [
    request.nextUrl.pathname,
    request.nextUrl.search,
  ].join("");

  loginUrl.pathname = "/login";
  loginUrl.search = "";

  loginUrl.searchParams.set(
    "next",
    requestedPath,
  );

  const redirectResponse =
    NextResponse.redirect(loginUrl);

  return copyResponseCookies(
    currentResponse,
    redirectResponse,
  );
}

export async function updateSession(
  request: NextRequest,
): Promise<NextResponse> {
  let supabaseResponse =
    NextResponse.next({
      request,
    });

  const { url, publishableKey } =
    getSupabasePublicConfig();

  const supabase =
    createServerClient<Database>(
      url,
      publishableKey,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll();
          },

          setAll(cookiesToSet) {
            cookiesToSet.forEach(
              ({ name, value }) => {
                request.cookies.set(
                  name,
                  value,
                );
              },
            );

            supabaseResponse =
              NextResponse.next({
                request,
              });

            cookiesToSet.forEach(
              ({
                name,
                value,
                options,
              }) => {
                supabaseResponse.cookies.set(
                  name,
                  value,
                  options,
                );
              },
            );
          },
        },
      },
    );

  /*
   * getClaims validates the authentication token and refreshes
   * expired session cookies when necessary.
   *
   * Do not use getSession for server-side authorization.
   */
  const { data } =
    await supabase.auth.getClaims();

  const userId =
    data?.claims?.sub;

  if (
    !userId &&
    isProtectedPath(
      request.nextUrl.pathname,
    )
  ) {
    return createLoginRedirect(
      request,
      supabaseResponse,
    );
  }

  return supabaseResponse;
}