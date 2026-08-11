// File: /frontend/features/learning-profile/routing.ts
// Purpose: Maps each learning-profile onboarding step to its
// protected application route and readable interface label.

import type {
  OnboardingStep,
} from "./constants";

export const ONBOARDING_STEP_ROUTES:
  Record<OnboardingStep, string> = {
    1: "/onboarding/profile",
    2: "/onboarding/study-preferences",
    3: "/onboarding/study-challenges",
    4: "/onboarding/subjects",
    5: "/onboarding/availability",
    6: "/onboarding/review",
  };

export const ONBOARDING_STEP_LABELS:
  Record<OnboardingStep, string> = {
    1: "Student profile",
    2: "Study preferences",
    3: "Study challenges",
    4: "Subjects and output confidence",
    5: "Available schedule",
    6: "Review and finish",
  };

export function getOnboardingStepPath(
  step: OnboardingStep,
): string {
  return ONBOARDING_STEP_ROUTES[step];
}