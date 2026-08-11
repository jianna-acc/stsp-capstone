// File: /frontend/features/learning-profile/actions/types.ts
// Purpose: Defines serializable action-state, form-value, and
// field-error types for learning-profile onboarding forms.

import type {
  LearningMethod,
  PreferredStudyTime,
  StudyChallenge,
} from "../constants";

// ============================================================
// Student profile
// ============================================================

export interface StudentProfileFormValues {
  fullName: string;
  schoolName: string;
  programName: string;
  yearLevel: string;
  timezone: string;
}

export interface StudentProfileFieldErrors {
  fullName?: string;
  schoolName?: string;
  programName?: string;
  yearLevel?: string;
  timezone?: string;
}

export interface StudentProfileActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: StudentProfileFieldErrors;
  values: StudentProfileFormValues;
}

export function createInitialStudentProfileState(
  values?: Partial<StudentProfileFormValues>,
): StudentProfileActionState {
  return {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      fullName: values?.fullName ?? "",
      schoolName: values?.schoolName ?? "",
      programName: values?.programName ?? "",
      yearLevel: values?.yearLevel ?? "",
      timezone: values?.timezone ?? "Asia/Manila",
    },
  };
}

// ============================================================
// Study preferences
// ============================================================

export interface StudyPreferencesFormValues {
  preferredStudyDurationMinutes: string;
  preferredStudyTimes: PreferredStudyTime[];
  preferredLearningMethods: LearningMethod[];
}

export interface StudyPreferencesFieldErrors {
  preferredStudyDurationMinutes?: string;
  preferredStudyTimes?: string;
  preferredLearningMethods?: string;
}

export interface StudyPreferencesActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: StudyPreferencesFieldErrors;
  values: StudyPreferencesFormValues;
}

export function createInitialStudyPreferencesState(
  values?: Partial<StudyPreferencesFormValues>,
): StudyPreferencesActionState {
  return {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      preferredStudyDurationMinutes:
        values?.preferredStudyDurationMinutes ?? "",
      preferredStudyTimes:
        values?.preferredStudyTimes ?? [],
      preferredLearningMethods:
        values?.preferredLearningMethods ?? [],
    },
  };
}

// ============================================================
// Study challenges
// ============================================================

export interface StudyChallengesFormValues {
  commonStudyChallenges: StudyChallenge[];
  estimatedTaskCompletionMinutes: string;
}

export interface StudyChallengesFieldErrors {
  commonStudyChallenges?: string;
  estimatedTaskCompletionMinutes?: string;
}

export interface StudyChallengesActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: StudyChallengesFieldErrors;
  values: StudyChallengesFormValues;
}

export function createInitialStudyChallengesState(
  values?: Partial<StudyChallengesFormValues>,
): StudyChallengesActionState {
  return {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      commonStudyChallenges:
        values?.commonStudyChallenges ?? [],
      estimatedTaskCompletionMinutes:
        values?.estimatedTaskCompletionMinutes ?? "",
    },
  };
}

// ============================================================
// Subjects and confidence
// ============================================================

export interface SubjectFormValue {
  subjectName: string;
  subjectStrength: string;
}

export interface OutputConfidenceFormValue {
  outputType: string;
  confidenceLevel: string;
}

export interface SubjectsFormValues {
  subjects: SubjectFormValue[];
  outputConfidences:
    OutputConfidenceFormValue[];
}

export interface SubjectsFieldErrors {
  [fieldName: string]: string | undefined;

  subjects?: string;
  strongSubjects?: string;
  weakSubjects?: string;
  outputConfidences?: string;
}

export interface SubjectsActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: SubjectsFieldErrors;
  values: SubjectsFormValues;
}

const DEFAULT_SUBJECT_ROWS:
  SubjectFormValue[] = [
    {
      subjectName: "",
      subjectStrength: "strong",
    },
    {
      subjectName: "",
      subjectStrength: "weak",
    },
  ];

const DEFAULT_OUTPUT_CONFIDENCE_ROWS:
  OutputConfidenceFormValue[] = [
    {
      outputType: "writing",
      confidenceLevel: "3",
    },
    {
      outputType: "computation",
      confidenceLevel: "3",
    },
    {
      outputType: "research",
      confidenceLevel: "3",
    },
    {
      outputType: "presentation",
      confidenceLevel: "3",
    },
    {
      outputType: "creative",
      confidenceLevel: "3",
    },
    {
      outputType: "reading_analysis",
      confidenceLevel: "3",
    },
    {
      outputType: "memorization",
      confidenceLevel: "3",
    },
  ];

export function createInitialSubjectsState(
  values?: Partial<SubjectsFormValues>,
): SubjectsActionState {
  const subjects =
    values?.subjects &&
    values.subjects.length > 0
      ? values.subjects
      : DEFAULT_SUBJECT_ROWS;

  const outputConfidences =
    values?.outputConfidences &&
    values.outputConfidences.length > 0
      ? values.outputConfidences
      : DEFAULT_OUTPUT_CONFIDENCE_ROWS;

  return {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      subjects: subjects.map(
        (subject) => ({
          ...subject,
        }),
      ),
      outputConfidences:
        outputConfidences.map(
          (confidence) => ({
            ...confidence,
          }),
        ),
    },
  };
}

// ============================================================
// Study availability
// ============================================================

export interface AvailabilitySlotFormValue {
  dayOfWeek: string;
  startTime: string;
  endTime: string;
}

export interface AvailabilityFormValues {
  slots: AvailabilitySlotFormValue[];
}

export interface AvailabilityFieldErrors {
  [fieldName: string]: string | undefined;

  availability?: string;
}

export interface AvailabilityActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: AvailabilityFieldErrors;
  values: AvailabilityFormValues;
}

const DEFAULT_AVAILABILITY_ROWS:
  AvailabilitySlotFormValue[] = [
    {
      dayOfWeek: "1",
      startTime: "18:00",
      endTime: "19:00",
    },
  ];

export function createInitialAvailabilityState(
  values?: Partial<AvailabilityFormValues>,
): AvailabilityActionState {
  const slots =
    values?.slots &&
    values.slots.length > 0
      ? values.slots
      : DEFAULT_AVAILABILITY_ROWS;

  return {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      slots: slots.map((slot) => ({
        ...slot,
      })),
    },
  };
}

// ============================================================
// Onboarding completion
// ============================================================

export interface CompleteOnboardingActionState {
  status: "idle" | "error";
  message: string;
}

export const initialCompleteOnboardingActionState:
  CompleteOnboardingActionState = {
    status: "idle",
    message: "",
  };