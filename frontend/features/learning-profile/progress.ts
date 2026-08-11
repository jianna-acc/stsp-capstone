// File: /frontend/features/learning-profile/progress.ts
// Purpose: Derives reliable onboarding progress from saved
// student-profile and learning-profile database records.

import {
  LEARNING_OUTPUT_TYPES,
  ONBOARDING_STEP_COUNT,
  type OnboardingStep,
} from "./constants";
import type {
  LearningOutputConfidenceRow,
  LearningProfileRow,
  LearningSubjectRow,
  OnboardingProgress,
  StudentProfileRow,
  StudyAvailabilityRow,
} from "./types";

interface ProgressSource {
  profile: StudentProfileRow;
  learningProfile:
    LearningProfileRow | null;
  subjects: LearningSubjectRow[];
  outputConfidences:
    LearningOutputConfidenceRow[];
  availability: StudyAvailabilityRow[];
}

function hasText(
  value: string | null,
): boolean {
  return Boolean(
    value?.trim(),
  );
}

function normalizeCurrentStep(
  value: number,
): OnboardingStep {
  const boundedValue =
    Math.min(
      ONBOARDING_STEP_COUNT,
      Math.max(
        1,
        value,
      ),
    );

  return boundedValue as OnboardingStep;
}

export function calculateOnboardingProgress({
  profile,
  learningProfile,
  subjects,
  outputConfidences,
  availability,
}: ProgressSource): OnboardingProgress {
  const studentProfileComplete =
    hasText(
      profile.full_name,
    ) &&
    hasText(
      profile.school_name,
    ) &&
    hasText(
      profile.program_name,
    ) &&
    hasText(
      profile.year_level,
    ) &&
    hasText(
      profile.timezone,
    );

  const studyPreferencesComplete =
    learningProfile !== null &&
    learningProfile
      .preferred_study_duration_minutes !==
      null &&
    learningProfile
      .preferred_study_times.length >
      0 &&
    learningProfile
      .preferred_learning_methods.length >
      0;

  const studyChallengesComplete =
    learningProfile !== null &&
    learningProfile
      .estimated_task_completion_minutes !==
      null &&
    learningProfile
      .common_study_challenges.length >
      0;

  const hasStrongSubject =
    subjects.some(
      (subject) =>
        subject.subject_strength ===
        "strong",
    );

  const hasWeakSubject =
    subjects.some(
      (subject) =>
        subject.subject_strength ===
        "weak",
    );

  const savedOutputTypes =
    new Set(
      outputConfidences.map(
        (confidence) =>
          confidence.output_type,
      ),
    );

  const hasAllOutputTypes =
    LEARNING_OUTPUT_TYPES.every(
      (outputType) =>
        savedOutputTypes.has(
          outputType,
        ),
    );

  const outputConfidenceComplete =
    outputConfidences.length ===
      LEARNING_OUTPUT_TYPES.length &&
    hasAllOutputTypes &&
    outputConfidences.every(
      (confidence) =>
        confidence.confidence_level >=
          1 &&
        confidence.confidence_level <=
          5,
    );

  /*
   * Keep the existing section key temporarily so the rest of
   * onboarding does not need a routing/progress rename yet.
   *
   * It now means:
   * - at least one strong subject
   * - at least one weak subject
   * - all seven output-confidence ratings completed
   */
  const subjectConfidenceComplete =
    hasStrongSubject &&
    hasWeakSubject &&
    outputConfidenceComplete;

  const studyAvailabilityComplete =
    availability.length > 0;

  const reviewAndCompletion =
    profile.onboarding_completed;

  const sections = {
    studentProfile:
      studentProfileComplete,
    studyPreferences:
      studyPreferencesComplete,
    studyChallenges:
      studyChallengesComplete,
    subjectConfidence:
      subjectConfidenceComplete,
    studyAvailability:
      studyAvailabilityComplete,
    reviewAndCompletion,
  };

  const completedSectionCount =
    Object.values(
      sections,
    ).filter(
      Boolean,
    ).length;

  return {
    currentStep:
      normalizeCurrentStep(
        profile.onboarding_current_step,
      ),
    completedSectionCount,
    totalSectionCount:
      ONBOARDING_STEP_COUNT,
    percentage:
      Math.round(
        (
          completedSectionCount /
          ONBOARDING_STEP_COUNT
        ) *
          100,
      ),
    sections,
  };
}