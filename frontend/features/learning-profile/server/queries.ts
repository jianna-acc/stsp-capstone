// File: /frontend/features/learning-profile/server/queries.ts
// Purpose: Loads the complete authenticated student onboarding
// snapshot from Supabase using user-scoped RLS queries.

import "server-only";

import type {
  SupabaseClient,
} from "@supabase/supabase-js";

import {
  createClient,
} from "@/lib/supabase/server";
import type {
  Database,
} from "@/types/database";

import {
  calculateOnboardingProgress,
} from "../progress";
import type {
  OnboardingSnapshot,
} from "../types";
import {
  requireAuthenticatedUserId,
} from "./auth";
import {
  LearningProfileDataError,
} from "./errors";

export async function getOnboardingSnapshotForUser(
  supabase: SupabaseClient<Database>,
  userId: string,
): Promise<OnboardingSnapshot> {
  const [
    profileResult,
    learningProfileResult,
    subjectsResult,
    outputConfidencesResult,
    availabilityResult,
  ] = await Promise.all([
    supabase
      .from("profiles")
      .select("*")
      .eq("id", userId)
      .single(),

    supabase
      .from("learning_profiles")
      .select("*")
      .eq("user_id", userId)
      .maybeSingle(),

    supabase
      .from("learning_profile_subjects")
      .select("*")
      .eq("user_id", userId)
      .order("subject_name", {
        ascending: true,
      }),

    supabase
      .from(
        "learning_output_confidences",
      )
      .select("*")
      .eq("user_id", userId)
      .order("output_type", {
        ascending: true,
      }),

    supabase
      .from("study_availability")
      .select("*")
      .eq("user_id", userId)
      .order("day_of_week", {
        ascending: true,
      })
      .order("start_time", {
        ascending: true,
      }),
  ]);

  if (
    profileResult.error ||
    !profileResult.data
  ) {
    throw new LearningProfileDataError(
      "PROFILE_NOT_FOUND",
      "The authenticated student profile could not be loaded.",
      {
        cause: profileResult.error,
      },
    );
  }

  if (learningProfileResult.error) {
    throw new LearningProfileDataError(
      "QUERY_FAILED",
      "The learning preferences could not be loaded.",
      {
        cause:
          learningProfileResult.error,
      },
    );
  }

  if (subjectsResult.error) {
    throw new LearningProfileDataError(
      "QUERY_FAILED",
      "The subject records could not be loaded.",
      {
        cause:
          subjectsResult.error,
      },
    );
  }

  if (
    outputConfidencesResult.error
  ) {
    throw new LearningProfileDataError(
      "QUERY_FAILED",
      "The output confidence ratings could not be loaded.",
      {
        cause:
          outputConfidencesResult.error,
      },
    );
  }

  if (availabilityResult.error) {
    throw new LearningProfileDataError(
      "QUERY_FAILED",
      "The study schedule could not be loaded.",
      {
        cause:
          availabilityResult.error,
      },
    );
  }

  const snapshotWithoutProgress = {
    userId,
    profile:
      profileResult.data,
    learningProfile:
      learningProfileResult.data,
    subjects:
      subjectsResult.data ?? [],
    outputConfidences:
      outputConfidencesResult.data ??
      [],
    availability:
      availabilityResult.data ?? [],
  };

  return {
    ...snapshotWithoutProgress,

    progress:
      calculateOnboardingProgress(
        snapshotWithoutProgress,
      ),
  };
}

export async function getOnboardingSnapshot():
Promise<OnboardingSnapshot> {
  const supabase =
    await createClient();

  const userId =
    await requireAuthenticatedUserId(
      supabase,
    );

  return getOnboardingSnapshotForUser(
    supabase,
    userId,
  );
}

export async function requireCompletedOnboarding():
Promise<OnboardingSnapshot> {
  const snapshot =
    await getOnboardingSnapshot();

  if (
    !snapshot.profile
      .onboarding_completed
  ) {
    throw new LearningProfileDataError(
      "ONBOARDING_INCOMPLETE",
      "The student learning profile is incomplete.",
    );
  }

  return snapshot;
}