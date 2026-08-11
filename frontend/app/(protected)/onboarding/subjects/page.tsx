// File: /frontend/app/(protected)/onboarding/subjects/page.tsx
// Purpose: Loads and displays Step 4 of learning-profile
// onboarding for the authenticated student.

import type { Metadata } from "next";
import { redirect } from "next/navigation";

import type {
  SubjectsFormValues,
} from "@/features/learning-profile/actions/types";
import { OnboardingShell } from "@/features/learning-profile/components/OnboardingShell";
import { SubjectsForm } from "@/features/learning-profile/components/SubjectsForm";
import { ONBOARDING_STEPS } from "@/features/learning-profile/constants";
import { getOnboardingSnapshot } from "@/features/learning-profile/server/queries";

export const metadata: Metadata = {
  title:
    "Subjects and Confidence | STS Capstone Project",
  description:
    "Identify strong and weak subjects and assign confidence ratings.",
};

export default async function SubjectsPage() {
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

  if (
    !snapshot.progress.sections
      .studyChallenges
  ) {
    redirect(
      "/onboarding/study-challenges",
    );
  }

  const initialValues:
    SubjectsFormValues = {
      subjects:
        snapshot.subjects.map(
          (subject) => ({
            subjectName:
              subject.subject_name,
            subjectStrength:
              subject.subject_strength,
          }),
        ),

      outputConfidences:
        snapshot.outputConfidences.map(
          (confidence) => ({
            outputType:
              confidence.output_type,
            confidenceLevel:
              String(
                confidence.confidence_level,
              ),
          }),
        ),
    };

  return (
    <OnboardingShell
      currentStep={
        ONBOARDING_STEPS
          .SUBJECT_CONFIDENCE
      }
      description="Identify the subjects where you feel strongest, the subjects where you need support, and your confidence level in each one."
      percentage={
        snapshot.progress.percentage
      }
      title="Map your subject confidence"
    >
      <SubjectsForm
        initialValues={initialValues}
      />
    </OnboardingShell>
  );
}