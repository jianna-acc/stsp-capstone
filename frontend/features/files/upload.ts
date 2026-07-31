// File: /frontend/features/files/upload.ts
// Purpose: Uploads one authenticated learning material to the
// private Supabase Storage bucket using resumable TUS uploads.

"use client";

import * as tus from "tus-js-client";

import {
  createClient,
} from "@/lib/supabase/client";
import {
  getSupabasePublicConfig,
} from "@/lib/supabase/config";

import {
  STUDY_MATERIALS_BUCKET,
  TUS_CHUNK_SIZE_BYTES,
} from "./constants";

interface UploadStudyFileOptions {
  file: File;
  storagePath: string;
  mimeType: string;
  onProgress: (
    percentage: number,
  ) => void;
}

function getResumableUploadEndpoint(
  supabaseUrl: string,
): string {
  const normalizedUrl =
    supabaseUrl.replace(/\/$/, "");

  try {
    const parsedUrl =
      new URL(normalizedUrl);

    /*
     * A normal hosted project URL resembles:
     *
     * https://PROJECT_REF.supabase.co
     *
     * Supabase recommends the direct Storage hostname for
     * resumable uploads:
     *
     * https://PROJECT_REF.storage.supabase.co
     */
    if (
      parsedUrl.hostname.endsWith(
        ".supabase.co",
      )
    ) {
      const projectReference =
        parsedUrl.hostname.split(".")[0];

      if (projectReference) {
        return [
          parsedUrl.protocol,
          "//",
          projectReference,
          ".storage.supabase.co",
          "/storage/v1/upload/resumable",
        ].join("");
      }
    }
  } catch {
    /*
     * Fall back to the configured project URL when the URL
     * uses a custom domain or cannot be parsed normally.
     */
  }

  return [
    normalizedUrl,
    "/storage/v1/upload/resumable",
  ].join("");
}

function normalizeUploadError(
  error: unknown,
): Error {
  if (error instanceof Error) {
    return error;
  }

  return new Error(
    "The resumable upload could not be started.",
  );
}

export async function uploadStudyFileWithTus({
  file,
  storagePath,
  mimeType,
  onProgress,
}: UploadStudyFileOptions): Promise<void> {
  const supabase = createClient();

  /*
   * The access token is forwarded to Supabase Storage.
   * Storage validates the token and applies the bucket's
   * Row Level Security policies.
   */
  const {
    data: { session },
    error: sessionError,
  } = await supabase.auth.getSession();

  if (
    sessionError ||
    !session?.access_token
  ) {
    throw new Error(
      "Your session has expired. Sign in again.",
    );
  }

  const {
    url,
  } = getSupabasePublicConfig();

  const endpoint =
    getResumableUploadEndpoint(url);

  await new Promise<void>(
    (resolve, reject) => {
      const upload = new tus.Upload(
        file,
        {
          endpoint,

          retryDelays: [
            0,
            1000,
            3000,
            5000,
            10000,
          ],

          headers: {
            authorization:
              `Bearer ${session.access_token}`,
            "x-upsert": "false",
          },

          uploadDataDuringCreation: true,
          removeFingerprintOnSuccess: true,
          chunkSize:
            TUS_CHUNK_SIZE_BYTES,

          metadata: {
            bucketName:
              STUDY_MATERIALS_BUCKET,
            objectName: storagePath,
            contentType: mimeType,
            cacheControl: "3600",
          },

          onError(
            error: Error,
          ) {
            reject(error);
          },

          onProgress(
            bytesUploaded: number,
            bytesTotal: number,
          ) {
            if (bytesTotal <= 0) {
              onProgress(0);
              return;
            }

            const percentage =
              Math.min(
                100,
                Math.max(
                  0,
                  Math.round(
                    (
                      bytesUploaded /
                      bytesTotal
                    ) * 100,
                  ),
                ),
              );

            onProgress(percentage);
          },

          onSuccess() {
            onProgress(100);
            resolve();
          },
        },
      );

      /*
       * Use an async function instead of a Promise.then()
       * callback. This avoids implicit-any callback parameters
       * and makes resume failures easier to handle.
       */
      void (async () => {
        try {
          const previousUploads =
            await upload.findPreviousUploads();

          if (
            previousUploads.length > 0
          ) {
            upload.resumeFromPreviousUpload(
              previousUploads[0],
            );
          }

          upload.start();
        } catch (error: unknown) {
          reject(
            normalizeUploadError(error),
          );
        }
      })();
    },
  );
}