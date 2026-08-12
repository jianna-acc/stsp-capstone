// File: /frontend/app/(protected)/academic-tasks/page.tsx
// Purpose: Loads student-owned subjects on the server and
// renders the Academic Tasks workspace.

import type { Metadata } from "next";

import {
  AcademicTasksWorkspace,
} from "@/features/academic-tasks/components/AcademicTasksWorkspace";
import {
  getSubjects,
} from "@/features/subjects/queries";

export const metadata: Metadata = {
  title:
    "Academic Tasks | Intelleap",
  description:
    "Manage academic deadlines, workload, and task priorities.",
};

export default async function AcademicTasksPage() {
  const subjects =
    await getSubjects();

  return (
    <AcademicTasksWorkspace
      subjects={subjects}
    />
  );
}