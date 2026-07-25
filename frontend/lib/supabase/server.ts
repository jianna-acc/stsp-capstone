// File: /frontend/lib/supabase/server.ts
// Purpose: Creates a typed, cookie-aware Supabase client for
// Next.js Server Components, Server Actions, and Route Handlers.

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

import type { Database } from "@/types/database";

import { getSupabasePublicConfig } from "./config";

export async function createClient() {
  const cookieStore = await cookies();

  const { url, publishableKey } =
    getSupabasePublicConfig();

  return createServerClient<Database>(
    url,
    publishableKey,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },

        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(
              ({ name, value, options }) => {
                cookieStore.set(
                  name,
                  value,
                  options,
                );
              },
            );
          } catch {
            /*
             * Server Components cannot always modify cookies.
             * Authentication session refresh will be handled
             * by the Next.js proxy during the auth phase.
             */
          }
        },
      },
    },
  );
}