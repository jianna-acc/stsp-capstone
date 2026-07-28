// File: /frontend/app/auth/confirm/route.ts
// Purpose: Verifies Supabase email tokens or exchanges PKCE
// authorization codes, creates a cookie-based session, and
// redirects the student safely.

import type {
  EmailOtpType,
} from "@supabase/supabase-js";
import {
  type NextRequest,
  NextResponse,
} from "next/server";

import {
  getSafeInternalPath,
} from "@/features/auth/redirects";
import {
  createClient,
} from "@/lib/supabase/server";

const SUPPORTED_EMAIL_OTP_TYPES =
  new Set<EmailOtpType>([
    "email",
    "signup",
  ]);

function isSupportedEmailOtpType(
  value: string | null,
): value is EmailOtpType {
  return (
    value !== null &&
    SUPPORTED_EMAIL_OTP_TYPES.has(
      value as EmailOtpType,
    )
  );
}

export async function GET(
  request: NextRequest,
): Promise<NextResponse> {
  const searchParams =
    request.nextUrl.searchParams;

  const code =
    searchParams.get("code");

  const tokenHash =
    searchParams.get("token_hash");

  const type =
    searchParams.get("type");

  const nextPath =
    getSafeInternalPath(
      searchParams.get("next"),
      "/login?confirmed=1",
    );

  const supabase =
    await createClient();

  /*
   * Flow 1:
   * The default Supabase PKCE confirmation link redirects
   * back to the application with an authorization code.
   */
  if (code) {
    const { error } =
      await supabase.auth
        .exchangeCodeForSession(code);

    if (!error) {
      return NextResponse.redirect(
        new URL(
          nextPath,
          request.nextUrl.origin,
        ),
      );
    }
  }

  /*
   * Flow 2:
   * A customized email template sends token_hash and type
   * directly to this Route Handler.
   */
  if (
    tokenHash &&
    isSupportedEmailOtpType(type)
  ) {
    const { error } =
      await supabase.auth.verifyOtp({
        token_hash: tokenHash,
        type,
      });

    if (!error) {
      return NextResponse.redirect(
        new URL(
          nextPath,
          request.nextUrl.origin,
        ),
      );
    }
  }

  return NextResponse.redirect(
    new URL(
      "/auth/auth-code-error",
      request.nextUrl.origin,
    ),
  );
}