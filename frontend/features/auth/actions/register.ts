// File: /frontend/features/auth/actions/register.ts
// Purpose: Validates registration submissions and creates
// Supabase Auth users through a Next.js Server Action.

"use server";

import { redirect } from "next/navigation";

import {
  getSupabasePublicConfig,
} from "@/lib/supabase/config";
import {
  createClient,
} from "@/lib/supabase/server";

import type {
  RegisterActionState,
} from "../types";
import {
  hasRegistrationErrors,
  validateRegistrationForm,
} from "../validation";

function getSignupErrorMessage(
  status?: number,
): string {
  if (status === 429) {
    return "Too many registration attempts were made. Wait a moment and try again.";
  }

  return "We could not create your account. Review your information and try again.";
}

export async function registerAction(
  previousState: RegisterActionState,
  formData: FormData,
): Promise<RegisterActionState> {
  void previousState;

  const validation =
    validateRegistrationForm(formData);

  if (
    hasRegistrationErrors(validation.errors)
  ) {
    return {
      status: "error",
      message:
        "Review the highlighted information before continuing.",
      fieldErrors: validation.errors,
      values: validation.values,
    };
  }

  const supabase = await createClient();

  const { siteUrl } =
    getSupabasePublicConfig();

  const { data, error } =
    await supabase.auth.signUp({
      email: validation.input.email,
      password: validation.input.password,
      options: {
        data: {
          full_name:
            validation.input.fullName,
        },
        emailRedirectTo:
          `${siteUrl}/auth/confirm`,
      },
    });

  if (error) {
    return {
      status: "error",
      message: getSignupErrorMessage(
        error.status,
      ),
      fieldErrors: {},
      values: validation.values,
    };
  }

  if (!data.user) {
    return {
      status: "error",
      message:
        "Supabase did not return a new account. Try again in a moment.",
      fieldErrors: {},
      values: validation.values,
    };
  }

  redirect("/register/check-email");
}