// File: /frontend/features/files/actions.ts
// Purpose: Handles study-file upload reservations, upload status
// updates, secure preview/download URLs, and file deletion.

"use server";

import { randomUUID } from "node:crypto";

import { revalidatePath } from "next/cache";

import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/types/database";

import { STUDY_MATERIALS_BUCKET } from "./constants";
import type {
  DeleteStudyFileResult,
  ReserveStudyFileResult,
  StudyFileAccessMode,
  StudyFileAccessResult,
  StudyFileMutationResult,
  StudyFileSummary,
} from "./types";
import {
  isValidStudyFileId,
  sanitizeStorageFilename,
  validateReserveStudyFileInput,
} from "./validation";

type StudyFileRow =
  Database["public"]["Tables"]["study_files"]["Row"];

function toStudyFileSummary(
  row: StudyFileRow,
): StudyFileSummary {
  return {
    id: row.id,
    subject_id: row.subject_id,
    topic: row.topic,
    original_filename: row.original_filename,
    storage_path: row.storage_path,
    mime_type: row.mime_type,
    size_bytes: row.size_bytes,
    processing_status: row.processing_status,
    failure_message: row.failure_message,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function filenamesMatch(
  firstFilename: string,
  secondFilename: string,
): boolean {
  return (
    firstFilename.trim().toLowerCase() ===
    secondFilename.trim().toLowerCase()
  );
}

function isDuplicateError(
  error: {
    code?: string;
  } | null,
): boolean {
  return error?.code === "23505";
}

function revalidateStudyFilePaths(
  subjectId: string,
): void {
  revalidatePath("/subjects");
  revalidatePath(
    `/subjects/${subjectId}`,
  );
  revalidatePath("/dashboard");
}

/**
 * Creates or prepares a study_files record before the browser
 * uploads the actual object to Supabase Storage.
 */
export async function reserveStudyFileAction(
  payload: unknown,
): Promise<ReserveStudyFileResult> {
  const validation =
    validateReserveStudyFileInput(
      payload,
    );

  if (!validation.success) {
    return {
      success: false,
      message: validation.message,
      fieldErrors:
        validation.fieldErrors,
    };
  }

  const supabase =
    await createClient();

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

  /*
   * Verify that the selected subject belongs to the current
   * authenticated student.
   */
  const {
    data: subject,
    error: subjectError,
  } = await supabase
    .from("subjects")
    .select("id")
    .eq(
      "id",
      validation.data.subjectId,
    )
    .eq("user_id", user.id)
    .maybeSingle();

  if (subjectError) {
    console.error(
      "Subject ownership check failed:",
      {
        code: subjectError.code,
        message:
          subjectError.message,
        details:
          subjectError.details,
        hint: subjectError.hint,
      },
    );

    return {
      success: false,
      message:
        "The selected subject could not be checked.",
      fieldErrors: {
        subjectId:
          "Select one of your subjects.",
      },
    };
  }

  if (!subject) {
    return {
      success: false,
      message:
        "The selected subject was not found.",
      fieldErrors: {
        subjectId:
          "Select one of your subjects.",
      },
    };
  }

  /*
   * Check existing files in the selected subject so that the
   * application can prevent duplicate filenames and reuse
   * failed upload records.
   */
  const {
    data: existingFiles,
    error: existingFilesError,
  } = await supabase
    .from("study_files")
    .select("*")
    .eq("user_id", user.id)
    .eq(
      "subject_id",
      validation.data.subjectId,
    );

  if (existingFilesError) {
    console.error(
      "Duplicate-file check failed:",
      {
        code:
          existingFilesError.code,
        message:
          existingFilesError.message,
        details:
          existingFilesError.details,
        hint:
          existingFilesError.hint,
      },
    );

    return {
      success: false,
      message:
        "The existing files could not be checked.",
    };
  }

  const existingFile =
    existingFiles?.find(
      (file) =>
        filenamesMatch(
          file.original_filename,
          validation.data
            .originalFilename,
        ),
    );

  /*
   * When a previous attempt failed, reuse its database ID and
   * Storage path instead of creating another duplicate record.
   */
  if (
    existingFile &&
    existingFile.processing_status ===
      "failed"
  ) {
    const {
      data: retriedFile,
      error: retryError,
    } = await supabase
      .from("study_files")
      .update({
        topic:
          validation.data.topic,
        mime_type:
          validation.data.mimeType,
        size_bytes:
          validation.data.sizeBytes,
        processing_status:
          "uploading",
        failure_code: null,
        failure_message: null,
        processed_at: null,
      })
      .eq("id", existingFile.id)
      .eq("user_id", user.id)
      .select("*")
      .maybeSingle();

    if (retryError) {
      console.error(
        "Failed-upload retry preparation failed:",
        {
          code: retryError.code,
          message:
            retryError.message,
          details:
            retryError.details,
          hint: retryError.hint,
        },
      );

      return {
        success: false,
        message:
          "The failed upload could not be retried.",
      };
    }

    if (!retriedFile) {
      return {
        success: false,
        message:
          "The failed upload record was not found.",
      };
    }

    revalidateStudyFilePaths(
      retriedFile.subject_id,
    );

    return {
      success: true,
      message:
        "The failed upload is ready to retry.",
      file:
        toStudyFileSummary(
          retriedFile,
        ),
    };
  }

  if (existingFile) {
    return {
      success: false,
      message:
        "A file with this name already exists in the selected subject.",
      fieldErrors: {
        file:
          "Rename the file or remove the existing copy.",
      },
    };
  }

  const fileId = randomUUID();

  const safeFilename =
    sanitizeStorageFilename(
      validation.data
        .originalFilename,
    );

  /*
   * Storage path format:
   *
   * user-id/subject-id/file-id/filename
   */
  const storagePath = [
    user.id,
    validation.data.subjectId,
    fileId,
    safeFilename,
  ].join("/");

  const {
    data: createdFile,
    error: insertError,
  } = await supabase
    .from("study_files")
    .insert({
      id: fileId,
      user_id: user.id,
      subject_id:
        validation.data.subjectId,
      topic: validation.data.topic,
      original_filename:
        validation.data
          .originalFilename,
      storage_path: storagePath,
      mime_type:
        validation.data.mimeType,
      size_bytes:
        validation.data.sizeBytes,
      processing_status:
        "uploading",
      failure_code: null,
      failure_message: null,
      processed_at: null,
    })
    .select("*")
    .single();

  if (insertError) {
    if (
      isDuplicateError(insertError)
    ) {
      return {
        success: false,
        message:
          "A file with this name already exists in the selected subject.",
        fieldErrors: {
          file:
            "Rename the file or remove the existing copy.",
        },
      };
    }

    console.error(
      "Study-file reservation failed:",
      {
        code: insertError.code,
        message:
          insertError.message,
        details:
          insertError.details,
        hint: insertError.hint,
      },
    );

    return {
      success: false,
      message:
        "The upload could not be prepared. Try again.",
    };
  }

  revalidateStudyFilePaths(
    createdFile.subject_id,
  );

  return {
    success: true,
    message:
      "The upload is ready.",
    file:
      toStudyFileSummary(
        createdFile,
      ),
  };
}

/**
 * Marks an uploaded Storage object as ready after the browser
 * completes the resumable upload.
 */
export async function completeStudyFileUploadAction(
  fileId: unknown,
): Promise<StudyFileMutationResult> {
  if (!isValidStudyFileId(fileId)) {
    return {
      success: false,
      message:
        "The uploaded file record is invalid.",
    };
  }

  const supabase =
    await createClient();

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
    data: updatedFile,
    error: updateError,
  } = await supabase
    .from("study_files")
    .update({
      processing_status: "ready",
      failure_code: null,
      failure_message: null,
      processed_at:
        new Date().toISOString(),
    })
    .eq("id", fileId)
    .eq("user_id", user.id)
    .select("*")
    .maybeSingle();

  if (updateError) {
    console.error(
      "Upload completion update failed:",
      {
        code: updateError.code,
        message:
          updateError.message,
        details:
          updateError.details,
        hint: updateError.hint,
      },
    );

    return {
      success: false,
      message:
        "The uploaded file status could not be updated.",
    };
  }

  if (!updatedFile) {
    return {
      success: false,
      message:
        "The uploaded file record was not found.",
    };
  }

  revalidateStudyFilePaths(
    updatedFile.subject_id,
  );

  return {
    success: true,
    message:
      "Your file is ready.",
    file:
      toStudyFileSummary(
        updatedFile,
      ),
  };
}

/**
 * Records that the browser-to-Storage upload failed.
 */
export async function failStudyFileUploadAction(
  fileId: unknown,
): Promise<StudyFileMutationResult> {
  if (!isValidStudyFileId(fileId)) {
    return {
      success: false,
      message:
        "The failed upload record is invalid.",
    };
  }

  const supabase =
    await createClient();

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

  const safeFailureMessage =
    "Upload failed. Check your connection and try again.";

  const {
    data: failedFile,
    error: updateError,
  } = await supabase
    .from("study_files")
    .update({
      processing_status: "failed",
      failure_code:
        "upload_failed",
      failure_message:
        safeFailureMessage,
      processed_at: null,
    })
    .eq("id", fileId)
    .eq("user_id", user.id)
    .select("*")
    .maybeSingle();

  if (updateError) {
    console.error(
      "Failed-upload status update failed:",
      {
        code: updateError.code,
        message:
          updateError.message,
        details:
          updateError.details,
        hint: updateError.hint,
      },
    );

    return {
      success: false,
      message:
        "The failed upload status could not be saved.",
    };
  }

  if (!failedFile) {
    return {
      success: false,
      message:
        "The failed upload record was not found.",
    };
  }

  revalidateStudyFilePaths(
    failedFile.subject_id,
  );

  return {
    success: true,
    message:
      safeFailureMessage,
    file:
      toStudyFileSummary(
        failedFile,
      ),
  };
}

/**
 * Prepares a failed study-file record for another upload attempt.
 *
 * The failed row is reused, but a new Storage path is generated
 * to avoid conflicts with incomplete resumable uploads.
 */
export async function prepareStudyFileRetryAction(
  fileId: unknown,
  payload: unknown,
): Promise<StudyFileMutationResult> {
  if (!isValidStudyFileId(fileId)) {
    return {
      success: false,
      message:
        "The failed file record is invalid.",
    };
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    Array.isArray(payload)
  ) {
    return {
      success: false,
      message:
        "The replacement file information is invalid.",
    };
  }

  const retryPayload =
    payload as Record<string, unknown>;

  const originalFilename =
    typeof retryPayload.originalFilename ===
    "string"
      ? retryPayload.originalFilename.trim()
      : "";

  const mimeType =
    typeof retryPayload.mimeType ===
    "string"
      ? retryPayload.mimeType
      : "";

  const sizeBytes =
    typeof retryPayload.sizeBytes ===
    "number"
      ? retryPayload.sizeBytes
      : Number.NaN;

  const supabase =
    await createClient();

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
    data: existingFile,
    error: fileError,
  } = await supabase
    .from("study_files")
    .select("*")
    .eq("id", fileId)
    .eq("user_id", user.id)
    .maybeSingle();

  if (fileError) {
    console.error(
      "Failed-file retry lookup failed:",
      {
        code: fileError.code,
        message: fileError.message,
        details: fileError.details,
        hint: fileError.hint,
      },
    );

    return {
      success: false,
      message:
        "The failed file could not be checked.",
    };
  }

  if (!existingFile) {
    return {
      success: false,
      message:
        "The failed file was not found or you do not have permission to retry it.",
    };
  }

  if (
    existingFile.processing_status !==
    "failed"
  ) {
    return {
      success: false,
      message:
        "Only failed uploads can be retried.",
    };
  }

  if (
    !filenamesMatch(
      existingFile.original_filename,
      originalFilename,
    )
  ) {
    return {
      success: false,
      message:
        `Select the same file named ${existingFile.original_filename}.`,
    };
  }

  /*
   * Reuse the normal upload validator so retry uploads receive
   * the same MIME-type and file-size checks as new uploads.
   */
  const validation =
    validateReserveStudyFileInput({
      subjectId:
        existingFile.subject_id,
      topic:
        existingFile.topic,
      originalFilename,
      mimeType,
      sizeBytes,
    });

  if (!validation.success) {
    return {
      success: false,
      message:
        validation.fieldErrors.file ??
        validation.message,
    };
  }

  /*
   * Remove any previous complete object that may exist.
   * Supabase normally succeeds even when the path does not exist.
   */
  const {
    error: oldObjectError,
  } = await supabase.storage
    .from(STUDY_MATERIALS_BUCKET)
    .remove([
      existingFile.storage_path,
    ]);

  if (oldObjectError) {
    console.error(
      "Old retry object cleanup failed:",
      {
        name:
          oldObjectError.name,
        message:
          oldObjectError.message,
      },
    );

    return {
      success: false,
      message:
        "The previous upload could not be cleared before retrying.",
    };
  }

  const nextStoragePath = [
    user.id,
    existingFile.subject_id,
    randomUUID(),
    sanitizeStorageFilename(
      validation.data.originalFilename,
    ),
  ].join("/");

  const {
    data: preparedFile,
    error: updateError,
  } = await supabase
    .from("study_files")
    .update({
      storage_path:
        nextStoragePath,
      mime_type:
        validation.data.mimeType,
      size_bytes:
        validation.data.sizeBytes,
      processing_status:
        "uploading",
      failure_code: null,
      failure_message: null,
      processed_at: null,
    })
    .eq("id", existingFile.id)
    .eq("user_id", user.id)
    .select("*")
    .maybeSingle();

  if (updateError) {
    console.error(
      "Failed-file retry preparation failed:",
      {
        code: updateError.code,
        message:
          updateError.message,
        details:
          updateError.details,
        hint:
          updateError.hint,
      },
    );

    return {
      success: false,
      message:
        "The failed upload could not be prepared for retry.",
    };
  }

  if (!preparedFile) {
    return {
      success: false,
      message:
        "The failed upload record was not found.",
    };
  }

  revalidateStudyFilePaths(
    preparedFile.subject_id,
  );

  return {
    success: true,
    message:
      "The failed upload is ready to retry.",
    file:
      toStudyFileSummary(
        preparedFile,
      ),
  };
}

/**
 * Deletes both the private Supabase Storage object and its
 * corresponding study_files database record.
 */
export async function deleteStudyFileAction(
  fileId: unknown,
): Promise<DeleteStudyFileResult> {
  if (!isValidStudyFileId(fileId)) {
    return {
      success: false,
      message:
        "The file record is invalid.",
    };
  }

  const supabase =
    await createClient();

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

  /*
   * Verify ownership and retrieve the private Storage path.
   */
  const {
    data: file,
    error: fileError,
  } = await supabase
    .from("study_files")
    .select("*")
    .eq("id", fileId)
    .eq("user_id", user.id)
    .maybeSingle();

  if (fileError) {
    console.error(
      "Study-file deletion lookup failed:",
      {
        code: fileError.code,
        message:
          fileError.message,
        details:
          fileError.details,
        hint: fileError.hint,
      },
    );

    return {
      success: false,
      message:
        "The file could not be checked before deletion.",
    };
  }

  if (!file) {
    return {
      success: false,
      message:
        "The file was not found or you do not have permission to delete it.",
    };
  }

  /*
   * Delete the private Storage object first.
   */
  const {
    error: storageError,
  } = await supabase.storage
    .from(
      STUDY_MATERIALS_BUCKET,
    )
    .remove([
      file.storage_path,
    ]);

  if (storageError) {
    console.error(
      "Study-file Storage deletion failed:",
      {
        name: storageError.name,
        message:
          storageError.message,
      },
    );

    return {
      success: false,
      message:
        "The stored file could not be deleted. Try again.",
    };
  }

  /*
   * Delete the metadata row after the object has been removed.
   */
  const {
    error: deleteError,
  } = await supabase
    .from("study_files")
    .delete()
    .eq("id", file.id)
    .eq("user_id", user.id);

  if (deleteError) {
    console.error(
      "Study-file record deletion failed:",
      {
        code: deleteError.code,
        message:
          deleteError.message,
        details:
          deleteError.details,
        hint: deleteError.hint,
      },
    );

    return {
      success: false,
      message:
        "The stored file was removed, but its record could not be deleted.",
    };
  }

  revalidateStudyFilePaths(
    file.subject_id,
  );

  return {
    success: true,
    message:
      `${file.original_filename} was deleted.`,
    deletedId: file.id,
  };
}

/**
 * Generates a temporary signed URL for an authenticated user's
 * private study material.
 *
 * The URL expires after five minutes.
 */
export async function createStudyFileAccessAction(
  fileId: unknown,
  mode: unknown,
): Promise<StudyFileAccessResult> {
  if (!isValidStudyFileId(fileId)) {
    return {
      success: false,
      message:
        "The selected file record is invalid.",
    };
  }

  if (
    mode !== "preview" &&
    mode !== "download"
  ) {
    return {
      success: false,
      message:
        "The requested file operation is invalid.",
    };
  }

  const accessMode:
    StudyFileAccessMode = mode;

  const supabase =
    await createClient();

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

  /*
   * Verify ownership before generating the signed URL.
   * Row Level Security provides an additional ownership check.
   */
  const {
    data: file,
    error: fileError,
  } = await supabase
    .from("study_files")
    .select("*")
    .eq("id", fileId)
    .eq("user_id", user.id)
    .maybeSingle();

  if (fileError) {
    console.error(
      "Study-file access lookup failed:",
      {
        code: fileError.code,
        message:
          fileError.message,
        details:
          fileError.details,
        hint: fileError.hint,
      },
    );

    return {
      success: false,
      message:
        "The file could not be checked.",
    };
  }

  if (!file) {
    return {
      success: false,
      message:
        "The file was not found or you do not have permission to access it.",
    };
  }

  if (
    file.processing_status !==
    "ready"
  ) {
    return {
      success: false,
      message:
        "The file is not ready to open yet.",
    };
  }

  const expiresInSeconds =
    5 * 60;

  const signedUrlOptions =
    accessMode === "download"
      ? {
          download:
            file.original_filename,
        }
      : undefined;

  const {
    data: signedUrlData,
    error: signedUrlError,
  } = await supabase.storage
    .from(
      STUDY_MATERIALS_BUCKET,
    )
    .createSignedUrl(
      file.storage_path,
      expiresInSeconds,
      signedUrlOptions,
    );

  if (
    signedUrlError ||
    !signedUrlData?.signedUrl
  ) {
    console.error(
      "Signed file URL creation failed:",
      {
        message:
          signedUrlError?.message,
      },
    );

    return {
      success: false,
      message:
        accessMode === "download"
          ? "The file could not be prepared for download."
          : "The file preview could not be prepared.",
    };
  }

  return {
    success: true,
    url:
      signedUrlData.signedUrl,
    filename:
      file.original_filename,
    mimeType: file.mime_type,
    expiresInSeconds,
  };
}