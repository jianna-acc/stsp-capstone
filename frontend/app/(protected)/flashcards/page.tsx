// File: /frontend/app/(protected)/flashcards/page.tsx
// Purpose: Provides the protected Flashcards page and loads
// authenticated subject and ready-file generation options.

import type {
  Metadata,
} from "next";

import {
  FlashcardWorkspace,
} from "@/features/flashcards/components/FlashcardWorkspace";
import {
  getFlashcardFilterOptions,
} from "@/features/flashcards/server/options";

export const metadata:
  Metadata = {
    title:
      "Flashcards | Intelleap",

    description:
      "Generate and study AI-powered Flashcards from your uploaded study materials.",
  };

export default async function FlashcardsPage() {
  const filterOptions =
    await getFlashcardFilterOptions();

  return (
    <FlashcardWorkspace
      filterOptions={
        filterOptions
      }
    />
  );
}