// File: /frontend/features/learning-profile/actions/save-subjects.ts
// Purpose: Reads, validates, and saves strong or weak subjects
// plus academic-output confidence before continuing onboarding.

"use server";

import {
  revalidatePath,
} from "next/cache";
import {
  redirect,
} from "next/navigation";

import {
  type LearningOutputType,
} from "../constants";
import {
  LearningProfileDataError,
} from "../server/errors";
import {
  replaceLearningOutputConfidences,
  replaceLearningSubjects,
} from "../server/mutations";
import {
  LearningProfileValidationError,
} from "../validation";
import type {
  OutputConfidenceFormValue,
  SubjectFormValue,
  SubjectsActionState,
  SubjectsFormValues,
} from "./types";

function getTextValue(
  formData: FormData,
  fieldName: string,
): string {
  const value =
    formData.get(
      fieldName,
    );

  return typeof value === "string"
    ? value.trim()
    : "";
}

function isObject(
  value: unknown,
): value is Record<
  string,
  unknown
> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(
      value,
    )
  );
}

function normalizeParsedSubject(
  value: unknown,
): SubjectFormValue {
  if (!isObject(value)) {
    return {
      subjectName: "",
      subjectStrength: "",
    };
  }

  return {
    subjectName:
      typeof value.subjectName ===
      "string"
        ? value.subjectName.trim()
        : "",

    subjectStrength:
      typeof value.subjectStrength ===
      "string"
        ? value.subjectStrength.trim()
        : "",
  };
}

function normalizeParsedOutputConfidence(
  value: unknown,
): OutputConfidenceFormValue {
  if (!isObject(value)) {
    return {
      outputType: "",
      confidenceLevel: "",
    };
  }

  return {
    outputType:
      typeof value.outputType ===
      "string"
        ? value.outputType.trim()
        : "",

    confidenceLevel:
      typeof value.confidenceLevel ===
      "string"
        ? value.confidenceLevel.trim()
        : "",
  };
}

function parseJsonArray(
  serializedValue: string,
): unknown[] {
  if (!serializedValue) {
    return [];
  }

  try {
    const parsedValue: unknown =
      JSON.parse(
        serializedValue,
      );

    return Array.isArray(
      parsedValue,
    )
      ? parsedValue
      : [];
  } catch {
    return [];
  }
}

function readSubjectsValues(
  formData: FormData,
): SubjectsFormValues {
  const serializedSubjects =
    getTextValue(
      formData,
      "subjectsJson",
    );

  const serializedOutputConfidences =
    getTextValue(
      formData,
      "outputConfidencesJson",
    );

  return {
    subjects:
      parseJsonArray(
        serializedSubjects,
      ).map(
        normalizeParsedSubject,
      ),

    outputConfidences:
      parseJsonArray(
        serializedOutputConfidences,
      ).map(
        normalizeParsedOutputConfidence,
      ),
  };
}

export async function saveSubjectsAction(
  previousState:
    SubjectsActionState,
  formData: FormData,
): Promise<SubjectsActionState> {
  void previousState;

  const values =
    readSubjectsValues(
      formData,
    );

  try {
    await replaceLearningOutputConfidences(
      values.outputConfidences.map(
        (confidence) => ({
          outputType:
            confidence.outputType as
              LearningOutputType,

          confidenceLevel:
            Number.parseInt(
              confidence.confidenceLevel,
              10,
            ),
        }),
      ),
    );

    await replaceLearningSubjects(
      values.subjects.map(
        (subject) => ({
          subjectName:
            subject.subjectName,

          subjectStrength:
            subject.subjectStrength as
              "strong" | "weak",
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
        message:
          error.message,
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
          "Your subject and output-confidence information could not be saved. Check your connection and try again.",
        fieldErrors: {},
        values,
      };
    }

    throw error;
  }

  revalidatePath(
    "/onboarding",
  );
  revalidatePath(
    "/onboarding/subjects",
  );
  revalidatePath(
    "/onboarding/availability",
  );
  revalidatePath(
    "/dashboard",
  );
  revalidatePath(
    "/profile",
  );

  redirect(
    "/onboarding/availability",
  );
}