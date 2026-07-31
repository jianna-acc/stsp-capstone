// File: /frontend/features/files/constants.ts
// Purpose: Defines supported learning-material types, upload limits,
// and student-friendly processing-status labels.

export const STUDY_MATERIALS_BUCKET =
  "study-materials";

export const MAX_FILE_SIZE_BYTES =
  20 * 1024 * 1024;

export const TUS_CHUNK_SIZE_BYTES =
  6 * 1024 * 1024;

export const SUPPORTED_MIME_TYPES = [
  "application/pdf",
  "text/plain",
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/vnd.ms-powerpoint",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
] as const;

export type SupportedMimeType =
  (typeof SUPPORTED_MIME_TYPES)[number];

export type ProcessingStatus =
  | "uploading"
  | "reading"
  | "indexing"
  | "ready"
  | "failed";

export const PROCESSING_STATUS_META: Record<
  ProcessingStatus,
  {
    label: string;
    color: string;
    description: string;
  }
> = {
  uploading: {
    label: "Uploading",
    color: "violet",
    description:
      "Your file is being transferred.",
  },

  reading: {
    label: "Reading your file",
    color: "blue",
    description:
      "The learning material is being read.",
  },

  indexing: {
    label: "Creating study index",
    color: "cyan",
    description:
      "The material is being prepared for study tools.",
  },

  ready: {
    label: "Ready",
    color: "green",
    description:
      "The file is available for use.",
  },

  failed: {
    label: "Needs attention",
    color: "red",
    description:
      "The upload could not be completed.",
  },
};

export function getProcessingStatusMeta(
  status: string,
) {
  if (status in PROCESSING_STATUS_META) {
    return PROCESSING_STATUS_META[
      status as ProcessingStatus
    ];
  }

  return PROCESSING_STATUS_META.failed;
}