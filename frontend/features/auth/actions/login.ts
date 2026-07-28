// File: /frontend/features/auth/actions/login.ts
// Purpose: Validates password-login submissions, authenticates
// students through Supabase, and redirects them safely.

"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

import type {
  LoginActionState,
} from "../types";
import {
  hasLoginErrors,
  validateLoginForm,
} from "../validation";

interface LoginErrorDetails {
  code?: string;
  status?: number;
}

function getLoginErrorMessage(
  error: LoginErrorDetails,
): string {
  if (
    error.status === 429 ||
    error.code ===
      "over_request_rate_limit"
  ) {
    return "Too many sign-in attempts were made. Wait a moment and try again.";
  }

  if (
    error.code ===
    "email_not_confirmed"
  ) {
    return "Confirm your email address before signing in. Check the confirmation message sent during registration.";
  }

  /*
   * Do not reveal whether a specific email address exists.
   * Incorrect emails and passwords receive the same message.
   */
  return "The email address or password is incorrect.";
}

export async function loginAction(
  previousState: LoginActionState,
  formData: FormData,
): Promise<LoginActionState> {
  void previousState;

  const validation =
    validateLoginForm(formData);

  if (hasLoginErrors(validation.errors)) {
    return {
      status: "error",
      message:
        "Review the highlighted information before continuing.",
      fieldErrors: validation.errors,
      values: validation.values,
    };
  }

  const supabase = await createClient();

  const { data, error } =
    await supabase.auth
      .signInWithPassword({
        email: validation.input.email,
        password:
          validation.input.password,
      });

  if (error) {
    return {
      status: "error",
      message: getLoginErrorMessage(
        error,
      ),
      fieldErrors: {},
      values: validation.values,
    };
  }

  if (!data.user || !data.session) {
    return {
      status: "error",
      message:
        "The sign-in request completed without creating a session. Try again.",
      fieldErrors: {},
      values: validation.values,
    };
  }

  redirect(validation.input.nextPath);
}