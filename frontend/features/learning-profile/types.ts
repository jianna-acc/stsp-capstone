// File: /frontend/features/learning-profile/types.ts
// Purpose: Defines typed input models, database row aliases,
// and complete onboarding-data snapshots.

import type {
  Tables,
} from "@/types/database";

import type {
  LearningMethod,
  OnboardingStep,
  PreferredStudyTime,
  StudyChallenge,
  SubjectStrength,
} from "./constants";

export type StudentProfileRow =
  Tables<"profiles">;

export type LearningProfileRow =
  Tables<"learning_profiles">;

export type LearningSubjectRow =
  Tables<"learning_profile_subjects">;

export type StudyAvailabilityRow =
  Tables<"study_availability">;

export interface StudentProfileInput {
  fullName: string;
  schoolName: string;
  programName: string;
  yearLevel: string;
  timezone: string;
}

export interface StudyPreferencesInput {
  preferredStudyDurationMinutes: number;
  preferredStudyTimes:
    readonly PreferredStudyTime[];
  preferredLearningMethods:
    readonly LearningMethod[];
}

export interface StudyChallengesInput {
  commonStudyChallenges:
    readonly StudyChallenge[];
  estimatedTaskCompletionMinutes: number;
}

export interface LearningSubjectInput {
  subjectName: string;
  subjectStrength: SubjectStrength;
  confidenceLevel: number;
}

export interface StudyAvailabilityInput {
  dayOfWeek: number;
  startTime: string;
  endTime: string;
}

export interface OnboardingSectionStatus {
  studentProfile: boolean;
  studyPreferences: boolean;
  studyChallenges: boolean;
  subjectConfidence: boolean;
  studyAvailability: boolean;
  reviewAndCompletion: boolean;
}

export interface OnboardingProgress {
  currentStep: OnboardingStep;
  completedSectionCount: number;
  totalSectionCount: number;
  percentage: number;
  sections: OnboardingSectionStatus;
}

export interface OnboardingSnapshot {
  userId: string;
  profile: StudentProfileRow;
  learningProfile: LearningProfileRow | null;
  subjects: LearningSubjectRow[];
  availability: StudyAvailabilityRow[];
  progress: OnboardingProgress;
}