// File: /frontend/app/(protected)/onboarding/profile/page.tsx
// Purpose: Loads and displays Step 1 of learning-profile
// onboarding for the authenticated student.

import type {
  Metadata,
} from "next";

import type {
  StudentProfileFormValues,
} from "@/features/learning-profile/actions/types";
import {
  ONBOARDING_STEPS,
} from "@/features/learning-profile/constants";
import {
  OnboardingShell,
} from "@/features/learning-profile/components/OnboardingShell";
import {
  StudentProfileForm,
} from "@/features/learning-profile/components/StudentProfileForm";
import {
  getOnboardingSnapshot,
} from "@/features/learning-profile/server/queries";

export const metadata: Metadata = {
  title:
    "Student Profile | STS Capstone Project",
  description:
    "Complete the first step of your personalized learning profile.",
};

export default async function StudentProfilePage() {
  const snapshot =
    await getOnboardingSnapshot();



  const initialValues:
    StudentProfileFormValues = {
      fullName:
        snapshot.profile.full_name ??
        "",
      schoolName:
        snapshot.profile.school_name ??
        "",
      programName:
        snapshot.profile.program_name ??
        "",
      yearLevel:
        snapshot.profile.year_level ??
        "",
      timezone:
        snapshot.profile.timezone ||
        "Asia/Manila",
    };

  return (
    <OnboardingShell
      currentStep={
        ONBOARDING_STEPS
          .STUDENT_PROFILE
      }
      description="Tell us about your academic background so future study plans and recommendations can match your context."
      percentage={
        snapshot.progress.percentage
      }
      title="Set up your student profile"
    >
      <StudentProfileForm
        initialValues={initialValues}
      />
    </OnboardingShell>
  );
}