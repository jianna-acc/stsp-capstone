// File: /frontend/app/(protected)/layout.tsx
// Purpose: Protects authenticated application pages and places
// them inside the shared student navigation shell.

import type { ReactNode } from "react";

import { redirect } from "next/navigation";

import { ProtectedAppShell } from "@/features/navigation/components/ProtectedAppShell";
import { createClient } from "@/lib/supabase/server";

interface ProtectedLayoutProps {
  children: ReactNode;
}

/*
 * Protected pages depend on the current request cookies and
 * must always perform a fresh authentication check.
 */
export const dynamic = "force-dynamic";

export default async function ProtectedLayout({
  children,
}: Readonly<ProtectedLayoutProps>) {
  const supabase = await createClient();

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    redirect("/login");
  }

  return (
    <ProtectedAppShell>
      {children}
    </ProtectedAppShell>
  );
}