// File: /frontend/features/flashcards/server/options.ts
// Purpose: Loads authenticated subjects and ready study-material
// options for Flashcard generation.

import "server-only";

import {
  redirect,
} from "next/navigation";

import {
  createClient,
} from "@/lib/supabase/server";

import type {
  FlashcardFileOption,
  FlashcardFilterOptions,
  FlashcardSubjectOption,
} from "../types";

const FILTER_LOAD_ERROR_MESSAGE =
  "Your subjects and ready study materials could not be loaded. Flashcard generation is temporarily unavailable.";

interface SubjectRow {
  id: string;
  name: string;
}

interface StudyFileRow {
  id: string;
  subject_id: string;
  original_filename: string;
}

function buildLoadError():
  FlashcardFilterOptions {
  return {
    subjects: [],
    studyFiles: [],
    loadError:
      FILTER_LOAD_ERROR_MESSAGE,
  };
}

function mapSubjects(
  rows: SubjectRow[],
): FlashcardSubjectOption[] {
  return rows.map(
    (
      row,
    ) => ({
      id: row.id,
      name: row.name,
    }),
  );
}

function mapStudyFiles(
  rows: StudyFileRow[],
): FlashcardFileOption[] {
  return rows.map(
    (
      row,
    ) => ({
      id: row.id,

      subjectId:
        row.subject_id,

      originalFilename:
        row.original_filename,
    }),
  );
}

export async function getFlashcardFilterOptions():
  Promise<FlashcardFilterOptions> {
  const supabase =
    await createClient();

  const {
    data: {
      user,
    },
    error: authError,
  } = await supabase.auth.getUser();

  if (
    authError ||
    !user
  ) {
    redirect(
      "/login",
    );
  }

  const {
    data: subjectRows,
    error: subjectError,
  } = await supabase
    .from(
      "subjects",
    )
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
    );

  if (
    subjectError ||
    !subjectRows
  ) {
    return buildLoadError();
  }

  const {
    data: studyFileRows,
    error: studyFileError,
  } = await supabase
    .from(
      "study_files",
    )
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
      "original_filename",
      {
        ascending: true,
      },
    );

  if (
    studyFileError ||
    !studyFileRows
  ) {
    return buildLoadError();
  }

  return {
    subjects:
      mapSubjects(
        subjectRows,
      ),

    studyFiles:
      mapStudyFiles(
        studyFileRows,
      ),

    loadError: null,
  };
}