// File: /frontend/app/(protected)/study-assistant/page.tsx
// Purpose: Renders the protected AI Study Assistant workspace
// and loads the authenticated student's filter options.

import type { Metadata } from "next";

import { StudyAssistantPanel } from "@/features/study-assistant/components/StudyAssistantPanel";
import { getStudyAssistantFilterOptions } from "@/features/study-assistant/server/options";

export const metadata: Metadata = {
  title: "Study Assistant | STS Capstone",
  description:
    "Ask questions grounded in your uploaded study materials.",
};

export default async function StudyAssistantPage() {
  const filterOptions =
    await getStudyAssistantFilterOptions();

  return (
    <StudyAssistantPanel
      filterOptions={filterOptions}
    />
  );
}