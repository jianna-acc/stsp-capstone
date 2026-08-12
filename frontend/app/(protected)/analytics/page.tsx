// File: /frontend/app/(protected)/analytics/page.tsx
// Purpose: Renders the protected student Analytics dashboard.

import type {
  Metadata,
} from "next";

import {
  AnalyticsDashboard,
} from "@/features/analytics/components/AnalyticsDashboard";


export const metadata:
  Metadata = {
    title:
      "Analytics | STS Capstone",

    description:
      "Track Quiz performance, Flashcard recall, and study topic strengths.",
  };


export default function AnalyticsPage() {
  return (
    <AnalyticsDashboard />
  );
}