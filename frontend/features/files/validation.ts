// File: /frontend/features/files/validation.ts
// Purpose: Validates and normalizes untrusted file-upload
// metadata before a study_files record is created.

import {
  MAX_FILE_SIZE_BYTES,
  SUPPORTED_MIME_TYPES,
  type SupportedMimeType,
} from "./constants";
import type {
  ReserveStudyFileInput,
} from "./types";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type ValidatedFileInput = {
  subjectId: string;
  topic: string;
  originalFilename: string;
  mimeType: SupportedMimeType;
  sizeBytes: number;
};

type ValidationResult =
  | {
      success: true;
      data: ValidatedFileInput;
    }
  | {
      success: false;
      message: string;
      fieldErrors: {
        subjectId?: string;
        topic?: string;
        file?: string;
      };
    };

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function normalizeMimeType(
  filename: string,
  suppliedMimeType: string,
): SupportedMimeType | null {
  const supplied =
    suppliedMimeType
      .trim()
      .toLowerCase();

  if (
    SUPPORTED_MIME_TYPES.includes(
      supplied as SupportedMimeType,
    )
  ) {
    return supplied as SupportedMimeType;
  }

  /*
   * Some browsers and operating systems may return an empty
   * or generic MIME type. Use the extension as a controlled
   * fallback and convert it to the application's canonical
   * MIME type.
   */
  const extension =
    filename
      .split(".")
      .pop()
      ?.toLowerCase() ?? "";

  const extensionMap: Record<
    string,
    SupportedMimeType
  > = {
    pdf: "application/pdf",
    txt: "text/plain",

    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    png: "image/png",
    webp: "image/webp",

    ppt:
      "application/vnd.ms-powerpoint",
    pptx:
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    xls:
      "application/vnd.ms-excel",
    xlsx:
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  };

  return extensionMap[extension] ?? null;
}

export function sanitizeStorageFilename(
  filename: string,
): string {
  const sanitized = filename
    .normalize("NFKD")
    .replace(/[^\w.\-\s]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^\.+/, "");

  return sanitized || "study-material";
}

export function validateReserveStudyFileInput(
  input: unknown,
): ValidationResult {
  if (!isRecord(input)) {
    return {
      success: false,
      message:
        "Check the upload information and try again.",
      fieldErrors: {
        subjectId:
          "Select a subject.",
        topic:
          "Enter a topic.",
        file:
          "Select a supported file.",
      },
    };
  }

  const subjectId =
    typeof input.subjectId === "string"
      ? input.subjectId.trim()
      : "";

  const topic =
    typeof input.topic === "string"
      ? input.topic
          .trim()
          .replace(/\s+/g, " ")
      : "";

  const originalFilename =
    typeof input.originalFilename === "string"
      ? input.originalFilename.trim()
      : "";

  const suppliedMimeType =
    typeof input.mimeType === "string"
      ? input.mimeType
      : "";

  const sizeBytes =
    typeof input.sizeBytes === "number"
      ? input.sizeBytes
      : Number.NaN;

  const fieldErrors: {
    subjectId?: string;
    topic?: string;
    file?: string;
  } = {};

  if (
    !subjectId ||
    !UUID_PATTERN.test(subjectId)
  ) {
    fieldErrors.subjectId =
      "Select a valid subject.";
  }

  if (!topic) {
    fieldErrors.topic =
      "Enter a topic.";
  } else if (topic.length > 120) {
    fieldErrors.topic =
      "The topic must be 120 characters or fewer.";
  }

  if (!originalFilename) {
    fieldErrors.file =
      "Select a supported file.";
  } else if (
    originalFilename.length > 255
  ) {
    fieldErrors.file =
      "The filename must be 255 characters or fewer.";
  } else if (
    originalFilename.includes("/") ||
    originalFilename.includes("\\")
  ) {
    fieldErrors.file =
      "The filename contains invalid characters.";
  }

  const mimeType =
    normalizeMimeType(
      originalFilename,
      suppliedMimeType,
    );

  if (!mimeType) {
    fieldErrors.file =
      "Upload a PDF, TXT, PPT, PPTX, XLS, XLSX, JPEG, PNG, or WebP file.";
  }

  if (
    !Number.isSafeInteger(sizeBytes) ||
    sizeBytes < 1
  ) {
    fieldErrors.file =
      "The selected file is empty or invalid.";
  } else if (
    sizeBytes > MAX_FILE_SIZE_BYTES
  ) {
    fieldErrors.file =
      "The file must be 20 MB or smaller.";
  }

  if (
    Object.keys(fieldErrors).length >
    0
  ) {
    return {
      success: false,
      message:
        "Check the upload information and try again.",
      fieldErrors,
    };
  }

  return {
    success: true,
    data: {
      subjectId,
      topic,
      originalFilename,
      mimeType:
        mimeType as SupportedMimeType,
      sizeBytes,
    },
  };
}

export function isValidStudyFileId(
  value: unknown,
): value is string {
  return (
    typeof value === "string" &&
    UUID_PATTERN.test(value)
  );
}

export function isReserveStudyFileInput(
  value: unknown,
): value is ReserveStudyFileInput {
  return (
    isRecord(value) &&
    typeof value.subjectId ===
      "string" &&
    typeof value.topic ===
      "string" &&
    typeof value.originalFilename ===
      "string" &&
    typeof value.mimeType ===
      "string" &&
    typeof value.sizeBytes ===
      "number"
  );
}