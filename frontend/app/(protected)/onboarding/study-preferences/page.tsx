// File: /frontend/app/(protected)/onboarding/study-preferences/page.tsx
// Purpose: Loads and displays Step 2 of learning-profile
// onboarding for the authenticated student.

import type {
  Metadata,
} from "next";
import {
  redirect,
} from "next/navigation";

import type {
  StudyPreferencesFormValues,
} from "@/features/learning-profile/actions/types";
import {
  StudyPreferencesForm,
} from "@/features/learning-profile/components/StudyPreferencesForm";
import {
  OnboardingShell,
} from "@/features/learning-profile/components/OnboardingShell";
import {
  LEARNING_METHODS,
  ONBOARDING_STEPS,
  PREFERRED_STUDY_TIMES,
  type LearningMethod,
  type PreferredStudyTime,
} from "@/features/learning-profile/constants";
import {
  getOnboardingSnapshot,
} from "@/features/learning-profile/server/queries";

export const metadata: Metadata = {
  title:
    "Study Preferences | Intelleap",
  description:
    "Configure preferred study duration, study times, and learning methods.",
};

function isPreferredStudyTime(
  value: string,
): value is PreferredStudyTime {
  return PREFERRED_STUDY_TIMES.includes(
    value as PreferredStudyTime,
  );
}

function isLearningMethod(
  value: string,
): value is LearningMethod {
  return LEARNING_METHODS.includes(
    value as LearningMethod,
  );
}

export default async function StudyPreferencesPage() {
  const snapshot =
    await getOnboardingSnapshot();


  if (
    !snapshot.progress.sections
      .studentProfile
  ) {
    redirect("/onboarding/profile");
  }

  const learningProfile =
    snapshot.learningProfile;

  const initialValues:
    StudyPreferencesFormValues = {
      preferredStudyDurationMinutes:
        learningProfile
          ?.preferred_study_duration_minutes
          ?.toString() ?? "",

      preferredStudyTimes:
        learningProfile
          ?.preferred_study_times
          .filter(isPreferredStudyTime) ??
        [],

      preferredLearningMethods:
        learningProfile
          ?.preferred_learning_methods
          .filter(isLearningMethod) ??
        [],
    };

  return (
    <OnboardingShell
      currentStep={
        ONBOARDING_STEPS
          .STUDY_PREFERENCES
      }
      description="Tell us when, how long, and through which methods you prefer to study. These answers will help personalize your future study plans."
      percentage={
        snapshot.progress.percentage
      }
      title="Set your study preferences"
    >
      <StudyPreferencesForm
        initialValues={initialValues}
      />
    </OnboardingShell>
  );
}