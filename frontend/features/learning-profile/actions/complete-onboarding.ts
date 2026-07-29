// File: /frontend/features/learning-profile/actions/complete-onboarding.ts
// Purpose: Performs the final database-controlled onboarding
// completion check and redirects successful students to the dashboard.

"use server";

import {
  revalidatePath,
} from "next/cache";
import {
  redirect,
} from "next/navigation";

import {
  LearningProfileDataError,
} from "../server/errors";
import {
  completeOnboarding,
} from "../server/mutations";
import type {
  CompleteOnboardingActionState,
} from "./types";

export async function completeOnboardingAction(
  previousState:
    CompleteOnboardingActionState,
  formData: FormData,
): Promise<CompleteOnboardingActionState> {
  void previousState;
  void formData;

  try {
    await completeOnboarding();
  } catch (error) {
    if (
      error instanceof
      LearningProfileDataError
    ) {
      if (
        error.code ===
        "ONBOARDING_INCOMPLETE"
      ) {
        return {
          status: "error",
          message:
            "Some required learning-profile information is still incomplete. Review each section and try again.",
        };
      }

      if (
        error.code ===
        "UNAUTHENTICATED"
      ) {
        return {
          status: "error",
          message:
            "Your session could not be verified. Sign in again before completing onboarding.",
        };
      }

      return {
        status: "error",
        message:
          "The onboarding completion check could not be finished. Check your connection and try again.",
      };
    }

    throw error;
  }

  revalidatePath("/onboarding");
  revalidatePath("/onboarding/review");
  revalidatePath("/dashboard");
  revalidatePath("/profile");

  redirect("/dashboard");
}