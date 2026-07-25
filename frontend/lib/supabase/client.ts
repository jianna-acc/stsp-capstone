// File: /frontend/lib/supabase/client.ts
// Purpose: Creates a typed browser Supabase client for Client
// Components and other code that runs in the user's browser.

import { createBrowserClient } from "@supabase/ssr";

import type { Database } from "@/types/database";

import { getSupabasePublicConfig } from "./config";

export function createClient() {
  const { url, publishableKey } =
    getSupabasePublicConfig();

  return createBrowserClient<Database>(
    url,
    publishableKey,
  );
}