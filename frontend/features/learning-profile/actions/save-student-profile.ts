// File: /frontend/features/learning-profile/actions/save-student-profile.ts
// Purpose: Reads the Step 1 onboarding form, validates and saves
// the authenticated student's profile, then continues to Step 2.

"use server";

import {
  revalidatePath,
} from "next/cache";
import {
  redirect,
} from "next/navigation";

import {
  LearningProfileDataError,
} from "../server/errors";
import {
  saveStudentProfile,
} from "../server/mutations";
import {
  LearningProfileValidationError,
} from "../validation";
import type {
  StudentProfileActionState,
  StudentProfileFormValues,
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

function readStudentProfileValues(
  formData: FormData,
): StudentProfileFormValues {
  return {
    fullName: getTextValue(
      formData,
      "fullName",
    ),
    schoolName: getTextValue(
      formData,
      "schoolName",
    ),
    programName: getTextValue(
      formData,
      "programName",
    ),
    yearLevel: getTextValue(
      formData,
      "yearLevel",
    ),
    timezone: getTextValue(
      formData,
      "timezone",
    ),
  };
}

export async function saveStudentProfileAction(
  previousState: StudentProfileActionState,
  formData: FormData,
): Promise<StudentProfileActionState> {
  void previousState;

  const values =
    readStudentProfileValues(formData);

  try {
    await saveStudentProfile(values);
  } catch (error) {
    if (
      error instanceof
      LearningProfileValidationError
    ) {
      return {
        status: "error",
        message: error.message,
        fieldErrors: {
          fullName:
            error.fieldErrors.fullName,
          schoolName:
            error.fieldErrors.schoolName,
          programName:
            error.fieldErrors.programName,
          yearLevel:
            error.fieldErrors.yearLevel,
          timezone:
            error.fieldErrors.timezone,
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
          "Your student profile could not be saved. Check your connection and try again.",
        fieldErrors: {},
        values,
      };
    }

    throw error;
  }

  revalidatePath("/onboarding");
  revalidatePath("/onboarding/profile");
  revalidatePath("/dashboard");

  redirect(
    "/onboarding/study-preferences",
  );
}