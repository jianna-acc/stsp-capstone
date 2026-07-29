// File: /frontend/features/learning-profile/actions/save-study-challenges.ts
// Purpose: Reads, validates, and saves Step 3 study-challenge
// answers before continuing to subjects and confidence.

"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  STUDY_CHALLENGES,
  type StudyChallenge,
} from "../constants";
import { LearningProfileDataError } from "../server/errors";
import { saveStudyChallenges } from "../server/mutations";
import { LearningProfileValidationError } from "../validation";
import type {
  StudyChallengesActionState,
  StudyChallengesFormValues,
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

function getAllowedValues<T extends string>(
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

function readStudyChallengesValues(
  formData: FormData,
): StudyChallengesFormValues {
  return {
    commonStudyChallenges:
      getAllowedValues<StudyChallenge>(
        formData,
        "commonStudyChallenges",
        STUDY_CHALLENGES,
      ),

    estimatedTaskCompletionMinutes:
      getTextValue(
        formData,
        "estimatedTaskCompletionMinutes",
      ),
  };
}

export async function saveStudyChallengesAction(
  previousState: StudyChallengesActionState,
  formData: FormData,
): Promise<StudyChallengesActionState> {
  void previousState;

  const values =
    readStudyChallengesValues(formData);

  const estimatedTaskCompletionMinutes =
    Number.parseInt(
      values.estimatedTaskCompletionMinutes,
      10,
    );

  try {
    await saveStudyChallenges({
      commonStudyChallenges:
        values.commonStudyChallenges,
      estimatedTaskCompletionMinutes,
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
          commonStudyChallenges:
            error.fieldErrors
              .commonStudyChallenges,

          estimatedTaskCompletionMinutes:
            error.fieldErrors
              .estimatedTaskCompletionMinutes,
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
          "Your study challenges could not be saved. Check your connection and try again.",
        fieldErrors: {},
        values,
      };
    }

    throw error;
  }

  revalidatePath("/onboarding");
  revalidatePath(
    "/onboarding/study-challenges",
  );
  revalidatePath("/onboarding/subjects");
  revalidatePath("/dashboard");

  redirect("/onboarding/subjects");
}