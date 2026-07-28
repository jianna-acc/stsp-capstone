// File: /frontend/lib/supabase/proxy.ts
// Purpose: Refreshes the Supabase authentication session and
// synchronizes updated cookies with Next.js and the browser.

import { createServerClient } from "@supabase/ssr";
import {
  NextResponse,
  type NextRequest,
} from "next/server";

import type { Database } from "@/types/database";

import { getSupabasePublicConfig } from "./config";

export async function updateSession(
  request: NextRequest,
): Promise<NextResponse> {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const { url, publishableKey } =
    getSupabasePublicConfig();

  const supabase = createServerClient<Database>(
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
              request.cookies.set(name, value);
            },
          );

          supabaseResponse = NextResponse.next({
            request,
          });

          cookiesToSet.forEach(
            ({ name, value, options }) => {
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
   * This validates the current access token and refreshes the
   * authentication cookies when necessary.
   *
   * Do not replace this with getSession() for authorization.
   */
  await supabase.auth.getClaims();

  return supabaseResponse;
}