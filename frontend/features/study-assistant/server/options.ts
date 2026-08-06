// File: /frontend/features/study-assistant/server/options.ts
// Purpose: Loads the authenticated student's subjects and
// ready study files for optional Study Assistant filtering.

import "server-only";

import { createClient } from "@/lib/supabase/server";
import type {
  StudyAssistantFilterOptions,
} from "@/types/rag";

const FILTER_LOAD_ERROR =
  "Your subject and study-material filters could not be loaded. You can still ask across all available materials.";

function createEmptyOptions(
  loadError: string | null,
): StudyAssistantFilterOptions {
  return {
    subjects: [],
    studyFiles: [],
    loadError,
  };
}

export async function getStudyAssistantFilterOptions(): Promise<StudyAssistantFilterOptions> {
  const supabase = await createClient();

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    return createEmptyOptions(
      FILTER_LOAD_ERROR,
    );
  }

  const [
    subjectsResult,
    studyFilesResult,
  ] = await Promise.all([
    supabase
      .from("subjects")
      .select("id, name")
      .eq("user_id", user.id)
      .order("name", {
        ascending: true,
      }),

    supabase
      .from("study_files")
      .select(
        "id, subject_id, original_filename",
      )
      .eq("user_id", user.id)
      .eq(
        "processing_status",
        "ready",
      )
      .order("created_at", {
        ascending: false,
      }),
  ]);

  if (
    subjectsResult.error ||
    studyFilesResult.error
  ) {
    return createEmptyOptions(
      FILTER_LOAD_ERROR,
    );
  }

  return {
    subjects:
      subjectsResult.data?.map(
        (subject) => ({
          id: subject.id,
          name: subject.name,
        }),
      ) ?? [],

    studyFiles:
      studyFilesResult.data?.map(
        (studyFile) => ({
          id: studyFile.id,
          subjectId:
            studyFile.subject_id,
          originalFilename:
            studyFile.original_filename,
        }),
      ) ?? [],

    loadError: null,
  };
}