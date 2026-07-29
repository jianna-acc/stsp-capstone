// File: /frontend/app/(protected)/onboarding/availability/page.tsx
// Purpose: Loads and displays Step 5 of learning-profile
// onboarding for the authenticated student.

import type { Metadata } from "next";
import { redirect } from "next/navigation";

import type {
  AvailabilityFormValues,
} from "@/features/learning-profile/actions/types";
import { AvailabilityForm } from "@/features/learning-profile/components/AvailabilityForm";
import { OnboardingShell } from "@/features/learning-profile/components/OnboardingShell";
import { ONBOARDING_STEPS } from "@/features/learning-profile/constants";
import { getOnboardingSnapshot } from "@/features/learning-profile/server/queries";

export const metadata: Metadata = {
  title:
    "Study Availability | STS Capstone Project",
  description:
    "Set the weekly periods available for study sessions.",
};

function normalizeDatabaseTime(
  value: string,
): string {
  return value.slice(0, 5);
}

export default async function AvailabilityPage() {
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

  if (
    !snapshot.progress.sections
      .subjectConfidence
  ) {
    redirect("/onboarding/subjects");
  }

  const initialValues:
    AvailabilityFormValues = {
      slots: snapshot.availability.map(
        (slot) => ({
          dayOfWeek:
            slot.day_of_week.toString(),
          startTime:
            normalizeDatabaseTime(
              slot.start_time,
            ),
          endTime:
            normalizeDatabaseTime(
              slot.end_time,
            ),
        }),
      ),
    };

  return (
    <OnboardingShell
      currentStep={
        ONBOARDING_STEPS
          .STUDY_AVAILABILITY
      }
      description="Add the days and times when you are normally available. These periods will later help the system create realistic study plans."
      percentage={
        snapshot.progress.percentage
      }
      title="Set your weekly availability"
    >
      <AvailabilityForm
        initialValues={initialValues}
      />
    </OnboardingShell>
  );
}