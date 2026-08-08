// File: /frontend/features/reviewers/server/options.ts
// Purpose: Loads the authenticated student's subjects and
// ready study files for reviewer generation options.

import "server-only";

import {
  createClient,
} from "@/lib/supabase/server";

import type {
  ReviewerFilterOptions,
} from "../types";

const FILTER_LOAD_ERROR =
  "Your subjects and ready study materials could not be loaded. Reviewer generation is temporarily unavailable.";

function createEmptyOptions(
  loadError: string | null,
): ReviewerFilterOptions {
  return {
    subjects: [],
    studyFiles: [],
    loadError,
  };
}

export async function getReviewerFilterOptions(): Promise<ReviewerFilterOptions> {
  const supabase =
    await createClient();

  const {
    data: {
      user,
    },
    error: userError,
  } = await supabase.auth.getUser();

  if (
    userError ||
    !user
  ) {
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
      .select(
        "id, name",
      )
      .eq(
        "user_id",
        user.id,
      )
      .order(
        "name",
        {
          ascending: true,
        },
      ),

    supabase
      .from("study_files")
      .select(
        "id, subject_id, original_filename",
      )
      .eq(
        "user_id",
        user.id,
      )
      .eq(
        "processing_status",
        "ready",
      )
      .order(
        "created_at",
        {
          ascending: false,
        },
      ),
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
        (
          subject,
        ) => ({
          id:
            subject.id,

          name:
            subject.name,
        }),
      ) ?? [],

    studyFiles:
      studyFilesResult.data?.map(
        (
          studyFile,
        ) => ({
          id:
            studyFile.id,

          subjectId:
            studyFile.subject_id,

          originalFilename:
            studyFile.original_filename,
        }),
      ) ?? [],

    loadError: null,
  };
}