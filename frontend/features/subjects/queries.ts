// File: /frontend/features/subjects/queries.ts
// Purpose: Loads authenticated student-owned subjects from
// Supabase for the protected subjects page.

import "server-only";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

import type { SubjectSummary } from "./types";

export async function getSubjects(): Promise<
  SubjectSummary[]
> {
  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    redirect("/login");
  }

  const { data, error } = await supabase
    .from("subjects")
    .select(
      "id, name, color, created_at, updated_at",
    )
    .eq("user_id", user.id)
    .order("name", {
      ascending: true,
    });

  if (error) {
    console.error(
      "Subject query failed:",
      error.code,
    );

    throw new Error(
      "The subjects could not be loaded.",
    );
  }

  return data ?? [];
}