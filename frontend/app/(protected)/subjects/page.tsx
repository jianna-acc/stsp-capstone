// File: /frontend/app/(protected)/subjects/page.tsx
// Purpose: Loads student-owned subjects on the server and
// renders the Phase 3 subject-management interface.

import type { Metadata } from "next";

import { SubjectsManager } from "@/features/subjects/components/SubjectsManager";
import { getSubjects } from "@/features/subjects/queries";

export const metadata: Metadata = {
  title: "Subjects | STS Capstone",
  description:
    "Create and organize academic subjects and learning materials.",
};

export default async function SubjectsPage() {
  const subjects = await getSubjects();

  return (
    <SubjectsManager
      initialSubjects={subjects}
    />
  );
}