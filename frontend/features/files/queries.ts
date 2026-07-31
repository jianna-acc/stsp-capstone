// File: /frontend/features/files/queries.ts
// Purpose: Loads authenticated student-owned file records for
// the protected file-management page.

import "server-only";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/types/database";

import type {
  StudyFileSummary,
} from "./types";

type StudyFileRow =
  Database["public"]["Tables"]["study_files"]["Row"];

function toStudyFileSummary(
  row: StudyFileRow,
): StudyFileSummary {
  return {
    id: row.id,
    subject_id: row.subject_id,
    topic: row.topic,
    original_filename:
      row.original_filename,
    storage_path: row.storage_path,
    mime_type: row.mime_type,
    size_bytes: row.size_bytes,
    processing_status:
      row.processing_status,
    failure_message:
      row.failure_message,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

export async function getStudyFiles(): Promise<
  StudyFileSummary[]
> {
  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    redirect("/login");
  }

  /*
   * Selecting the complete row preserves the generated
   * database type. The result is then converted into the
   * smaller serializable StudyFileSummary shape.
   */
  const { data, error } = await supabase
    .from("study_files")
    .select("*")
    .eq("user_id", user.id)
    .order("created_at", {
      ascending: false,
    });

  if (error) {
    console.error(
      "Study-file query failed:",
      error.code,
    );

    throw new Error(
      "The uploaded files could not be loaded.",
    );
  }

  return (data ?? []).map(
    toStudyFileSummary,
  );
}