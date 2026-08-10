// File: /frontend/features/learning-profile/server/mutations.ts
// Purpose: Saves validated student-profile and learning-profile
// sections through the authenticated Supabase server client.

import "server-only";

import type {
  SupabaseClient,
} from "@supabase/supabase-js";

import {
  createClient,
} from "@/lib/supabase/server";
import type {
  Database,
  Json,
} from "@/types/database";

import {
  ONBOARDING_STEPS,
  type OnboardingStep,
} from "../constants";
import type {
  LearningSubjectInput,
  StudentProfileInput,
  StudyAvailabilityInput,
  StudyChallengesInput,
  StudyPreferencesInput,
  LearningOutputConfidenceInput,
} from "../types";
import {
  validateLearningSubjects,
  validateStudentProfileInput,
  validateStudyAvailability,
  validateStudyChallengesInput,
  validateStudyPreferencesInput,
  validateLearningOutputConfidences,
} from "../validation";
import {
  requireAuthenticatedUserId,
} from "./auth";
import {
  LearningProfileDataError,
} from "./errors";

interface MutationContext {
  supabase:
    SupabaseClient<Database>;
  userId: string;
}

async function createMutationContext():
  Promise<MutationContext> {
  const supabase = await createClient();

  const userId =
    await requireAuthenticatedUserId(
      supabase,
    );

  return {
    supabase,
    userId,
  };
}

async function advanceOnboardingStep(
  supabase: SupabaseClient<Database>,
  userId: string,
  nextStep: OnboardingStep,
): Promise<void> {
  const {
    data: profile,
    error: readError,
  } = await supabase
    .from("profiles")
    .select("onboarding_current_step")
    .eq("id", userId)
    .single();

  if (
    readError ||
    !profile
  ) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The onboarding progress could not be read.",
      {
        cause: readError,
      },
    );
  }

  if (
    profile.onboarding_current_step >=
    nextStep
  ) {
    return;
  }

  const {
    error: updateError,
  } = await supabase
    .from("profiles")
    .update({
      onboarding_current_step:
        nextStep,
    })
    .eq("id", userId);

  if (updateError) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The onboarding progress could not be saved.",
      {
        cause: updateError,
      },
    );
  }
}

export async function saveStudentProfile(
  input: StudentProfileInput,
): Promise<void> {
  const normalizedInput =
    validateStudentProfileInput(input);

  const {
    supabase,
    userId,
  } = await createMutationContext();

  const {
    error,
  } = await supabase
    .from("profiles")
    .update({
      full_name:
        normalizedInput.fullName,
      school_name:
        normalizedInput.schoolName,
      program_name:
        normalizedInput.programName,
      year_level:
        normalizedInput.yearLevel,
      timezone:
        normalizedInput.timezone,
    })
    .eq("id", userId);

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The student profile could not be saved.",
      {
        cause: error,
      },
    );
  }

  await advanceOnboardingStep(
    supabase,
    userId,
    ONBOARDING_STEPS
      .STUDY_PREFERENCES,
  );
}

export async function saveStudyPreferences(
  input: StudyPreferencesInput,
): Promise<void> {
  const normalizedInput =
    validateStudyPreferencesInput(input);

  const {
    supabase,
    userId,
  } = await createMutationContext();

  const {
    error,
  } = await supabase
    .from("learning_profiles")
    .upsert(
      {
        user_id: userId,
        preferred_study_duration_minutes:
          normalizedInput
            .preferredStudyDurationMinutes,
        preferred_study_times:
          [
            ...normalizedInput
              .preferredStudyTimes,
          ],
        preferred_learning_methods:
          [
            ...normalizedInput
              .preferredLearningMethods,
          ],
      },
      {
        onConflict: "user_id",
      },
    );

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The study preferences could not be saved.",
      {
        cause: error,
      },
    );
  }

  await advanceOnboardingStep(
    supabase,
    userId,
    ONBOARDING_STEPS
      .STUDY_CHALLENGES,
  );
}

export async function saveStudyChallenges(
  input: StudyChallengesInput,
): Promise<void> {
  const normalizedInput =
    validateStudyChallengesInput(input);

  const {
    supabase,
    userId,
  } = await createMutationContext();

  const {
    error,
  } = await supabase
    .from("learning_profiles")
    .upsert(
      {
        user_id: userId,
        common_study_challenges:
          [
            ...normalizedInput
              .commonStudyChallenges,
          ],
        estimated_task_completion_minutes:
          normalizedInput
            .estimatedTaskCompletionMinutes,
      },
      {
        onConflict: "user_id",
      },
    );

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The study challenges could not be saved.",
      {
        cause: error,
      },
    );
  }

  await advanceOnboardingStep(
    supabase,
    userId,
    ONBOARDING_STEPS
      .SUBJECT_CONFIDENCE,
  );
}

export async function replaceLearningSubjects(
  input:
    readonly LearningSubjectInput[],
): Promise<void> {
  const normalizedSubjects =
    validateLearningSubjects(input);

  const {
    supabase,
    userId,
  } = await createMutationContext();

  const payload = normalizedSubjects.map(
    (subject) => ({
      subject_name:
        subject.subjectName,
      subject_strength:
        subject.subjectStrength,

      // Legacy compatibility only.
      // Subject confidence is no longer
      // collected from the student.
      confidence_level: 3,
    }),
  ) as Json;

  const {
    error,
  } = await supabase.rpc(
    "replace_learning_profile_subjects",
    {
      p_subjects: payload,
    },
  );

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The subject-confidence information could not be saved.",
      {
        cause: error,
      },
    );
  }

  await advanceOnboardingStep(
    supabase,
    userId,
    ONBOARDING_STEPS
      .STUDY_AVAILABILITY,
  );
}

export async function replaceLearningOutputConfidences(
  input:
    readonly LearningOutputConfidenceInput[],
): Promise<void> {
  const normalizedConfidences =
    validateLearningOutputConfidences(
      input,
    );

  const {
    supabase,
  } = await createMutationContext();

  const payload =
    normalizedConfidences.map(
      (confidence) => ({
        output_type:
          confidence.outputType,
        confidence_level:
          confidence.confidenceLevel,
      }),
    ) as Json;

  const {
    error,
  } = await supabase.rpc(
    "replace_learning_output_confidences",
    {
      p_confidences: payload,
    },
  );

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "Your output confidence ratings could not be saved.",
      {
        cause: error,
      },
    );
  }
}

export async function replaceStudyAvailability(
  input:
    readonly StudyAvailabilityInput[],
): Promise<void> {
  const normalizedSlots =
    validateStudyAvailability(input);

  const {
    supabase,
    userId,
  } = await createMutationContext();

  const payload = normalizedSlots.map(
    (slot) => ({
      day_of_week:
        slot.dayOfWeek,
      start_time:
        `${slot.startTime}:00`,
      end_time:
        `${slot.endTime}:00`,
    }),
  ) as Json;

  const {
    error,
  } = await supabase.rpc(
    "replace_study_availability",
    {
      p_slots: payload,
    },
  );

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The available study schedule could not be saved.",
      {
        cause: error,
      },
    );
  }

  await advanceOnboardingStep(
    supabase,
    userId,
    ONBOARDING_STEPS.REVIEW,
  );
}

export async function completeOnboarding():
  Promise<void> {
  const {
    supabase,
  } = await createMutationContext();

  const {
    data,
    error,
  } = await supabase.rpc(
    "complete_learning_profile_onboarding",
  );

  if (error) {
    throw new LearningProfileDataError(
      "MUTATION_FAILED",
      "The onboarding completion check could not be performed.",
      {
        cause: error,
      },
    );
  }

  if (data !== true) {
    throw new LearningProfileDataError(
      "ONBOARDING_INCOMPLETE",
      "Complete every required learning-profile section before finishing onboarding.",
    );
  }
}