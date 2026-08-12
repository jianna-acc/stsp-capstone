// File: /frontend/app/(protected)/dashboard/page.tsx
// Purpose: Guards the authenticated student Dashboard,
// loads stable server-side profile data, and renders the
// client-side Dashboard command center.

import type {
  Metadata,
} from "next";

import {
  DashboardWorkspace,
} from "@/features/dashboard/components/DashboardWorkspace";

import {
  requireCompletedLearningProfile,
} from "@/features/learning-profile/server/guards";

import {
  getSubjects,
} from "@/features/subjects/queries";


export const metadata:
  Metadata = {
    title:
      "Dashboard | STS Capstone Project",

    description:
      "Authenticated student dashboard.",
  };


export default async function DashboardPage() {
  const [
    snapshot,
    academicSubjects,
  ] = await Promise.all([
    requireCompletedLearningProfile(),
    getSubjects(),
  ]);

  const displayName =
    snapshot.profile.full_name
      ?.trim() ||
    "Student";

  return (
    <DashboardWorkspace
      displayName={
        displayName
      }
      subjects={
        academicSubjects
      }
    />
  );
}