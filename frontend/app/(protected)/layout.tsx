// File: /frontend/app/(protected)/layout.tsx
// Purpose: Performs a server-side authentication check before
// rendering protected application pages.

import type { ReactNode } from "react";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

interface ProtectedLayoutProps {
  children: ReactNode;
}

export default async function ProtectedLayout({
  children,
}: Readonly<ProtectedLayoutProps>) {
  const supabase = await createClient();

  const { data, error } =
    await supabase.auth.getClaims();

  if (
    error ||
    !data?.claims?.sub
  ) {
    redirect(
      "/login?next=%2Fdashboard",
    );
  }

  return children;
}