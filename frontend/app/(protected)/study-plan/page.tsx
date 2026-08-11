// File: /frontend/app/(protected)/study-plan/page.tsx
// Purpose: Renders the protected Track D study-plan calendar
// and loads the authenticated student's subject display data.

import type { Metadata } from "next";

import {
  StudyPlansWorkspace,
} from "@/features/study-plans/components/StudyPlansWorkspace";
import {
  getSubjects,
} from "@/features/subjects/queries";


export const metadata: Metadata = {
  title: "Study Plan | STS Capstone",
  description:
    "View study plans and scheduled study sessions in a weekly calendar.",
};


export default async function StudyPlanPage() {
  const subjects =
    await getSubjects();

  return (
    <StudyPlansWorkspace
      initialSubjects={subjects}
    />
  );
}