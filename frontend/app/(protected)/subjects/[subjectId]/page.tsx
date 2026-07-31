// File: /frontend/app/(protected)/subjects/[subjectId]/page.tsx
// Purpose: Displays one selected subject together with its
// upload form, material list, progress, and processing statuses.

import type { Metadata } from "next";

import {
  Anchor,
  Container,
  Group,
  Stack,
  Text,
} from "@mantine/core";
import { IconArrowLeft } from "@tabler/icons-react";
import { notFound } from "next/navigation";

import { FileUploadManager } from "@/features/files/components/FileUploadManager";
import { getStudyFiles } from "@/features/files/queries";
import { SubjectTabs } from "@/features/subjects/components/SubjectTabs";
import { getSubjects } from "@/features/subjects/queries";

export const metadata: Metadata = {
  title:
    "Subject Workspace | STS Capstone Project",
  description:
    "Upload and manage learning materials for an academic subject.",
};

interface SubjectWorkspacePageProps {
  params: Promise<{
    subjectId: string;
  }>;
}

export default async function SubjectWorkspacePage({
  params,
}: SubjectWorkspacePageProps) {
  const { subjectId } = await params;

  const [
    subjects,
    allFiles,
  ] = await Promise.all([
    getSubjects(),
    getStudyFiles(),
  ]);

  const activeSubject = subjects.find(
    (subject) =>
      subject.id === subjectId,
  );

  if (!activeSubject) {
    notFound();
  }

  const subjectFiles = allFiles.filter(
    (file) =>
      file.subject_id ===
      activeSubject.id,
  );

  return (
    <Stack gap={0}>
      <Container
        size="xl"
        w="100%"
        pt={{
          base: 22,
          sm: 32,
        }}
        px={{
          base: 16,
          sm: 32,
        }}
      >
        <Stack gap="md">
          <Anchor
            href="/subjects"
            c="dimmed"
            size="sm"
            w="fit-content"
          >
            <Group gap={6}>
              <IconArrowLeft size={16} />

              <Text size="sm">
                All subjects
              </Text>
            </Group>
          </Anchor>

          <SubjectTabs
            subjects={subjects}
            activeSubjectId={
              activeSubject.id
            }
          />
        </Stack>
      </Container>

      <FileUploadManager
        key={activeSubject.id}
        subjects={[activeSubject]}
        initialFiles={subjectFiles}
        initialSubjectId={
            activeSubject.id
        }
        hideSubjectSelector
        title={activeSubject.name}
        description={`Upload and manage learning materials for ${activeSubject.name}.`}
        />
            </Stack>
  );
}