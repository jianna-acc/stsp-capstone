// File: /frontend/features/files/components/FilePreviewModal.tsx
// Purpose: Displays secure temporary previews of private files
// and provides a download option for all supported formats.

"use client";

import {
  Alert,
  Button,
  Center,
  Group,
  Image,
  Loader,
  Modal,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconDownload,
  IconEyeOff,
  IconFile,
} from "@tabler/icons-react";

import type {
  StudyFileSummary,
} from "../types";

import classes from "./FilePreviewModal.module.css";

interface FilePreviewModalProps {
  file: StudyFileSummary | null;
  signedUrl: string | null;
  opened: boolean;
  loading: boolean;
  downloading: boolean;
  onClose: () => void;
  onDownload: () => void;
}

function isImageFile(
  mimeType: string,
): boolean {
  return mimeType.startsWith(
    "image/",
  );
}

function isPdfFile(
  mimeType: string,
): boolean {
  return (
    mimeType ===
    "application/pdf"
  );
}

function isTextFile(
  mimeType: string,
): boolean {
  return (
    mimeType ===
    "text/plain"
  );
}

function supportsInlinePreview(
  mimeType: string,
): boolean {
  return (
    isImageFile(mimeType) ||
    isPdfFile(mimeType) ||
    isTextFile(mimeType)
  );
}

export function FilePreviewModal({
  file,
  signedUrl,
  opened,
  loading,
  downloading,
  onClose,
  onDownload,
}: FilePreviewModalProps) {
  const canPreview =
    file
      ? supportsInlinePreview(
          file.mime_type,
        )
      : false;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        file?.original_filename ??
        "File preview"
      }
      size="xl"
      centered
      radius="lg"
    >
      <Stack gap="md">
        {loading && (
          <Center mih={360}>
            <Stack
              align="center"
              gap="sm"
            >
              <Loader />

              <Text c="dimmed">
                Preparing secure
                preview...
              </Text>
            </Stack>
          </Center>
        )}

        {!loading &&
          file &&
          !canPreview && (
            <Paper
              withBorder
              className={
                classes.unavailable
              }
            >
              <Stack
                align="center"
                gap="md"
                maw={460}
              >
                <ThemeIcon
                  size={58}
                  radius="xl"
                  variant="light"
                >
                  <IconEyeOff
                    size={28}
                  />
                </ThemeIcon>

                <div>
                  <Title order={3}>
                    Browser preview is
                    unavailable
                  </Title>

                  <Text
                    c="dimmed"
                    mt={6}
                  >
                    PowerPoint and Excel
                    files can be downloaded
                    securely. Their slide
                    and worksheet contents
                    will be processed by
                    the FastAPI backend in
                    the next phase.
                  </Text>
                </div>
              </Stack>
            </Paper>
          )}

        {!loading &&
          file &&
          signedUrl &&
          isImageFile(
            file.mime_type,
          ) && (
            <div
              className={
                classes.previewArea
              }
            >
              <div
                className={
                  classes.imageWrapper
                }
              >
                <Image
                  src={signedUrl}
                  alt={
                    file.original_filename
                  }
                  className={
                    classes.image
                  }
                  fit="contain"
                />
              </div>
            </div>
          )}

        {!loading &&
          file &&
          signedUrl &&
          (
            isPdfFile(
              file.mime_type,
            ) ||
            isTextFile(
              file.mime_type,
            )
          ) && (
            <div
              className={
                classes.previewArea
              }
            >
              <iframe
                src={signedUrl}
                title={`Preview of ${file.original_filename}`}
                className={
                  classes.frame
                }
              />
            </div>
          )}

        {!loading &&
          !file && (
            <Alert
              color="red"
              icon={
                <IconFile
                  size={18}
                />
              }
            >
              No file was selected.
            </Alert>
          )}

        <Group
          justify="flex-end"
        >
          <Button
            variant="default"
            onClick={onClose}
          >
            Close
          </Button>

          {file && (
            <Button
              leftSection={
                <IconDownload
                  size={18}
                />
              }
              loading={downloading}
              onClick={onDownload}
            >
              Download
            </Button>
          )}
        </Group>
      </Stack>
    </Modal>
  );
}