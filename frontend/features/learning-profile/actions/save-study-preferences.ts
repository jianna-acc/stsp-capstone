// File: /frontend/features/learning-profile/actions/save-study-preferences.ts
// Purpose: Reads, validates, and saves Step 2 study-preference
// answers before continuing to the study-challenges step.

"use server";

import {
  revalidatePath,
} from "next/cache";
import {
  redirect,
} from "next/navigation";

import {
  LEARNING_METHODS,
  PREFERRED_STUDY_TIMES,
  type LearningMethod,
  type PreferredStudyTime,
} from "../constants";
import {
  LearningProfileDataError,
} from "../server/errors";
import {
  saveStudyPreferences,
} from "../server/mutations";
import {
  LearningProfileValidationError,
} from "../validation";
import type {
  StudyPreferencesActionState,
  StudyPreferencesFormValues,
} from "./types";

function getTextValue(
  formData: FormData,
  fieldName: string,
): string {
  const value = formData.get(fieldName);

  return typeof value === "string"
    ? value.trim()
    : "";
}

function getAllowedValues<
  T extends string,
>(
  formData: FormData,
  fieldName: string,
  allowedValues: readonly T[],
): T[] {
  const submittedValues = formData
    .getAll(fieldName)
    .filter(
      (value): value is string =>
        typeof value === "string",
    );

  return submittedValues.filter(
    (value): value is T =>
      allowedValues.includes(value as T),
  );
}

function readStudyPreferencesValues(
  formData: FormData,
): StudyPreferencesFormValues {
  return {
    preferredStudyDurationMinutes:
      getTextValue(
        formData,
        "preferredStudyDurationMinutes",
      ),

    preferredStudyTimes:
      getAllowedValues<PreferredStudyTime>(
        formData,
        "preferredStudyTimes",
        PREFERRED_STUDY_TIMES,
      ),

    preferredLearningMethods:
      getAllowedValues<LearningMethod>(
        formData,
        "preferredLearningMethods",
        LEARNING_METHODS,
      ),
  };
}

export async function saveStudyPreferencesAction(
  previousState: StudyPreferencesActionState,
  formData: FormData,
): Promise<StudyPreferencesActionState> {
  void previousState;

  const values =
    readStudyPreferencesValues(formData);

  const preferredStudyDurationMinutes =
    Number.parseInt(
      values.preferredStudyDurationMinutes,
      10,
    );

  try {
    await saveStudyPreferences({
      preferredStudyDurationMinutes,
      preferredStudyTimes:
        values.preferredStudyTimes,
      preferredLearningMethods:
        values.preferredLearningMethods,
    });
  } catch (error) {
    if (
      error instanceof
      LearningProfileValidationError
    ) {
      return {
        status: "error",
        message: error.message,
        fieldErrors: {
          preferredStudyDurationMinutes:
            error.fieldErrors
              .preferredStudyDurationMinutes,

          preferredStudyTimes:
            error.fieldErrors
              .preferredStudyTimes,

          preferredLearningMethods:
            error.fieldErrors
              .preferredLearningMethods,
        },
        values,
      };
    }

    if (
      error instanceof
      LearningProfileDataError
    ) {
      return {
        status: "error",
        message:
          "Your study preferences could not be saved. Check your connection and try again.",
        fieldErrors: {},
        values,
      };
    }

    throw error;
  }

  revalidatePath("/onboarding");
  revalidatePath(
    "/onboarding/study-preferences",
  );
  revalidatePath(
    "/onboarding/study-challenges",
  );
  revalidatePath("/dashboard");

  redirect(
    "/onboarding/study-challenges",
  );
}