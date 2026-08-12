// File: /frontend/app/(protected)/quizzes/page.tsx
// Purpose: Renders the protected AI Quiz workspace with
// authenticated subject and ready study-material options.

import type {
  Metadata,
} from "next";

import {
  QuizWorkspace,
} from "@/features/quizzes/components/QuizWorkspace";
import {
  getQuizFilterOptions,
} from "@/features/quizzes/server/options";

export const metadata:
Metadata = {
  title:
    "Quizzes | Intelleap",

  description:
    "Generate AI practice quizzes from your uploaded study materials.",
};

export default async function QuizzesPage() {
  const filterOptions =
    await getQuizFilterOptions();

  return (
    <QuizWorkspace
      filterOptions={
        filterOptions
      }
    />
  );
}