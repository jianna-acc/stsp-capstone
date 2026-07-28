// File: /frontend/features/learning-profile/server/guards.ts
// Purpose: Protects application pages that require a completed
// student learning profile.

import "server-only";

import { redirect } from "next/navigation";

import type {
  OnboardingSnapshot,
} from "../types";
import {
  getOnboardingSnapshot,
} from "./queries";

export async function requireCompletedLearningProfile():
  Promise<OnboardingSnapshot> {
  const snapshot =
    await getOnboardingSnapshot();

  if (
    !snapshot.profile
      .onboarding_completed
  ) {
    redirect("/onboarding");
  }

  return snapshot;
}