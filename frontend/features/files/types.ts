// File: /frontend/features/files/types.ts
// Purpose: Defines study-file records, upload inputs,
// mutations, deletion results, and secure access results.

import type {
  Database,
} from "@/types/database";

type StudyFileRow =
  Database["public"]["Tables"]["study_files"]["Row"];

export type StudyFileSummary = Pick<
  StudyFileRow,
  | "id"
  | "subject_id"
  | "topic"
  | "original_filename"
  | "storage_path"
  | "mime_type"
  | "size_bytes"
  | "processing_status"
  | "failure_message"
  | "created_at"
  | "updated_at"
>;

export type ReserveStudyFileInput = {
  subjectId: string;
  topic: string;
  originalFilename: string;
  mimeType: string;
  sizeBytes: number;
};

export type ReserveStudyFileResult =
  | {
      success: true;
      message: string;
      file: StudyFileSummary;
    }
  | {
      success: false;
      message: string;
      fieldErrors?: {
        subjectId?: string;
        topic?: string;
        file?: string;
      };
    };

export type StudyFileMutationResult =
  | {
      success: true;
      message: string;
      file: StudyFileSummary;
    }
  | {
      success: false;
      message: string;
    };

export type DeleteStudyFileResult =
  | {
      success: true;
      message: string;
      deletedId: string;
    }
  | {
      success: false;
      message: string;
    };

export type StudyFileAccessMode =
  | "preview"
  | "download";

export type StudyFileAccessResult =
  | {
      success: true;
      url: string;
      filename: string;
      mimeType: string;
      expiresInSeconds: number;
    }
  | {
      success: false;
      message: string;
    };