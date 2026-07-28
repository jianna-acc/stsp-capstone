// File: /frontend/lib/supabase/config.ts
// Purpose: Validates and provides the browser-safe application
// and Supabase configuration shared by frontend clients.

export interface SupabasePublicConfig {
  siteUrl: string;
  url: string;
  publishableKey: string;
}

function parseSiteUrl(value: string): string {
  let parsedUrl: URL;

  try {
    parsedUrl = new URL(value);
  } catch {
    throw new Error(
      "NEXT_PUBLIC_SITE_URL must be a valid URL.",
    );
  }

  if (
    parsedUrl.protocol !== "http:" &&
    parsedUrl.protocol !== "https:"
  ) {
    throw new Error(
      "NEXT_PUBLIC_SITE_URL must use HTTP or HTTPS.",
    );
  }

  if (
    parsedUrl.protocol !== "https:" &&
    parsedUrl.hostname !== "localhost"
  ) {
    throw new Error(
      "NEXT_PUBLIC_SITE_URL must use HTTPS outside local development.",
    );
  }

  return parsedUrl.origin;
}

export function getSupabasePublicConfig():
  SupabasePublicConfig {
  const rawSiteUrl =
    process.env.NEXT_PUBLIC_SITE_URL?.trim();

  const url =
    process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();

  const publishableKey =
    process.env
      .NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
      ?.trim();

  if (!rawSiteUrl) {
    throw new Error(
      "NEXT_PUBLIC_SITE_URL is not configured.",
    );
  }

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
    siteUrl: parseSiteUrl(rawSiteUrl),
    url: url.replace(/\/+$/, ""),
    publishableKey,
  };
}