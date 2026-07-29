// File: /frontend/app/(protected)/onboarding/page.tsx
// Purpose: Resumes authenticated students at their last saved
// onboarding step or sends completed students to the dashboard.

import {
  redirect,
} from "next/navigation";

import {
  getOnboardingStepPath,
} from "@/features/learning-profile/routing";
import {
  getOnboardingSnapshot,
} from "@/features/learning-profile/server/queries";

export default async function OnboardingPage():
  Promise<never> {
  const snapshot =
    await getOnboardingSnapshot();

  if (
    snapshot.profile
      .onboarding_completed
  ) {
    redirect("/dashboard");
  }

  redirect(
    getOnboardingStepPath(
      snapshot.progress.currentStep,
    ),
  );
}