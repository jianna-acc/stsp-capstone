// File: /frontend/features/subjects/actions.ts
// Purpose: Implements authenticated create, update, and
// safe-delete subject mutations using Supabase and Server Actions.

"use server";

import { revalidatePath } from "next/cache";

import { createClient } from "@/lib/supabase/server";

import type {
  SubjectDeleteResult,
  SubjectMutationResult,
} from "./types";
import {
  isValidSubjectId,
  validateSubjectInput,
} from "./validation";

const SUBJECT_SELECT =
  "id, name, color, created_at, updated_at";

function isDuplicateError(
  error: { code?: string } | null,
): boolean {
  return error?.code === "23505";
}

export async function createSubjectAction(
  payload: unknown,
): Promise<SubjectMutationResult> {
  const validation =
    validateSubjectInput(payload);

  if (!validation.success) {
    return {
      success: false,
      message:
        "Check the subject information and try again.",
      fieldErrors: validation.errors,
    };
  }

  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return {
      success: false,
      message:
        "Your session has expired. Sign in again.",
    };
  }

  const { data, error } = await supabase
    .from("subjects")
    .insert({
      user_id: user.id,
      name: validation.data.name,
      color: validation.data.color,
    })
    .select(SUBJECT_SELECT)
    .single();

  if (error) {
    if (isDuplicateError(error)) {
      return {
        success: false,
        message:
          "You already have a subject with this name.",
        fieldErrors: {
          name:
            "Use a different subject name.",
        },
      };
    }

    return {
      success: false,
      message:
        "The subject could not be created. Try again.",
    };
  }

  revalidatePath("/subjects");

  return {
    success: true,
    message: "Subject created successfully.",
    subject: data,
  };
}

export async function updateSubjectAction(
  subjectId: unknown,
  payload: unknown,
): Promise<SubjectMutationResult> {
  if (!isValidSubjectId(subjectId)) {
    return {
      success: false,
      message:
        "The selected subject is not valid.",
    };
  }

  const validation =
    validateSubjectInput(payload);

  if (!validation.success) {
    return {
      success: false,
      message:
        "Check the subject information and try again.",
      fieldErrors: validation.errors,
    };
  }

  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return {
      success: false,
      message:
        "Your session has expired. Sign in again.",
    };
  }

  const { data, error } = await supabase
    .from("subjects")
    .update({
      name: validation.data.name,
      color: validation.data.color,
    })
    .eq("id", subjectId)
    .eq("user_id", user.id)
    .select(SUBJECT_SELECT)
    .maybeSingle();

  if (error) {
    if (isDuplicateError(error)) {
      return {
        success: false,
        message:
          "You already have a subject with this name.",
        fieldErrors: {
          name:
            "Use a different subject name.",
        },
      };
    }

    return {
      success: false,
      message:
        "The subject could not be updated. Try again.",
    };
  }

  if (!data) {
    return {
      success: false,
      message:
        "The subject was not found or you cannot edit it.",
    };
  }

  revalidatePath("/subjects");

  return {
    success: true,
    message: "Subject updated successfully.",
    subject: data,
  };
}

export async function deleteSubjectAction(
  subjectId: unknown,
): Promise<SubjectDeleteResult> {
  if (!isValidSubjectId(subjectId)) {
    return {
      success: false,
      message:
        "The selected subject is not valid.",
    };
  }

  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return {
      success: false,
      message:
        "Your session has expired. Sign in again.",
    };
  }

  const {
    count: fileCount,
    error: fileCountError,
  } = await supabase
    .from("study_files")
    .select("id", {
      count: "exact",
      head: true,
    })
    .eq("subject_id", subjectId)
    .eq("user_id", user.id);

  if (fileCountError) {
    return {
      success: false,
      message:
        "The subject could not be checked. Try again.",
    };
  }

  if ((fileCount ?? 0) > 0) {
    return {
      success: false,
      message:
        "This subject still contains uploaded files. Remove the files before deleting the subject.",
    };
  }

  const { data, error } = await supabase
    .from("subjects")
    .delete()
    .eq("id", subjectId)
    .eq("user_id", user.id)
    .select("id")
    .maybeSingle();

  if (error) {
    return {
      success: false,
      message:
        "The subject could not be deleted. Try again.",
    };
  }

  if (!data) {
    return {
      success: false,
      message:
        "The subject was not found or you cannot delete it.",
    };
  }

  revalidatePath("/subjects");

  return {
    success: true,
    message: "Subject deleted successfully.",
    deletedId: subjectId,
  };
}