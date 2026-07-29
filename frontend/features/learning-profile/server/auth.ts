// File: /frontend/features/learning-profile/server/auth.ts
// Purpose: Retrieves the verified authenticated student ID for
// server-side learning-profile queries and mutations.

import "server-only";

import type {
  SupabaseClient,
} from "@supabase/supabase-js";

import type {
  Database,
} from "@/types/database";

import {
  LearningProfileDataError,
} from "./errors";

export async function requireAuthenticatedUserId(
  supabase: SupabaseClient<Database>,
): Promise<string> {
  const {
    data,
    error,
  } = await supabase.auth.getClaims();

  const userId =
    data?.claims?.sub;

  if (
    error ||
    typeof userId !== "string" ||
    !userId
  ) {
    throw new LearningProfileDataError(
      "UNAUTHENTICATED",
      "A verified student session is required.",
      {
        cause: error,
      },
    );
  }

  return userId;
}