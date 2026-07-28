// File: /frontend/features/learning-profile/actions/save-subjects.ts
// Purpose: Reads, validates, and saves strong and weak subjects
// with confidence values before continuing to availability.

"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type {
  SubjectStrength,
} from "../constants";
import { LearningProfileDataError } from "../server/errors";
import { replaceLearningSubjects } from "../server/mutations";
import { LearningProfileValidationError } from "../validation";
import type {
  SubjectConfidenceFormValue,
  SubjectsActionState,
  SubjectsFormValues,
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

function isObject(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function normalizeParsedSubject(
  value: unknown,
): SubjectConfidenceFormValue {
  if (!isObject(value)) {
    return {
      subjectName: "",
      subjectStrength: "",
      confidenceLevel: "",
    };
  }

  return {
    subjectName:
      typeof value.subjectName === "string"
        ? value.subjectName.trim()
        : "",

    subjectStrength:
      typeof value.subjectStrength === "string"
        ? value.subjectStrength.trim()
        : "",

    confidenceLevel:
      typeof value.confidenceLevel === "string"
        ? value.confidenceLevel.trim()
        : "",
  };
}

function readSubjectsValues(
  formData: FormData,
): SubjectsFormValues {
  const serializedSubjects =
    getTextValue(formData, "subjectsJson");

  if (!serializedSubjects) {
    return {
      subjects: [],
    };
  }

  try {
    const parsedValue: unknown =
      JSON.parse(serializedSubjects);

    if (!Array.isArray(parsedValue)) {
      return {
        subjects: [],
      };
    }

    return {
      subjects:
        parsedValue.map(
          normalizeParsedSubject,
        ),
    };
  } catch {
    return {
      subjects: [],
    };
  }
}

export async function saveSubjectsAction(
  previousState: SubjectsActionState,
  formData: FormData,
): Promise<SubjectsActionState> {
  void previousState;

  const values =
    readSubjectsValues(formData);

  try {
    await replaceLearningSubjects(
      values.subjects.map(
        (subject) => ({
          subjectName:
            subject.subjectName,

          subjectStrength:
            subject.subjectStrength as SubjectStrength,

          confidenceLevel:
            Number.parseInt(
              subject.confidenceLevel,
              10,
            ),
        }),
      ),
    );
  } catch (error) {
    if (
      error instanceof
      LearningProfileValidationError
    ) {
      return {
        status: "error",
        message: error.message,
        fieldErrors: {
          ...error.fieldErrors,
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
          "Your subject information could not be saved. Check your connection and try again.",
        fieldErrors: {},
        values,
      };
    }

    throw error;
  }

  revalidatePath("/onboarding");
  revalidatePath("/onboarding/subjects");
  revalidatePath("/onboarding/availability");
  revalidatePath("/dashboard");

  redirect("/onboarding/availability");
}