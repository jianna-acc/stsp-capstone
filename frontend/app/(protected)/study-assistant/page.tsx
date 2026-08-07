// File: /frontend/app/(protected)/study-assistant/page.tsx
// Purpose: Renders the protected Study Assistant workspace
// with saved conversations and authenticated filter options.

import type {
  Metadata,
} from "next";

import {
  StudyAssistantWorkspace,
} from "@/features/study-assistant/components/StudyAssistantWorkspace";
import {
  getStudyAssistantFilterOptions,
} from "@/features/study-assistant/server/options";

export const metadata: Metadata = {
  title:
    "Study Assistant | STS Capstone",

  description:
    "Ask questions grounded in your uploaded study materials.",
};

export default async function StudyAssistantPage() {
  const filterOptions =
    await getStudyAssistantFilterOptions();

  return (
    <StudyAssistantWorkspace
      filterOptions={
        filterOptions
      }
    />
  );
}
