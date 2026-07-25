// File: /frontend/lib/supabase/config.ts
// Purpose: Validates and provides the browser-safe Supabase
// configuration shared by frontend Supabase clients.

export interface SupabasePublicConfig {
  url: string;
  publishableKey: string;
}

export function getSupabasePublicConfig():
  SupabasePublicConfig {
  const url =
    process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();

  const publishableKey =
    process.env
      .NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
      ?.trim();

  if (!url) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL is not configured.",
    );
  }

  if (!url.startsWith("https://")) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL must use HTTPS.",
    );
  }

  if (!url.includes(".supabase.co")) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL is not a valid hosted Supabase URL.",
    );
  }

  if (!publishableKey) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY is not configured.",
    );
  }

  if (!publishableKey.startsWith("sb_publishable_")) {
    throw new Error(
      "The frontend must use a Supabase publishable key.",
    );
  }

  return {
    url: url.replace(/\/+$/, ""),
    publishableKey,
  };
}