// File: /frontend/features/learning-profile/actions/save-availability.ts
// Purpose: Reads, validates, and saves recurring weekly study
// availability before continuing to the onboarding review step.

"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { LearningProfileDataError } from "../server/errors";
import { replaceStudyAvailability } from "../server/mutations";
import { LearningProfileValidationError } from "../validation";
import type {
  AvailabilityActionState,
  AvailabilityFormValues,
  AvailabilitySlotFormValue,
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

function normalizeParsedSlot(
  value: unknown,
): AvailabilitySlotFormValue {
  if (!isObject(value)) {
    return {
      dayOfWeek: "",
      startTime: "",
      endTime: "",
    };
  }

  return {
    dayOfWeek:
      typeof value.dayOfWeek === "string"
        ? value.dayOfWeek.trim()
        : "",

    startTime:
      typeof value.startTime === "string"
        ? value.startTime.trim()
        : "",

    endTime:
      typeof value.endTime === "string"
        ? value.endTime.trim()
        : "",
  };
}

function readAvailabilityValues(
  formData: FormData,
): AvailabilityFormValues {
  const serializedSlots =
    getTextValue(formData, "availabilityJson");

  if (!serializedSlots) {
    return {
      slots: [],
    };
  }

  try {
    const parsedValue: unknown =
      JSON.parse(serializedSlots);

    if (!Array.isArray(parsedValue)) {
      return {
        slots: [],
      };
    }

    return {
      slots: parsedValue.map(
        normalizeParsedSlot,
      ),
    };
  } catch {
    return {
      slots: [],
    };
  }
}

export async function saveAvailabilityAction(
  previousState: AvailabilityActionState,
  formData: FormData,
): Promise<AvailabilityActionState> {
  void previousState;

  const values =
    readAvailabilityValues(formData);

  try {
    await replaceStudyAvailability(
      values.slots.map((slot) => ({
        dayOfWeek: Number.parseInt(
          slot.dayOfWeek,
          10,
        ),
        startTime: slot.startTime,
        endTime: slot.endTime,
      })),
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
          "Your available study schedule could not be saved. Check your connection and try again.",
        fieldErrors: {},
        values,
      };
    }

    throw error;
  }

  revalidatePath("/onboarding");
  revalidatePath("/onboarding/availability");
  revalidatePath("/onboarding/review");
  revalidatePath("/dashboard");

  redirect("/onboarding/review");
}