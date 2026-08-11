// File: /frontend/features/learning-profile/constants.ts
// Purpose: Defines onboarding steps and allowed learning-profile
// values shared by validation and future questionnaire components.

export const ONBOARDING_STEPS = {
  STUDENT_PROFILE: 1,
  STUDY_PREFERENCES: 2,
  STUDY_CHALLENGES: 3,
  SUBJECT_CONFIDENCE: 4,
  STUDY_AVAILABILITY: 5,
  REVIEW: 6,
} as const;

export type OnboardingStep =
  (typeof ONBOARDING_STEPS)[keyof typeof ONBOARDING_STEPS];

export const ONBOARDING_STEP_COUNT = 6;

export const PREFERRED_STUDY_TIMES = [
  "early_morning",
  "morning",
  "afternoon",
  "evening",
  "late_night",
] as const;

export type PreferredStudyTime =
  (typeof PREFERRED_STUDY_TIMES)[number];

export const STUDY_CHALLENGES = [
  "procrastination",
  "distractions",
  "time_management",
  "motivation",
  "difficult_content",
  "heavy_workload",
  "forgetfulness",
  "test_anxiety",
  "other",
] as const;

export type StudyChallenge =
  (typeof STUDY_CHALLENGES)[number];

export const LEARNING_METHODS = [
  "visual",
  "auditory",
  "reading_writing",
  "kinesthetic",
  "collaborative",
  "mixed",
] as const;

export type LearningMethod =
  (typeof LEARNING_METHODS)[number];

export const SUBJECT_STRENGTHS = [
  "strong",
  "weak",
] as const;

export type SubjectStrength =
  (typeof SUBJECT_STRENGTHS)[number];

export const WEEKDAYS = [
  {
    value: 1,
    label: "Monday",
  },
  {
    value: 2,
    label: "Tuesday",
  },
  {
    value: 3,
    label: "Wednesday",
  },
  {
    value: 4,
    label: "Thursday",
  },
  {
    value: 5,
    label: "Friday",
  },
  {
    value: 6,
    label: "Saturday",
  },
  {
    value: 7,
    label: "Sunday",
  },
] as const;

export const LEARNING_OUTPUT_TYPES = [
  "writing",
  "computation",
  "research",
  "presentation",
  "creative",
  "reading_analysis",
  "memorization",
] as const;

export type LearningOutputType =
  (typeof LEARNING_OUTPUT_TYPES)[number];

export const LEARNING_OUTPUT_TYPE_LABELS: Record<
  LearningOutputType,
  string
> = {
  writing: "Essay / Writing",
  computation:
    "Computation / Problem Solving",
  research: "Research",
  presentation:
    "Presentation / Oral",
  creative: "Creative Output",
  reading_analysis:
    "Reading / Analysis",
  memorization:
    "Memorization / Recall",
};