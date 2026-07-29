// File: /frontend/features/learning-profile/display.ts
// Purpose: Converts saved learning-profile values into readable
// labels for the review, dashboard, and student-profile pages.

import {
  WEEKDAYS,
  type LearningMethod,
  type PreferredStudyTime,
  type StudyChallenge,
  type SubjectStrength,
} from "./constants";

const STUDY_TIME_LABELS:
  Record<PreferredStudyTime, string> = {
    early_morning: "Early morning",
    morning: "Morning",
    afternoon: "Afternoon",
    evening: "Evening",
    late_night: "Late night",
  };

const LEARNING_METHOD_LABELS:
  Record<LearningMethod, string> = {
    visual: "Visual",
    auditory: "Auditory",
    reading_writing: "Reading and writing",
    kinesthetic: "Hands-on",
    collaborative: "Collaborative",
    mixed: "Mixed approach",
  };

const STUDY_CHALLENGE_LABELS:
  Record<StudyChallenge, string> = {
    procrastination: "Procrastination",
    distractions: "Distractions",
    time_management: "Time management",
    motivation: "Lack of motivation",
    difficult_content: "Difficult lessons",
    heavy_workload: "Heavy workload",
    forgetfulness: "Forgetfulness",
    test_anxiety: "Test anxiety",
    other: "Other challenges",
  };

const SUBJECT_STRENGTH_LABELS:
  Record<SubjectStrength, string> = {
    strong: "Strong subject",
    weak: "Weak subject",
  };

function formatUnknownValue(
  value: string,
): string {
  return value
    .split("_")
    .filter(Boolean)
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}

export function getStudyTimeLabel(
  value: string,
): string {
  return (
    STUDY_TIME_LABELS[
      value as PreferredStudyTime
    ] ?? formatUnknownValue(value)
  );
}

export function getLearningMethodLabel(
  value: string,
): string {
  return (
    LEARNING_METHOD_LABELS[
      value as LearningMethod
    ] ?? formatUnknownValue(value)
  );
}

export function getStudyChallengeLabel(
  value: string,
): string {
  return (
    STUDY_CHALLENGE_LABELS[
      value as StudyChallenge
    ] ?? formatUnknownValue(value)
  );
}

export function getSubjectStrengthLabel(
  value: string,
): string {
  return (
    SUBJECT_STRENGTH_LABELS[
      value as SubjectStrength
    ] ?? formatUnknownValue(value)
  );
}

export function getWeekdayLabel(
  dayOfWeek: number,
): string {
  return (
    WEEKDAYS.find(
      (weekday) =>
        weekday.value === dayOfWeek,
    )?.label ?? `Day ${dayOfWeek}`
  );
}

export function formatDuration(
  minutes: number | null,
): string {
  if (minutes === null) {
    return "Not provided";
  }

  if (minutes < 60) {
    return `${minutes} ${
      minutes === 1 ? "minute" : "minutes"
    }`;
  }

  const hours = Math.floor(
    minutes / 60,
  );

  const remainingMinutes =
    minutes % 60;

  const hourText = `${hours} ${
    hours === 1 ? "hour" : "hours"
  }`;

  if (remainingMinutes === 0) {
    return hourText;
  }

  return `${hourText} and ${remainingMinutes} ${
    remainingMinutes === 1
      ? "minute"
      : "minutes"
  }`;
}

export function formatClockTime(
  value: string,
): string {
  const normalizedValue =
    value.slice(0, 5);

  const [hourValue, minuteValue] =
    normalizedValue.split(":");

  const hour = Number.parseInt(
    hourValue,
    10,
  );

  const minute = Number.parseInt(
    minuteValue,
    10,
  );

  if (
    !Number.isInteger(hour) ||
    !Number.isInteger(minute) ||
    hour < 0 ||
    hour > 23 ||
    minute < 0 ||
    minute > 59
  ) {
    return value;
  }

  const period =
    hour >= 12 ? "PM" : "AM";

  const displayedHour =
    hour % 12 || 12;

  return `${displayedHour}:${minuteValue} ${period}`;
}