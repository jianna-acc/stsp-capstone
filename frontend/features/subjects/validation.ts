// File: /frontend/features/subjects/validation.ts
// Purpose: Validates and normalizes untrusted subject data
// before it reaches Supabase.

import { SUBJECT_COLORS } from "./constants";
import type {
  SubjectFieldErrors,
  SubjectInput,
} from "./types";

type ValidationResult =
  | {
      success: true;
      data: SubjectInput;
    }
  | {
      success: false;
      errors: SubjectFieldErrors;
    };

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

export function normalizeSubjectName(
  value: string,
): string {
  return value.trim().replace(/\s+/g, " ");
}

export function validateSubjectInput(
  input: unknown,
): ValidationResult {
  if (!isRecord(input)) {
    return {
      success: false,
      errors: {
        name: "Enter a subject name.",
        color: "Select a subject color.",
      },
    };
  }

  const rawName =
    typeof input.name === "string"
      ? input.name
      : "";

  const rawColor =
    typeof input.color === "string"
      ? input.color
      : "";

  const name = normalizeSubjectName(rawName);
  const color = rawColor.trim().toLowerCase();

  const errors: SubjectFieldErrors = {};

  if (!name) {
    errors.name = "Enter a subject name.";
  } else if (name.length > 80) {
    errors.name =
      "The subject name must be 80 characters or fewer.";
  }

  if (
    !SUBJECT_COLORS.includes(
      color as (typeof SUBJECT_COLORS)[number],
    )
  ) {
    errors.color =
      "Select one of the available subject colors.";
  }

  if (Object.keys(errors).length > 0) {
    return {
      success: false,
      errors,
    };
  }

  return {
    success: true,
    data: {
      name,
      color,
    },
  };
}

export function isValidSubjectId(
  value: unknown,
): value is string {
  return (
    typeof value === "string" &&
    UUID_PATTERN.test(value)
  );
}