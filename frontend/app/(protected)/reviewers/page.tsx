// File: /frontend/app/(protected)/reviewers/page.tsx
// Purpose: Renders the protected AI Reviewer workspace with
// authenticated subject and ready study-material options.

import type {
  Metadata,
} from "next";

import {
  ReviewerWorkspace,
} from "@/features/reviewers/components/ReviewerWorkspace";
import {
  getReviewerFilterOptions,
} from "@/features/reviewers/server/options";

export const metadata:
Metadata = {
  title:
    "Reviewers | STS Capstone",

  description:
    "Generate structured AI reviewers from your uploaded study materials.",
};

export default async function ReviewersPage() {
  const filterOptions =
    await getReviewerFilterOptions();

  return (
    <ReviewerWorkspace
      filterOptions={
        filterOptions
      }
    />
  );
}
