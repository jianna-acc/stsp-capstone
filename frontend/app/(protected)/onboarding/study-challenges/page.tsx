// File: /frontend/app/(protected)/onboarding/study-challenges/page.tsx
// Purpose: Loads and displays Step 3 of learning-profile
// onboarding for the authenticated student.

import type { Metadata } from "next";
import { redirect } from "next/navigation";

import type { StudyChallengesFormValues } from "@/features/learning-profile/actions/types";
import { OnboardingShell } from "@/features/learning-profile/components/OnboardingShell";
import { StudyChallengesForm } from "@/features/learning-profile/components/StudyChallengesForm";
import {
  ONBOARDING_STEPS,
  STUDY_CHALLENGES,
  type StudyChallenge,
} from "@/features/learning-profile/constants";
import { getOnboardingSnapshot } from "@/features/learning-profile/server/queries";

export const metadata: Metadata = {
  title:
    "Study Challenges | STS Capstone Project",
  description:
    "Identify common study challenges and estimated task-completion time.",
};

function isStudyChallenge(
  value: string,
): value is StudyChallenge {
  return STUDY_CHALLENGES.includes(
    value as StudyChallenge,
  );
}

export default async function StudyChallengesPage() {
  const snapshot =
    await getOnboardingSnapshot();


  if (
    !snapshot.progress.sections
      .studentProfile
  ) {
    redirect("/onboarding/profile");
  }

  if (
    !snapshot.progress.sections
      .studyPreferences
  ) {
    redirect(
      "/onboarding/study-preferences",
    );
  }

  const learningProfile =
    snapshot.learningProfile;

  const initialValues:
    StudyChallengesFormValues = {
      commonStudyChallenges:
        learningProfile
          ?.common_study_challenges
          .filter(isStudyChallenge) ??
        [],

      estimatedTaskCompletionMinutes:
        learningProfile
          ?.estimated_task_completion_minutes
          ?.toString() ?? "",
    };

  return (
    <OnboardingShell
      currentStep={
        ONBOARDING_STEPS
          .STUDY_CHALLENGES
      }
      description="Tell us which difficulties commonly affect your study sessions and how long typical academic tasks take you."
      percentage={
        snapshot.progress.percentage
      }
      title="Identify your study challenges"
    >
      <StudyChallengesForm
        initialValues={initialValues}
      />
    </OnboardingShell>
  );
}