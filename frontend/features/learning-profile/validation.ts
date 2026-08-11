// File: /frontend/features/learning-profile/validation.ts
// Purpose: Validates and normalizes all student-profile and
// learning-profile values before database mutations.

import {
  LEARNING_METHODS,
  LEARNING_OUTPUT_TYPES,
  PREFERRED_STUDY_TIMES,
  STUDY_CHALLENGES,
  SUBJECT_STRENGTHS,
  type LearningMethod,
  type LearningOutputType,
  type PreferredStudyTime,
  type StudyChallenge,
  type SubjectStrength,
} from "./constants";
import type {
  LearningOutputConfidenceInput,
  LearningSubjectInput,
  StudentProfileInput,
  StudyAvailabilityInput,
  StudyChallengesInput,
  StudyPreferencesInput,
} from "./types";

export interface ValidationFieldErrors {
  [fieldName: string]: string;
}

export class LearningProfileValidationError
  extends Error {
  readonly fieldErrors:
    ValidationFieldErrors;

  constructor(
    message: string,
    fieldErrors: ValidationFieldErrors,
  ) {
    super(message);

    this.name =
      "LearningProfileValidationError";

    this.fieldErrors = fieldErrors;
  }
}

function normalizeText(
  value: string,
): string {
  return value.trim().replace(/\s+/g, " ");
}

function isIntegerInRange(
  value: number,
  minimum: number,
  maximum: number,
): boolean {
  return (
    Number.isInteger(value) &&
    value >= minimum &&
    value <= maximum
  );
}

function isValidTimezone(
  value: string,
): boolean {
  try {
    new Intl.DateTimeFormat(
      "en-US",
      {
        timeZone: value,
      },
    ).format();

    return true;
  } catch {
    return false;
  }
}

function normalizeChoiceArray<
  T extends string,
>(
  values: readonly T[],
  allowedValues: readonly T[],
  fieldName: string,
  emptyMessage: string,
): T[] {
  const uniqueValues = Array.from(
    new Set(values),
  );

  const invalidValue =
    uniqueValues.some(
      (value) =>
        !allowedValues.includes(value),
    );

  if (invalidValue) {
    throw new LearningProfileValidationError(
      "Some submitted values are invalid.",
      {
        [fieldName]:
          "One or more selected options are invalid.",
      },
    );
  }

  if (uniqueValues.length === 0) {
    throw new LearningProfileValidationError(
      "Required learning-profile information is missing.",
      {
        [fieldName]: emptyMessage,
      },
    );
  }

  return uniqueValues;
}

export function validateStudentProfileInput(
  input: StudentProfileInput,
): StudentProfileInput {
  const fullName =
    normalizeText(input.fullName);

  const schoolName =
    normalizeText(input.schoolName);

  const programName =
    normalizeText(input.programName);

  const yearLevel =
    normalizeText(input.yearLevel);

  const timezone =
    input.timezone.trim();

  const errors: ValidationFieldErrors =
    {};

  if (fullName.length < 2) {
    errors.fullName =
      "Enter your complete name.";
  } else if (fullName.length > 120) {
    errors.fullName =
      "Your name cannot exceed 120 characters.";
  }

  if (!schoolName) {
    errors.schoolName =
      "Enter your school or institution.";
  } else if (schoolName.length > 160) {
    errors.schoolName =
      "The school name cannot exceed 160 characters.";
  }

  if (!programName) {
    errors.programName =
      "Enter your program, course, or academic track.";
  } else if (programName.length > 160) {
    errors.programName =
      "The program name cannot exceed 160 characters.";
  }

  if (!yearLevel) {
    errors.yearLevel =
      "Enter your current year level.";
  } else if (yearLevel.length > 50) {
    errors.yearLevel =
      "The year level cannot exceed 50 characters.";
  }

  if (!timezone) {
    errors.timezone =
      "Select your timezone.";
  } else if (
    timezone.length > 100 ||
    !isValidTimezone(timezone)
  ) {
    errors.timezone =
      "Select a valid timezone.";
  }

  if (Object.keys(errors).length > 0) {
    throw new LearningProfileValidationError(
      "Review the student-profile information.",
      errors,
    );
  }

  return {
    fullName,
    schoolName,
    programName,
    yearLevel,
    timezone,
  };
}

export function validateStudyPreferencesInput(
  input: StudyPreferencesInput,
): StudyPreferencesInput {
  const errors: ValidationFieldErrors =
    {};

  if (
    !isIntegerInRange(
      input.preferredStudyDurationMinutes,
      10,
      240,
    )
  ) {
    errors.preferredStudyDurationMinutes =
      "Choose a study duration from 10 to 240 minutes.";
  }

  let preferredStudyTimes:
    PreferredStudyTime[] = [];

  let preferredLearningMethods:
    LearningMethod[] = [];

  try {
    preferredStudyTimes =
      normalizeChoiceArray(
        input.preferredStudyTimes,
        PREFERRED_STUDY_TIMES,
        "preferredStudyTimes",
        "Select at least one preferred study time.",
      );
  } catch (error) {
    if (
      error instanceof
      LearningProfileValidationError
    ) {
      Object.assign(
        errors,
        error.fieldErrors,
      );
    } else {
      throw error;
    }
  }

  try {
    preferredLearningMethods =
      normalizeChoiceArray(
        input.preferredLearningMethods,
        LEARNING_METHODS,
        "preferredLearningMethods",
        "Select at least one preferred learning method.",
      );
  } catch (error) {
    if (
      error instanceof
      LearningProfileValidationError
    ) {
      Object.assign(
        errors,
        error.fieldErrors,
      );
    } else {
      throw error;
    }
  }

  if (Object.keys(errors).length > 0) {
    throw new LearningProfileValidationError(
      "Review your study preferences.",
      errors,
    );
  }

  return {
    preferredStudyDurationMinutes:
      input.preferredStudyDurationMinutes,
    preferredStudyTimes,
    preferredLearningMethods,
  };
}

export function validateStudyChallengesInput(
  input: StudyChallengesInput,
): StudyChallengesInput {
  const errors: ValidationFieldErrors =
    {};

  if (
    !isIntegerInRange(
      input.estimatedTaskCompletionMinutes,
      5,
      480,
    )
  ) {
    errors.estimatedTaskCompletionMinutes =
      "Choose an estimated duration from 5 to 480 minutes.";
  }

  let commonStudyChallenges:
    StudyChallenge[] = [];

  try {
    commonStudyChallenges =
      normalizeChoiceArray(
        input.commonStudyChallenges,
        STUDY_CHALLENGES,
        "commonStudyChallenges",
        "Select at least one common study challenge.",
      );
  } catch (error) {
    if (
      error instanceof
      LearningProfileValidationError
    ) {
      Object.assign(
        errors,
        error.fieldErrors,
      );
    } else {
      throw error;
    }
  }

  if (Object.keys(errors).length > 0) {
    throw new LearningProfileValidationError(
      "Review your study challenges.",
      errors,
    );
  }

  return {
    commonStudyChallenges,
    estimatedTaskCompletionMinutes:
      input.estimatedTaskCompletionMinutes,
  };
}

export function validateLearningSubjects(
  subjects: readonly LearningSubjectInput[],
): LearningSubjectInput[] {
  const errors: ValidationFieldErrors =
    {};

  if (subjects.length < 2) {
    errors.subjects =
      "Add at least one strong subject and one weak subject.";
  } else if (subjects.length > 30) {
    errors.subjects =
      "A maximum of 30 subjects is allowed.";
  }

  const normalizedSubjects =
    subjects.map(
      (subject, index) => {
        const subjectName =
          normalizeText(
            subject.subjectName,
          );

        const subjectStrength =
          subject.subjectStrength;

        if (!subjectName) {
          errors[`subjects.${index}.name`] =
            "Enter the subject name.";
        } else if (
          subjectName.length > 100
        ) {
          errors[`subjects.${index}.name`] =
            "The subject name cannot exceed 100 characters.";
        }

        if (
          !SUBJECT_STRENGTHS.includes(
            subjectStrength,
          )
        ) {
          errors[
            `subjects.${index}.strength`
          ] =
            "Select strong or weak.";
        }

        return {
          subjectName,
          subjectStrength:
            subjectStrength as SubjectStrength,
        };
      },
    );

  const normalizedNames =
    new Set<string>();

  normalizedSubjects.forEach(
    (subject, index) => {
      const duplicateKey =
        subject.subjectName.toLocaleLowerCase(
          "en-US",
        );

      if (
        subject.subjectName &&
        normalizedNames.has(
          duplicateKey,
        )
      ) {
        errors[`subjects.${index}.name`] =
          "Each subject may only be added once.";
      }

      normalizedNames.add(
        duplicateKey,
      );
    },
  );

  const hasStrongSubject =
    normalizedSubjects.some(
      (subject) =>
        subject.subjectStrength ===
        "strong",
    );

  const hasWeakSubject =
    normalizedSubjects.some(
      (subject) =>
        subject.subjectStrength ===
        "weak",
    );

  if (!hasStrongSubject) {
    errors.strongSubjects =
      "Add at least one strong subject.";
  }

  if (!hasWeakSubject) {
    errors.weakSubjects =
      "Add at least one weak subject.";
  }

  if (Object.keys(errors).length > 0) {
    throw new LearningProfileValidationError(
      "Review your subject information.",
      errors,
    );
  }

  return normalizedSubjects;
}

export function validateLearningOutputConfidences(
  confidences:
    readonly LearningOutputConfidenceInput[],
): LearningOutputConfidenceInput[] {
  const errors: ValidationFieldErrors =
    {};

  if (
    confidences.length !==
    LEARNING_OUTPUT_TYPES.length
  ) {
    errors.outputConfidences =
      "Rate your confidence for all seven output types.";
  }

  const seenOutputTypes =
    new Set<LearningOutputType>();

  const normalizedConfidences =
    confidences.map(
      (confidence, index) => {
        const outputType =
          confidence.outputType;

        const confidenceLevel =
          confidence.confidenceLevel;

        if (
          !LEARNING_OUTPUT_TYPES.includes(
            outputType,
          )
        ) {
          errors[
            `outputConfidences.${index}.outputType`
          ] =
            "Select a valid output type.";
        } else if (
          seenOutputTypes.has(
            outputType,
          )
        ) {
          errors[
            `outputConfidences.${index}.outputType`
          ] =
            "Each output type may only appear once.";
        } else {
          seenOutputTypes.add(
            outputType,
          );
        }

        if (
          !isIntegerInRange(
            confidenceLevel,
            1,
            5,
          )
        ) {
          errors[
            `outputConfidences.${index}.confidence`
          ] =
            "Select a confidence level from 1 to 5.";
        }

        return {
          outputType:
            outputType as LearningOutputType,
          confidenceLevel,
        };
      },
    );

  const hasEveryOutputType =
    LEARNING_OUTPUT_TYPES.every(
      (outputType) =>
        seenOutputTypes.has(
          outputType,
        ),
    );

  if (!hasEveryOutputType) {
    errors.outputConfidences =
      "Rate your confidence for all seven output types.";
  }

  if (Object.keys(errors).length > 0) {
    throw new LearningProfileValidationError(
      "Review your academic-output confidence ratings.",
      errors,
    );
  }

  return normalizedConfidences;
}

const TIME_PATTERN =
  /^(?:[01]\d|2[0-3]):[0-5]\d$/;

function timeToMinutes(
  value: string,
): number {
  const [hours, minutes] =
    value.split(":").map(Number);

  return hours * 60 + minutes;
}

export function validateStudyAvailability(
  slots: readonly StudyAvailabilityInput[],
): StudyAvailabilityInput[] {
  const errors: ValidationFieldErrors =
    {};

  if (slots.length === 0) {
    errors.availability =
      "Add at least one available study period.";
  } else if (slots.length > 30) {
    errors.availability =
      "A maximum of 30 study periods is allowed.";
  }

  const normalizedSlots =
    slots.map((slot, index) => {
      const startTime =
        slot.startTime.trim();

      const endTime =
        slot.endTime.trim();

      if (
        !isIntegerInRange(
          slot.dayOfWeek,
          1,
          7,
        )
      ) {
        errors[
          `availability.${index}.day`
        ] =
          "Select a valid weekday.";
      }

      if (!TIME_PATTERN.test(startTime)) {
        errors[
          `availability.${index}.startTime`
        ] =
          "Enter a valid start time.";
      }

      if (!TIME_PATTERN.test(endTime)) {
        errors[
          `availability.${index}.endTime`
        ] =
          "Enter a valid end time.";
      }

      if (
        TIME_PATTERN.test(startTime) &&
        TIME_PATTERN.test(endTime) &&
        timeToMinutes(startTime) >=
          timeToMinutes(endTime)
      ) {
        errors[
          `availability.${index}.endTime`
        ] =
          "The end time must be later than the start time.";
      }

      return {
        dayOfWeek: slot.dayOfWeek,
        startTime,
        endTime,
      };
    });

  for (
    let firstIndex = 0;
    firstIndex < normalizedSlots.length;
    firstIndex += 1
  ) {
    const firstSlot =
      normalizedSlots[firstIndex];

    if (
      !TIME_PATTERN.test(
        firstSlot.startTime,
      ) ||
      !TIME_PATTERN.test(
        firstSlot.endTime,
      )
    ) {
      continue;
    }

    for (
      let secondIndex =
        firstIndex + 1;
      secondIndex <
      normalizedSlots.length;
      secondIndex += 1
    ) {
      const secondSlot =
        normalizedSlots[secondIndex];

      if (
        firstSlot.dayOfWeek !==
        secondSlot.dayOfWeek
      ) {
        continue;
      }

      if (
        !TIME_PATTERN.test(
          secondSlot.startTime,
        ) ||
        !TIME_PATTERN.test(
          secondSlot.endTime,
        )
      ) {
        continue;
      }

      const periodsOverlap =
        timeToMinutes(
          firstSlot.startTime,
        ) <
          timeToMinutes(
            secondSlot.endTime,
          ) &&
        timeToMinutes(
          secondSlot.startTime,
        ) <
          timeToMinutes(
            firstSlot.endTime,
          );

      if (periodsOverlap) {
        errors[
          `availability.${secondIndex}.startTime`
        ] =
          "Study periods on the same day cannot overlap.";
      }
    }
  }

  if (Object.keys(errors).length > 0) {
    throw new LearningProfileValidationError(
      "Review your available study schedule.",
      errors,
    );
  }

  return normalizedSlots;
}