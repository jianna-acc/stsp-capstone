// File: /frontend/features/files/components/FileUploadManager.tsx
// Purpose: Provides subject-aware file uploads, secure previews,
// downloads, deletion, retry controls, progress tracking, and statuses.

"use client";

import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Paper,
  Progress,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  Dropzone,
  type FileRejection,
} from "@mantine/dropzone";
import {
  modals,
} from "@mantine/modals";
import {
  notifications,
} from "@mantine/notifications";
import {
  IconAlertCircle,
  IconCheck,
  IconDownload,
  IconEye,
  IconFile,
  IconFileText,
  IconFileTypePdf,
  IconPhoto,
  IconPresentation,
  IconRefresh,
  IconTable,
  IconTrash,
  IconUpload,
} from "@tabler/icons-react";
import {
  type ChangeEvent,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  SubjectSummary,
} from "@/features/subjects/types";

import {
  completeStudyFileUploadAction,
  createStudyFileAccessAction,
  deleteStudyFileAction,
  failStudyFileUploadAction,
  prepareStudyFileRetryAction,
  reserveStudyFileAction,
} from "../actions";
import {
  getProcessingStatusMeta,
  MAX_FILE_SIZE_BYTES,
  SUPPORTED_MIME_TYPES,
} from "../constants";
import type {
  StudyFileSummary,
} from "../types";
import {
  uploadStudyFileWithTus,
} from "../upload";
import {
  FilePreviewModal,
} from "./FilePreviewModal";

import classes from "./FileUploadManager.module.css";

interface FileUploadManagerProps {
  subjects: SubjectSummary[];
  initialFiles: StudyFileSummary[];
  initialSubjectId?: string;
  hideSubjectSelector?: boolean;
  title?: string;
  description?: string;
}

interface UploadFieldErrors {
  subjectId?: string;
  topic?: string;
  file?: string;
}

const RETRY_FILE_ACCEPT = [
  ...SUPPORTED_MIME_TYPES,
  ".pdf",
  ".txt",
  ".ppt",
  ".pptx",
  ".xls",
  ".xlsx",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
].join(",");

function formatFileSize(
  bytes: number,
): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(
      bytes / 1024
    ).toFixed(1)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}

function getFileIcon(
  mimeType: string,
) {
  if (
    mimeType ===
    "application/pdf"
  ) {
    return IconFileTypePdf;
  }

  if (
    mimeType ===
    "text/plain"
  ) {
    return IconFileText;
  }

  if (
    mimeType ===
      "application/vnd.ms-powerpoint" ||
    mimeType ===
      "application/vnd.openxmlformats-officedocument.presentationml.presentation"
  ) {
    return IconPresentation;
  }

  if (
    mimeType ===
      "application/vnd.ms-excel" ||
    mimeType ===
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  ) {
    return IconTable;
  }

  if (
    mimeType.startsWith("image/")
  ) {
    return IconPhoto;
  }

  return IconFile;
}

function replaceFile(
  files: StudyFileSummary[],
  nextFile: StudyFileSummary,
): StudyFileSummary[] {
  return [
    nextFile,
    ...files.filter(
      (file) =>
        file.id !== nextFile.id,
    ),
  ];
}

function filenamesMatch(
  firstFilename: string,
  secondFilename: string,
): boolean {
  return (
    firstFilename
      .trim()
      .toLowerCase() ===
    secondFilename
      .trim()
      .toLowerCase()
  );
}

export function FileUploadManager({
  subjects,
  initialFiles,
  initialSubjectId,
  hideSubjectSelector = false,
  title =
    "Upload learning materials",
  description =
    "Add PDFs, PowerPoint presentations, Excel spreadsheets, text files, and images to your academic subjects.",
}: FileUploadManagerProps) {
  const resolvedInitialSubjectId =
    initialSubjectId ??
    subjects[0]?.id ??
    null;

  const [
    selectedSubjectId,
    setSelectedSubjectId,
  ] = useState<string | null>(
    resolvedInitialSubjectId,
  );

  const [
    topic,
    setTopic,
  ] = useState("");

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(
    null,
  );

  const [
    files,
    setFiles,
  ] = useState(initialFiles);

  const [
    progress,
    setProgress,
  ] = useState(0);

  const [
    isUploading,
    setIsUploading,
  ] = useState(false);

  const [
    deletingFileId,
    setDeletingFileId,
  ] = useState<string | null>(
    null,
  );

  const [
    downloadingFileId,
    setDownloadingFileId,
  ] = useState<string | null>(
    null,
  );

  const [
    retryingFileId,
    setRetryingFileId,
  ] = useState<string | null>(
    null,
  );

  const [
    previewFile,
    setPreviewFile,
  ] =
    useState<StudyFileSummary | null>(
      null,
    );

  const [
    previewUrl,
    setPreviewUrl,
  ] = useState<string | null>(
    null,
  );

  const [
    isPreviewLoading,
    setIsPreviewLoading,
  ] = useState(false);

  const [
    fieldErrors,
    setFieldErrors,
  ] =
    useState<UploadFieldErrors>(
      {},
    );

  const retryInputRef =
    useRef<HTMLInputElement | null>(
      null,
    );

  const retryTargetFileRef =
    useRef<StudyFileSummary | null>(
      null,
    );

  const subjectOptions =
    useMemo(
      () =>
        subjects.map(
          (subject) => ({
            value: subject.id,
            label: subject.name,
          }),
        ),
      [subjects],
    );

  const subjectNames =
    useMemo(
      () =>
        new Map(
          subjects.map(
            (subject) => [
              subject.id,
              subject.name,
            ],
          ),
        ),
      [subjects],
    );

  function handleAcceptedFiles(
    acceptedFiles: File[],
  ) {
    const nextFile =
      acceptedFiles[0] ?? null;

    setSelectedFile(nextFile);

    setFieldErrors(
      (current) => ({
        ...current,
        file: undefined,
      }),
    );

    setProgress(0);
  }

  function handleRejectedFiles(
    rejections: FileRejection[],
  ) {
    const firstError =
      rejections[0]?.errors[0];

    const message =
      firstError?.code ===
      "file-too-large"
        ? "The file must be 20 MB or smaller."
        : "Upload a PDF, TXT, PPT, PPTX, XLS, XLSX, JPEG, PNG, or WebP file.";

    setSelectedFile(null);

    setFieldErrors(
      (current) => ({
        ...current,
        file: message,
      }),
    );

    notifications.show({
      title:
        "File not accepted",
      message,
      color: "red",
    });
  }

  function closePreview() {
    setPreviewFile(null);
    setPreviewUrl(null);
    setIsPreviewLoading(false);
  }

  async function openPreview(
    file: StudyFileSummary,
  ) {
    if (
      file.processing_status !==
      "ready"
    ) {
      notifications.show({
        title:
          "Preview unavailable",
        message:
          "The file is not ready to open yet.",
        color: "orange",
      });

      return;
    }

    setPreviewFile(file);
    setPreviewUrl(null);
    setIsPreviewLoading(true);

    try {
      const result =
        await createStudyFileAccessAction(
          file.id,
          "preview",
        );

      if (!result.success) {
        notifications.show({
          title:
            "Preview unavailable",
          message:
            result.message,
          color: "red",
        });

        closePreview();
        return;
      }

      setPreviewUrl(result.url);
    } catch (error: unknown) {
      console.error(
        "Study-file preview failed:",
        error,
      );

      notifications.show({
        title:
          "Preview unavailable",
        message:
          "The secure file preview could not be prepared.",
        color: "red",
      });

      closePreview();
    } finally {
      setIsPreviewLoading(false);
    }
  }

  async function downloadFile(
    file: StudyFileSummary,
  ) {
    if (
      file.processing_status !==
      "ready"
    ) {
      notifications.show({
        title:
          "Download unavailable",
        message:
          "The file is not ready to download yet.",
        color: "orange",
      });

      return;
    }

    setDownloadingFileId(
      file.id,
    );

    try {
      const result =
        await createStudyFileAccessAction(
          file.id,
          "download",
        );

      if (!result.success) {
        notifications.show({
          title:
            "Download unavailable",
          message:
            result.message,
          color: "red",
        });

        return;
      }

      const downloadAnchor =
        document.createElement("a");

      downloadAnchor.href =
        result.url;

      downloadAnchor.download =
        result.filename;

      downloadAnchor.rel =
        "noopener noreferrer";

      document.body.appendChild(
        downloadAnchor,
      );

      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (error: unknown) {
      console.error(
        "Study-file download failed:",
        error,
      );

      notifications.show({
        title:
          "Download unavailable",
        message:
          "The file could not be prepared for download.",
        color: "red",
      });
    } finally {
      setDownloadingFileId(
        null,
      );
    }
  }

  function openRetryFilePicker(
    file: StudyFileSummary,
  ) {
    if (
      file.processing_status !==
      "failed"
    ) {
      notifications.show({
        title:
          "Retry unavailable",
        message:
          "Only failed uploads can be retried.",
        color: "orange",
      });

      return;
    }

    retryTargetFileRef.current =
      file;

    /*
     * Reset the hidden input so selecting the same file again
     * still triggers the change event.
     */
    if (
      retryInputRef.current
    ) {
      retryInputRef.current.value =
        "";
    }

    retryInputRef.current?.click();
  }

  async function handleRetryFileSelected(
    event:
      ChangeEvent<HTMLInputElement>,
  ) {
    const replacementFile =
      event.currentTarget
        .files?.[0] ?? null;

    const failedFile =
      retryTargetFileRef.current;

    event.currentTarget.value =
      "";

    if (
      !replacementFile ||
      !failedFile
    ) {
      retryTargetFileRef.current =
        null;

      return;
    }

    if (
      !filenamesMatch(
        replacementFile.name,
        failedFile.original_filename,
      )
    ) {
      notifications.show({
        title:
          "Different file selected",
        message:
          `Select the same file named ${failedFile.original_filename}.`,
        color: "red",
      });

      retryTargetFileRef.current =
        null;

      return;
    }

    setRetryingFileId(
      failedFile.id,
    );

    setProgress(0);

    try {
      const preparation =
        await prepareStudyFileRetryAction(
          failedFile.id,
          {
            originalFilename:
              replacementFile.name,
            mimeType:
              replacementFile.type,
            sizeBytes:
              replacementFile.size,
          },
        );

      if (!preparation.success) {
        notifications.show({
          title:
            "Retry not started",
          message:
            preparation.message,
          color: "red",
        });

        return;
      }

      setFiles(
        (currentFiles) =>
          replaceFile(
            currentFiles,
            preparation.file,
          ),
      );

      try {
        await uploadStudyFileWithTus({
          file:
            replacementFile,
          storagePath:
            preparation.file
              .storage_path,
          mimeType:
            preparation.file
              .mime_type,
          onProgress:
            setProgress,
        });

        const completion =
          await completeStudyFileUploadAction(
            preparation.file.id,
          );

        if (!completion.success) {
          throw new Error(
            completion.message,
          );
        }

        setFiles(
          (currentFiles) =>
            replaceFile(
              currentFiles,
              completion.file,
            ),
        );

        notifications.show({
          title:
            "Retry complete",
          message:
            `${completion.file.original_filename} is ready.`,
          color: "green",
          icon: (
            <IconCheck
              size={18}
            />
          ),
        });
      } catch (
        retryError: unknown
      ) {
        console.error(
          "Study-file retry upload failed:",
          retryError,
        );

        const failure =
          await failStudyFileUploadAction(
            preparation.file.id,
          );

        if (failure.success) {
          setFiles(
            (currentFiles) =>
              replaceFile(
                currentFiles,
                failure.file,
              ),
          );
        }

        notifications.show({
          title:
            "Retry failed",
          message:
            failure.success
              ? failure.message
              : "The file could not be uploaded again.",
          color: "red",
        });
      }
    } catch (error: unknown) {
      console.error(
        "Study-file retry preparation failed:",
        error,
      );

      notifications.show({
        title:
          "Retry not started",
        message:
          "The failed upload could not be prepared for retry.",
        color: "red",
      });
    } finally {
      setRetryingFileId(null);
      setProgress(0);

      retryTargetFileRef.current =
        null;
    }
  }

  async function executeDeleteFile(
    file: StudyFileSummary,
  ) {
    setDeletingFileId(
      file.id,
    );

    try {
      const result =
        await deleteStudyFileAction(
          file.id,
        );

      if (!result.success) {
        notifications.show({
          title:
            "File not deleted",
          message:
            result.message,
          color: "red",
        });

        return;
      }

      setFiles(
        (currentFiles) =>
          currentFiles.filter(
            (currentFile) =>
              currentFile.id !==
              result.deletedId,
          ),
      );

      if (
        previewFile?.id ===
        result.deletedId
      ) {
        closePreview();
      }

      notifications.show({
        title:
          "File deleted",
        message:
          result.message,
        color: "green",
        icon: (
          <IconCheck size={18} />
        ),
      });
    } catch (error: unknown) {
      console.error(
        "Study-file deletion failed:",
        error,
      );

      notifications.show({
        title:
          "File not deleted",
        message:
          "The file could not be deleted. Try again.",
        color: "red",
      });
    } finally {
      setDeletingFileId(
        null,
      );
    }
  }

  function confirmDeleteFile(
    file: StudyFileSummary,
  ) {
    modals.openConfirmModal({
      title:
        "Delete uploaded file?",
      centered: true,

      children: (
        <Stack gap="xs">
          <Text size="sm">
            Delete{" "}
            <strong>
              {
                file.original_filename
              }
            </strong>
            ?
          </Text>

          <Text
            size="sm"
            c="dimmed"
          >
            This removes both the
            private stored file and
            its database record. This
            action cannot be undone.
          </Text>
        </Stack>
      ),

      labels: {
        confirm:
          "Delete file",
        cancel:
          "Keep file",
      },

      confirmProps: {
        color: "red",
      },

      onConfirm: () => {
        void executeDeleteFile(
          file,
        );
      },
    });
  }

  async function handleUpload() {
    const activeSubjectId =
      selectedSubjectId;

    const activeFile =
      selectedFile;

    const normalizedTopic =
      topic.trim();

    const localErrors:
      UploadFieldErrors = {};

    if (!activeSubjectId) {
      localErrors.subjectId =
        "Select a subject.";
    }

    if (!normalizedTopic) {
      localErrors.topic =
        "Enter a topic.";
    }

    if (!activeFile) {
      localErrors.file =
        "Select a file.";
    }

    if (
      !activeSubjectId ||
      !activeFile ||
      !normalizedTopic
    ) {
      setFieldErrors(
        localErrors,
      );

      return;
    }

    setIsUploading(true);
    setProgress(0);
    setFieldErrors({});

    try {
      const reservation =
        await reserveStudyFileAction({
          subjectId:
            activeSubjectId,
          topic:
            normalizedTopic,
          originalFilename:
            activeFile.name,
          mimeType:
            activeFile.type,
          sizeBytes:
            activeFile.size,
        });

      if (!reservation.success) {
        setFieldErrors(
          reservation.fieldErrors ??
            {},
        );

        notifications.show({
          title:
            "Upload not started",
          message:
            reservation.message,
          color: "red",
        });

        return;
      }

      setFiles(
        (currentFiles) =>
          replaceFile(
            currentFiles,
            reservation.file,
          ),
      );

      try {
        await uploadStudyFileWithTus({
          file:
            activeFile,
          storagePath:
            reservation.file
              .storage_path,
          mimeType:
            reservation.file
              .mime_type,
          onProgress:
            setProgress,
        });

        const completion =
          await completeStudyFileUploadAction(
            reservation.file.id,
          );

        if (!completion.success) {
          throw new Error(
            completion.message,
          );
        }

        setFiles(
          (currentFiles) =>
            replaceFile(
              currentFiles,
              completion.file,
            ),
        );

        notifications.show({
          title:
            "Upload complete",
          message:
            completion.message,
          color: "green",
          icon: (
            <IconCheck
              size={18}
            />
          ),
        });

        setSelectedFile(null);
        setTopic("");
        setProgress(0);
      } catch (
        uploadError: unknown
      ) {
        console.error(
          "Study-file upload failed:",
          uploadError,
        );

        const failure =
          await failStudyFileUploadAction(
            reservation.file.id,
          );

        if (failure.success) {
          setFiles(
            (currentFiles) =>
              replaceFile(
                currentFiles,
                failure.file,
              ),
          );
        }

        notifications.show({
          title:
            "Upload needs attention",
          message:
            failure.success
              ? failure.message
              : "Upload failed. Check your connection and try again.",
          color: "red",
        });
      }
    } catch (error: unknown) {
      console.error(
        "Study-file reservation failed:",
        error,
      );

      notifications.show({
        title:
          "Upload not started",
        message:
          "The upload could not be prepared. Try again.",
        color: "red",
      });
    } finally {
      setIsUploading(false);
    }
  }

  if (
    subjects.length === 0
  ) {
    return (
      <main
        className={classes.page}
      >
        <Paper
          withBorder
          radius="lg"
          p="xl"
          className={
            classes.emptyState
          }
        >
          <ThemeIcon
            size={60}
            radius="xl"
            variant="light"
          >
            <IconUpload
              size={30}
            />
          </ThemeIcon>

          <Title order={2}>
            Create a subject first
          </Title>

          <Text
            c="dimmed"
            ta="center"
            maw={480}
          >
            Learning materials must
            be connected to one of
            your academic subjects.
          </Text>

          <Button
            component="a"
            href="/subjects"
          >
            Open subjects
          </Button>
        </Paper>
      </main>
    );
  }

  const fileListTitle =
    hideSubjectSelector
      ? "Subject materials"
      : "Recent files";

  const operationInProgress =
    isUploading ||
    deletingFileId !== null ||
    downloadingFileId !== null ||
    retryingFileId !== null;

  return (
    <main
      className={classes.page}
    >
      <Stack gap="xl">
        <div>
          <Text
            className={
              classes.eyebrow
            }
            fw={700}
          >
            SUBJECT WORKSPACE
          </Text>

          <Title order={1}>
            {title}
          </Title>

          <Text
            c="dimmed"
            mt="xs"
            maw={680}
          >
            {description}
          </Text>
        </div>

        <SimpleGrid
          cols={{
            base: 1,
            lg: 2,
          }}
          spacing="xl"
        >
          <Card
            withBorder
            radius="lg"
            padding="xl"
          >
            <Stack gap="lg">
              {!hideSubjectSelector && (
                <Select
                  label="Subject"
                  description="Choose where this material belongs"
                  data={
                    subjectOptions
                  }
                  value={
                    selectedSubjectId
                  }
                  error={
                    fieldErrors
                      .subjectId
                  }
                  allowDeselect={
                    false
                  }
                  required
                  disabled={
                    operationInProgress
                  }
                  onChange={(value) => {
                    setSelectedSubjectId(
                      value,
                    );

                    setFieldErrors(
                      (current) => ({
                        ...current,
                        subjectId:
                          undefined,
                      }),
                    );
                  }}
                />
              )}

              <TextInput
                label="Topic"
                description="For example: Photosynthesis, Chapter 4, or Financial Analysis"
                placeholder="Enter the material topic"
                value={topic}
                error={
                  fieldErrors.topic
                }
                maxLength={120}
                required
                disabled={
                  operationInProgress
                }
                onChange={(event) => {
                  const nextTopic =
                    event.currentTarget
                      .value;

                  setTopic(nextTopic);

                  setFieldErrors(
                    (current) => ({
                      ...current,
                      topic: undefined,
                    }),
                  );
                }}
              />

              <div>
                <Dropzone
                  accept={[
                    ...SUPPORTED_MIME_TYPES,
                  ]}
                  maxSize={
                    MAX_FILE_SIZE_BYTES
                  }
                  maxFiles={1}
                  multiple={false}
                  disabled={
                    operationInProgress
                  }
                  onDrop={
                    handleAcceptedFiles
                  }
                  onReject={
                    handleRejectedFiles
                  }
                  className={
                    classes.dropzone
                  }
                >
                  <Group
                    justify="center"
                    gap="xl"
                    mih={150}
                    className={
                      classes
                        .dropzoneContent
                    }
                  >
                    <Dropzone.Accept>
                      <IconUpload
                        size={42}
                      />
                    </Dropzone.Accept>

                    <Dropzone.Reject>
                      <IconAlertCircle
                        size={42}
                      />
                    </Dropzone.Reject>

                    <Dropzone.Idle>
                      <IconUpload
                        size={42}
                      />
                    </Dropzone.Idle>

                    <Stack gap={4}>
                      <Text
                        fw={700}
                        size="lg"
                      >
                        Drop one file here
                      </Text>

                      <Text
                        c="dimmed"
                        size="sm"
                      >
                        PDF, PPT, PPTX,
                        XLS, XLSX, TXT,
                        JPEG, PNG, or
                        WebP — maximum
                        20 MB
                      </Text>
                    </Stack>
                  </Group>
                </Dropzone>

                {fieldErrors.file && (
                  <Text
                    c="red"
                    size="sm"
                    mt={6}
                  >
                    {
                      fieldErrors.file
                    }
                  </Text>
                )}
              </div>

              {selectedFile && (
                <Paper
                  withBorder
                  radius="md"
                  p="md"
                >
                  <Group
                    justify="space-between"
                    wrap="nowrap"
                  >
                    <div>
                      <Text
                        fw={700}
                        className={
                          classes.filename
                        }
                      >
                        {
                          selectedFile.name
                        }
                      </Text>

                      <Text
                        c="dimmed"
                        size="sm"
                      >
                        {formatFileSize(
                          selectedFile.size,
                        )}
                      </Text>
                    </div>

                    <Badge
                      variant="light"
                    >
                      Selected
                    </Badge>
                  </Group>
                </Paper>
              )}

              {isUploading && (
                <Stack gap={6}>
                  <Group
                    justify="space-between"
                  >
                    <Text
                      fw={600}
                      size="sm"
                    >
                      Uploading
                    </Text>

                    <Text size="sm">
                      {progress}%
                    </Text>
                  </Group>

                  <Progress
                    value={progress}
                    animated={
                      progress < 100
                    }
                    radius="xl"
                  />
                </Stack>
              )}

              <Button
                leftSection={
                  <IconUpload
                    size={18}
                  />
                }
                loading={
                  isUploading
                }
                disabled={
                  deletingFileId !==
                    null ||
                  downloadingFileId !==
                    null ||
                  retryingFileId !==
                    null ||
                  !selectedFile ||
                  !selectedSubjectId ||
                  !topic.trim()
                }
                onClick={() => {
                  void handleUpload();
                }}
              >
                Upload file
              </Button>
            </Stack>
          </Card>

          <Card
            withBorder
            radius="lg"
            padding="xl"
          >
            <Stack gap="lg">
              <div>
                <Title order={2}>
                  {fileListTitle}
                </Title>

                <Text
                  c="dimmed"
                  size="sm"
                  mt={4}
                >
                  Uploaded materials,
                  processing statuses,
                  and file controls
                  appear here.
                </Text>
              </div>

              {files.length === 0 ? (
                <Alert
                  color="gray"
                  title="No files uploaded"
                >
                  Upload your first
                  learning material for
                  this subject.
                </Alert>
              ) : (
                <Stack gap="sm">
                  {files.map((file) => {
                    const status =
                      getProcessingStatusMeta(
                        file.processing_status,
                      );

                    const FileIcon =
                      getFileIcon(
                        file.mime_type,
                      );

                    const isDeleting =
                      deletingFileId ===
                      file.id;

                    const isDownloading =
                      downloadingFileId ===
                      file.id;

                    const isRetrying =
                      retryingFileId ===
                      file.id;

                    const fileIsReady =
                      file.processing_status ===
                      "ready";

                    const fileHasFailed =
                      file.processing_status ===
                      "failed";

                    return (
                      <Paper
                        key={file.id}
                        withBorder
                        radius="md"
                        p="md"
                      >
                        <Group
                          justify="space-between"
                          align="flex-start"
                          wrap="nowrap"
                        >
                          <Group
                            align="flex-start"
                            wrap="nowrap"
                          >
                            <ThemeIcon
                              variant="light"
                              color={
                                status.color
                              }
                              size={42}
                              radius="md"
                            >
                              <FileIcon
                                size={22}
                              />
                            </ThemeIcon>

                            <div>
                              <Text
                                fw={700}
                                className={
                                  classes.filename
                                }
                              >
                                {
                                  file.original_filename
                                }
                              </Text>

                              <Text
                                c="dimmed"
                                size="sm"
                              >
                                {
                                  subjectNames.get(
                                    file.subject_id,
                                  ) ??
                                  "Unknown subject"
                                }
                                {" · "}
                                {file.topic}
                              </Text>

                              <Text
                                c="dimmed"
                                size="xs"
                                mt={3}
                              >
                                {formatFileSize(
                                  file.size_bytes,
                                )}
                              </Text>
                            </div>
                          </Group>

                          <Badge
                            color={
                              status.color
                            }
                            variant="light"
                          >
                            {status.label}
                          </Badge>
                        </Group>

                        {file.failure_message && (
                          <Alert
                            color="red"
                            mt="md"
                            icon={
                              <IconAlertCircle
                                size={17}
                              />
                            }
                          >
                            {
                              file.failure_message
                            }
                          </Alert>
                        )}

                        {isRetrying && (
                          <Stack
                            gap={6}
                            mt="md"
                          >
                            <Group
                              justify="space-between"
                            >
                              <Text
                                fw={600}
                                size="sm"
                              >
                                Retrying upload
                              </Text>

                              <Text size="sm">
                                {progress}%
                              </Text>
                            </Group>

                            <Progress
                              value={progress}
                              animated={
                                progress < 100
                              }
                              radius="xl"
                            />
                          </Stack>
                        )}

                        <Group
                          justify="flex-end"
                          mt="md"
                          gap="xs"
                        >
                          {fileHasFailed && (
                            <Button
                              variant="light"
                              color="orange"
                              size="compact-sm"
                              leftSection={
                                <IconRefresh
                                  size={16}
                                />
                              }
                              loading={
                                isRetrying
                              }
                              disabled={
                                isUploading ||
                                deletingFileId !==
                                  null ||
                                downloadingFileId !==
                                  null ||
                                (
                                  retryingFileId !==
                                    null &&
                                  !isRetrying
                                )
                              }
                              onClick={() => {
                                openRetryFilePicker(
                                  file,
                                );
                              }}
                            >
                              Retry upload
                            </Button>
                          )}

                          {fileIsReady && (
                            <>
                              <Button
                                variant="light"
                                size="compact-sm"
                                leftSection={
                                  <IconEye
                                    size={16}
                                  />
                                }
                                disabled={
                                  isUploading ||
                                  deletingFileId !==
                                    null ||
                                  downloadingFileId !==
                                    null ||
                                  retryingFileId !==
                                    null
                                }
                                onClick={() => {
                                  void openPreview(
                                    file,
                                  );
                                }}
                              >
                                Preview
                              </Button>

                              <Button
                                variant="light"
                                size="compact-sm"
                                leftSection={
                                  <IconDownload
                                    size={16}
                                  />
                                }
                                loading={
                                  isDownloading
                                }
                                disabled={
                                  isUploading ||
                                  deletingFileId !==
                                    null ||
                                  retryingFileId !==
                                    null ||
                                  (
                                    downloadingFileId !==
                                      null &&
                                    !isDownloading
                                  )
                                }
                                onClick={() => {
                                  void downloadFile(
                                    file,
                                  );
                                }}
                              >
                                Download
                              </Button>
                            </>
                          )}

                          <Button
                            color="red"
                            variant="subtle"
                            size="compact-sm"
                            leftSection={
                              <IconTrash
                                size={16}
                              />
                            }
                            loading={
                              isDeleting
                            }
                            disabled={
                              isUploading ||
                              downloadingFileId !==
                                null ||
                              retryingFileId !==
                                null ||
                              (
                                deletingFileId !==
                                  null &&
                                !isDeleting
                              )
                            }
                            onClick={() => {
                              confirmDeleteFile(
                                file,
                              );
                            }}
                          >
                            Delete file
                          </Button>
                        </Group>
                      </Paper>
                    );
                  })}
                </Stack>
              )}
            </Stack>
          </Card>
        </SimpleGrid>
      </Stack>

      <input
        ref={retryInputRef}
        type="file"
        hidden
        accept={
          RETRY_FILE_ACCEPT
        }
        onChange={(event) => {
          void handleRetryFileSelected(
            event,
          );
        }}
      />

      <FilePreviewModal
        file={previewFile}
        signedUrl={previewUrl}
        opened={
          previewFile !== null
        }
        loading={
          isPreviewLoading
        }
        downloading={
          previewFile
            ? downloadingFileId ===
              previewFile.id
            : false
        }
        onClose={closePreview}
        onDownload={() => {
          if (previewFile) {
            void downloadFile(
              previewFile,
            );
          }
        }}
      />
    </main>
  );
}